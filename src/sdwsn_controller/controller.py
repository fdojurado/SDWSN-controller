import threading
from time import sleep
from sdwsn_common import common
from threading import Thread
from abc import ABC, abstractmethod
from sdwsn_serial.serial import SerialBus
from sdwsn_packet.packet_dissector import PacketDissector
from typing import Dict
from sdwsn_docker.docker import CoojaDocker
from sdwsn_result_analysis.run_analysis import run_analysis
from sdwsn_database.database import NODES_INFO
from sdwsn_tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_routes.router import SimpleRouter
from sdwsn_packet.packet import Cell_Packet_Payload, RA_Packet_Payload
from sdwsn_common import common
from sdwsn_database.db_manager import SLOT_DURATION

import numpy as np
import networkx as nx


class BaseController(ABC):
    def __init__(
        self,
        cooja_host: str = '127.0.0.1',
        cooja_port: int = 60001,
        db_name: str = 'mySDN',
        db_host: str = '127.0.0.1',
        db_port: int = 27017,
        simulation_name: str = 'mySimulation',
        processing_window: int = 200,
        max_channel_offsets: int = 3,
        max_slotframe_size: int = 500,
        log_dir: str = "./monitor/"
    ):
        # Save instance of a serial interface
        self.ser = SerialBus(cooja_host, cooja_port)
        # Save instance of packet dissector
        self.packet_dissector = PacketDissector(db_name, db_host, db_port)
        # Create instance of the scheduler, we now only support contention free
        self.scheduler = ContentionFreeScheduler(
            sf_size=max_slotframe_size, channel_offsets=max_channel_offsets)
        # Create an instance of a routes
        self.router = SimpleRouter()
        # Variable to check whether the controller is running or not
        self.is_running = False
        self.simulation_name = simulation_name
        self.num_episodes = 0
        self.processing_window = processing_window
        self._read_ser_thread = None
        self.log_dir = log_dir

    """ Controller primitives """

    def controller_start(self):
        # Initialize database
        self.packet_dissector.initialise_db()
        # Start the serial interface
        self.__controller_serial_start()
        # Restart variables at packet dissector
        self.packet_dissector.cycle_sequence = 0
        self.packet_dissector.sequence = 0
        # Set running flag
        self.is_running = True

    def controller_stop(self):
        # Clear the running flag
        self.is_running = False
        # Stop the serial interface
        self.__controller_serial_stop()
        # Reset the packet dissector sequence
        self.packet_dissector.cycle_sequence = 0
        self.packet_dissector.sequence = 0
        # Run the data analysis script if there is data in the DB
        self.run_data_analysis()

    def run_data_analysis(self):
        self.num_episodes += 1
        # This function plots and save the charts in pdf format
        if self.packet_dissector.DATABASE is not None:
            run_analysis(self.packet_dissector,
                         self.simulation_name+str(self.num_episodes), self.log_dir)

    def __controller_serial_stop(self):
        if self._read_ser_thread is not None:
            print(f"start to shutdown thread, running flag = {self.is_running}")
            self._read_ser_thread.join()
        self.ser.shutdown()

    """ TSCH scheduler/schedule functions """

    def get_max_ts_size(self):
        return self.scheduler.slotframe_size

    def get_last_active_ts(self):
        return self.scheduler.schedule_last_active_ts()

    def get_list_of_active_slots(self):
        return self.scheduler.schedule_get_list_ts_in_use()

    def compute_schedule(self, path, current_sf_size):
        # We clean previous schedule first
        self.scheduler.schedule_clear_schedule()
        self.scheduler.run(path, current_sf_size)

    def send_schedules(self, sf_size):
        num_pkts = 0
        payload = []
        rows, cols = (self.scheduler.num_channel_offsets,
                      self.scheduler.slotframe_size)
        for i in range(rows):
            for j in range(cols):
                if (self.scheduler.schedule[i][j]):
                    for elem in self.scheduler.schedule[i][j]:
                        channel = elem.channeloffset
                        timeslot = elem.timeoffset
                        addr = elem.source
                        type = elem.type
                        dst = elem.destination
                        data = {"channel": channel, "timeslot": timeslot, "addr": addr, "type": type,
                                "dest": dst}
                        print("schedule element")
                        print(data)
                        # if num_links < 11:
                        cell_pkt = Cell_Packet_Payload(payload=payload, type=int(type),
                                                       channel=int(channel), timeslot=int(timeslot), scr=addr,
                                                       dst=dst)
                        cell_packed = cell_pkt.pack()
                        payload = cell_packed
                        if len(payload) > 90:
                            print(f'Sending schedule packet {num_pkts}')
                            # We send the current payload
                            num_pkts += 1
                            current_sf_size = 0
                            if num_pkts == 1:
                                current_sf_size = sf_size
                            packedData, serial_pkt = common.tsch_build_pkt(
                                payload, current_sf_size, self.increase_cycle_sequence())
                            payload = []
                            # Send NC packet
                            self.controller_reliable_send(
                                packedData, serial_pkt.reserved0+1)
        # Send the remain payload if there is one
        if payload:
            num_pkts += 1
            print(f'Sending schedule packet {num_pkts}')
            current_sf_size = 0
            if num_pkts == 1:
                current_sf_size = sf_size
            packedData, serial_pkt = common.tsch_build_pkt(
                payload, current_sf_size, self.increase_cycle_sequence())
            # Send NC packet
            self.controller_reliable_send(
                packedData, serial_pkt.reserved0+1)

    """ Serial/socket interface functions """

    def __controller_serial_start(self):
        # Connect serial
        if self.ser.connect() != 0:
            print('unsuccessful serial connection')
            return 0
        print("Socket up and running")
        # Read serial
        self._read_ser_thread = threading.Thread(target=self.__read_ser)
        self._read_ser_thread.start()
        return 1

    def __read_ser(self):
        while(1):
            try:
                msg = self.ser.recv(0.1)
                if(len(msg) > 0):
                    self.packet_dissector.handle_serial_packet(msg)
            except TypeError:
                pass
            if not self.is_running:
                break
        print("Socket reading thread exited.")

    """ Cycle management """

    def controller_wait_cycle_finishes(self):
        # If we have not received any data after looping 10 times
        # We return
        print("Waiting for the current cycle to finish")
        count = 0
        result = -1
        while(1):
            count += 1
            if self.packet_dissector.sequence > self.processing_window:
                result = 1
                break
            if count > 10:
                result = 0
                break
            sleep(1)
        print(f"cycle finished, result: {result}")
        return result

    def save_observations(self, *args):
        self.packet_dissector.save_observations(*args)

    def get_last_observations(self):
        return self.packet_dissector.get_last_observations()

    def delete_info_collection(self):
        self.packet_dissector.delete_collection(NODES_INFO)

    """ Reward calculation functions """

    def calculate_reward(self, alpha, beta, delta):
        # Get the sensor nodes to loop in ascending order
        nodes = self.packet_dissector.get_sensor_nodes_in_order()
        # Get the normalized average power consumption for this cycle
        power_wam, power_mean, power_normalized = self.get_network_power_consumption(
            nodes)
        power = [power_wam, power_mean, power_normalized]
        # Get the normalized average delay for this cycle
        delay_wam, delay_mean, delay_normalized = self.get_network_delay(nodes)
        delay = [delay_wam, delay_mean, delay_normalized]
        # Get the normalized average pdr for this cycle
        pdr_wam, pdf_mean = self.get_network_pdr(nodes)
        pdr = [pdr_wam, pdf_mean]
        # Calculate the reward
        reward = -1*(alpha*power_normalized+beta *
                     delay_normalized-delta*pdr_wam)
        return reward, power, delay, pdr

    def get_network_power_consumption(self, nodes):
        # Min power
        p_min = 0
        # Max power
        p_max = 3000
        # Variable to keep track of the number of energy consumption samples
        power_samples = []
        # We first loop through all sensor nodes
        for node in nodes:
            # Get all samples from the start of the network configuration
            self.packet_dissector.get_last_power_consumption(
                node, power_samples, self.get_cycle_sequence())
        print(f"power samples for sequence {self.packet_dissector.cycle_sequence}")
        print(power_samples)
        # We now need to compute the weighted arithmetic mean
        power_wam, power_mean = self.power_weighted_arithmetic_mean(
            power_samples)
        # We now need to normalize the power WAM
        normalized_power = (power_wam - p_min)/(p_max-p_min)
        print(f'normalized power {normalized_power}')
        return power_wam, power_mean, normalized_power

    def power_weighted_arithmetic_mean(self, power_samples):
        weights = []
        all_power_samples = []
        for elem in power_samples:
            node = elem[0]
            power = elem[1]
            all_power_samples.append(power)
            # print(f'Finding the WAM of {node} with power {power}')
            weight = self.power_compute_wam_weight(node)
            weights.append(weight)
        print(f'power all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        # print(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        print(f'normalized weights {normalized_weights}')
        all_power = np.array(all_power_samples)
        all_power_transpose = np.transpose(all_power)
        # print(f'transpose all power {all_power_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_power_transpose)
        # Overall network mean
        normal_mean = all_power.sum()/len(all_power_samples)
        print(f'power network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def power_compute_wam_weight(self, node):
        # Let's first get the rank of the sensor node
        node_rank = self.packet_dissector.get_rank(node)
        # Get the value of the greatest rank of the network
        db = self.packet_dissector.find_one(
            NODES_INFO, {}, sort=[("rank", -1)])
        last_rank = db['rank']
        # Let's get the number of neighbors
        num_nbr = 0
        for _ in self.packet_dissector.get_last_nbr(node):
            num_nbr += 1
        # Get the total number of sensor nodes
        N = self.packet_dissector.get_number_of_sensors()
        # Calculate the weight
        weight = 0.9 * (node_rank/last_rank) + 0.1 * (num_nbr/N)
        # print(f'computing WAM of node {node} rank {node_rank} num nbr {num_nbr} N {N} weight {weight}')
        return weight

    def get_network_delay(self, nodes):
        # Min power
        delay_min = SLOT_DURATION
        # Max power
        delay_max = 2500
        # Variable to keep track of the number of delay samples
        delay_samples = []
        # We first loop through all sensor nodes
        for node in nodes:
            # Get all samples from the start of the network configuration
            self.packet_dissector.get_avg_delay(
                node, delay_samples, self.get_cycle_sequence())
        print(f"delay samples for sequence {self.packet_dissector.cycle_sequence}")
        print(delay_samples)
        # We now need to compute the weighted arithmetic mean
        delay_wam, delay_mean = self.delay_weighted_arithmetic_mean(
            delay_samples)
        # We now need to normalize the power WAM
        normalized_delay = (delay_wam - delay_min)/(delay_max-delay_min)
        print(f'normalized delay {normalized_delay}')
        return delay_wam, delay_mean, normalized_delay

    def delay_weighted_arithmetic_mean(self, delay_samples):
        weights = []
        all_delay_samples = []
        for elem in delay_samples:
            node = elem[0]
            delay = elem[1]
            all_delay_samples.append(delay)
            weight = self.delay_compute_wam_weight(node)
            weights.append(weight)
        print(f'delay all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        print(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        print(f'normalized weights {normalized_weights}')
        all_delay = np.array(all_delay_samples)
        all_delay_transpose = np.transpose(all_delay)
        # print(f'transpose all delay {all_delay_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_delay_transpose)
        # Overall network mean
        normal_mean = all_delay.sum()/len(all_delay_samples)
        print(f'delay network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def delay_compute_wam_weight(self, node):
        # We assume that the wight depends on the rank
        # Let's get the rank of the sensor node
        node_rank = self.packet_dissector.get_rank(node)
        # Get the value of the greatest rank of the network
        db = self.packet_dissector.find_one(
            NODES_INFO, {}, sort=[("rank", -1)])
        last_rank = db['rank']
        # Calculate the weight
        weight = 1 - node_rank/(last_rank+1)
        # print(f'computing WAM of node {node} rank {node_rank} weight {weight}')
        return weight

    def get_network_pdr(self, nodes):
        # Variable to keep track of the number of pdr samples
        pdr_samples = []
        # We first loop through all sensor nodes
        for node in nodes:
            # Get all samples from the start of the network configuration
            self.packet_dissector.get_avg_pdr(
                node, pdr_samples, self.get_cycle_sequence())
        print(f"pdr samples for sequence {self.packet_dissector.cycle_sequence}")
        print(pdr_samples)
        # We now need to compute the weighted arithmetic mean
        pdr_wam, pdr_mean = self.pdr_weighted_arithmetic_mean(
            pdr_samples)
        print(f'normalized pdr {pdr_wam}')
        return pdr_wam, pdr_mean

    def pdr_weighted_arithmetic_mean(self, pdr_samples):
        weights = []
        all_pdr_samples = []
        for elem in pdr_samples:
            node = elem[0]
            pdr = elem[1]
            all_pdr_samples.append(pdr)
            weight = self.pdr_compute_wam_weight(node)
            weights.append(weight)
        print(f'pdr all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        # print(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        print(f'normalized weights {normalized_weights}')
        all_pdr = np.array(all_pdr_samples)
        all_pdr_transpose = np.transpose(all_pdr)
        # print(f'transpose all pdr {all_pdr_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_pdr_transpose)
        # Overall network mean
        normal_mean = all_pdr.sum()/len(all_pdr_samples)
        print(f'pdr network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def pdr_compute_wam_weight(self, node):
        # We assume that the wight depends on the rank of
        # the node and the number of NBRs
        # Let's first get the rank of the sensor node
        node_rank = self.packet_dissector.get_rank(node)
        # Get the value of the greatest rank of the network
        db = self.packet_dissector.find_one(
            NODES_INFO, {}, sort=[("rank", -1)])
        last_rank = db['rank']
        # Let's get the number of neighbors
        num_nbr = 0
        for _ in self.packet_dissector.get_last_nbr(node):
            num_nbr += 1
        # Get the total number of sensor nodes
        N = self.packet_dissector.get_number_of_sensors()
        # Calculate the weight
        weight = 0.9 * (node_rank/last_rank) + 0.1 * (num_nbr/N)
        # print(f'computing pdr WAM of node {node} rank {node_rank} num nbr {num_nbr} N {N} weight {weight}')
        return weight

    """ Network information methods """

    def controller_get_network_links(self):
        # Get last index of sensor
        N = self.packet_dissector.get_last_index_wsn()+1
        # Neighbor matrix
        nbr_rssi_matrix = np.zeros(shape=(N, N))
        # We first loop through all sensor nodes
        nodes = self.packet_dissector.find(NODES_INFO, {})
        for node in nodes:
            # Get last neighbors
            nbr = self.packet_dissector.get_last_nbr(node["node_id"])
            if nbr is not None:
                for nbr_node in nbr:
                    source, _ = node["node_id"].split('.')
                    dst, _ = nbr_node["dst"].split('.')
                    nbr_rssi_matrix[int(source)][int(
                        dst)] = int(nbr_node["rssi"])
        matrix = nbr_rssi_matrix * -1
        G = nx.from_numpy_matrix(matrix, create_using=nx.DiGraph)
        G.remove_nodes_from(list(nx.isolates(G)))
        return G

    """ Routing functions """

    def send_routes(self):
        print('Sending routes')
        num_pkts = 0
        payload = []
        for _, row in self.router.routes.iterrows():
            scr = row['scr']
            dst = row['dst']
            via = row['via']
            data = {"scr": scr, "dst": dst, "via": via}
            print("route")
            print(data)
            route_pkt = RA_Packet_Payload(
                dst=dst, scr=scr, via=via, payload=payload)
            routed_packed = route_pkt.pack()
            payload = routed_packed
            if len(payload) > 90:
                print(f'Sending routing packet {num_pkts}')
                # We send the current payload
                num_pkts += 1
                packedData, serial_pkt = common.routing_build_pkt(
                    payload, self.increase_cycle_sequence())
                payload = []
                # Send NC packet
                self.controller_reliable_send(
                    packedData, serial_pkt.reserved0+1)
        # Send the remain payload if there is one
        if payload:
            num_pkts += 1
            print(f'Sending routing packet {num_pkts}')
            packedData, serial_pkt = common.routing_build_pkt(
                payload, self.increase_cycle_sequence())
            # Send NC packet
            self.controller_reliable_send(
                packedData, serial_pkt.reserved0+1)

    def compute_dijkstra(self, G):
        # Clear all previous routes
        self.router.delete_all_routes()
        # TODO: Routes should be part of the controller
        # We want to compute the SP from all nodes to the controller
        path = {}
        for node in list(G.nodes):
            if node != 1 and node != 0:
                # print("sp from node "+str(node))
                try:
                    node_path = nx.dijkstra_path(G, node, 1, weight='weight')
                    # print("dijkstra path")
                    # print(node_path)
                    path[node] = node_path
                    # TODO: find a way to avoid forcing the last addr of
                    # sensor nodes to 0.
                    self.router.add_link(
                        str(node)+".0", "1.1", str(node_path[1])+".0")
                except nx.NetworkXNoPath:
                    print("path not found")
        # self.router.print_routes()
        print("total path")
        print(path)
        return path

    """ Sequence functions """

    def increase_cycle_sequence(self):
        self.packet_dissector.cycle_sequence += 1
        return self.packet_dissector.cycle_sequence

    def increase_pkt_sequence(self):
        self.packet_dissector.sequence += 1

    def reset_pkt_sequence(self):
        self.packet_dissector.sequence = 0

    def get_cycle_sequence(self):
        return self.packet_dissector.cycle_sequence

    def controller_send_data(self, data):
        if self.is_running:
            print("sending serial packet")
            # Send data to the serial send interface
            self.ser.send(data)
        else:
            print("Couldn't send data, controller is Not running")

    """ Send a reliable packet to the SDWSN """

    def controller_reliable_send(self, data, ack):
        # Reliable socket data transmission
        # set retransmission
        rtx = 0
        # Send NC packet through serial interface
        self.controller_send_data(data)
        # Result variable to see if the sending went well
        result = 0
        while True:
            if self.packet_dissector.ack_pkt is not None:
                if (self.packet_dissector.ack_pkt.reserved0 == ack):
                    print("correct ACK received")
                    result = 1
                    break
                print("ACK not received")
                # We stop sending the current NC packet if
                # we reached the max RTx or we received ACK
                if(rtx >= 7):
                    print("ACK never received")
                    break
                # We resend the packet if retransmission < 7
                rtx = rtx + 1
                self.controller_send_data(data)
            sleep(1.2)
        return result


class ContainerController(BaseController):
    def __init__(
            self,
            image: str = 'contiker/contiki-ng',
            command: str = '/bin/sh -c "cd examples/benchmarks/rl-sdwsn && ./run-cooja.py"',
            mount: Dict = {
                'target': '/home/user/contiki-ng',
                'source': '/Users/fernando/contiki-ng',
                'type': 'bind'
            },
            sysctls: Dict = {
                'net.ipv6.conf.all.disable_ipv6': 0
            },
            container_ports: Dict = {
                'container': 60001,
                'host': 60001
            },
            privileged: bool = True,
            detach: bool = True,
            socket_file: str = '/Users/fernando/contiki-ng/examples/benchmarks/rl-sdwsn/COOJA.log',
            cooja_host: str = '127.0.0.1',
            cooja_port: int = 60001,
            db_name: str = 'mySDN',
            db_host: str = '127.0.0.1',
            db_port: int = 27017,
            simulation_name: str = 'mySimulation',
            processing_window: int = 200,
            max_channel_offsets: int = 3,
            max_slotframe_size: int = 500,
            log_dir: str = './monitor/'
    ):
        super().__init__(
            cooja_host,
            cooja_port,
            db_name,
            db_host,
            db_port,
            simulation_name,
            processing_window,
            max_channel_offsets,
            max_slotframe_size,
            log_dir)

        self.container = CoojaDocker(image=image, command=command, mount=mount,
                                     sysctls=sysctls, ports=container_ports, privileged=privileged, detach=detach,
                                     socket_file=socket_file)

    def container_controller_start(self):
        self.container.start_container()
        self.controller_start()

    def container_controller_shutdown(self):
        self.container.shutdown()
        self.controller_stop()

    def container_reset(self):
        print('Resetting container, controller, etc.')
        self.container_controller_shutdown()
        self.container_controller_start()
