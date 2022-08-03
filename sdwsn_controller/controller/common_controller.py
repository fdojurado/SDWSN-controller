from sdwsn_controller.controller.controller import BaseController
from sdwsn_controller.common import common
from sdwsn_controller.packet.packet import RA_Packet_Payload
from sdwsn_controller.routes.router import SimpleRouter
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.database.database import NODES_INFO
from sdwsn_controller.serial.serial import SerialBus
from sdwsn_controller.packet.packet_dissector import PacketDissector
from sdwsn_controller.reinforcement_learning.reward_processing import EmulatedRewardProcessing
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.packet.packet import Cell_Packet_Payload




import numpy as np
import networkx as nx
import threading
from time import sleep


class CommonController(BaseController):

    def __init__(
        self,
        host: str = '127.0.0.1',
        port: int = 60001,
        db_name: str = 'mySDN',
        db_host: str = '127.0.0.1',
        db_port: int = 27017,
        router: object = SimpleRouter(),
        tsch_scheduler: object = ContentionFreeScheduler(500, 3),
        processing_window: int = 200
    ):
        # Create a socket communication
        self.__socket = SerialBus(host, port)
        self.__read_socket_thread = None

        # Create database
        self.__db = DatabaseManager(
            name=db_name,
            host=db_host,
            port=db_port
        )

        # Create packet dissector
        self.__packet_dissector = PacketDissector(database=self.__db)

        # Create reward module
        self.__reward_processing = EmulatedRewardProcessing(database=self.__db)

        # Create TSCH scheduler module
        self.__tsch_scheduler = tsch_scheduler

        # Create an instance of Router
        self.__router = router

        # Initialize some variables
        self.__is_running = False
        self.__processing_window = processing_window

        super().__init__()

    """ Controller related functions """

    def start(self):
        # Initialize database
        self.init_db()
        # Start the socket interface
        sock = self.comm_interface_start()
        if sock == 0:
            self.stop()
            return
        # Restart variables at packet dissector
        self.cycle_sequence = 0
        self.sequence = 0
        # Set running flag
        self.__is_running = True
        # self.controller_start()

    def stop(self):
        # Clear the running flag
        self.__is_running = False
        # Stop the serial interface
        self.comm_interface_stop()
        # Reset the packet dissector sequence
        self.cycle_sequence = 0
        self.sequence = 0
        # Run the data analysis script if there is data in the DB
        # self.run_data_analysis()

    def wait(self):
        """
         We wait for the current cycle to finish
         """
        # If we have not received any data after looping 10 times
        # We return
        print("Waiting for the current cycle to finish")
        count = 0
        result = -1
        while(1):
            count += 1
            if self.sequence > self.__processing_window:
                result = 1
                break
            if count > 10:
                result = 0
                break
            sleep(1)
        print(f"cycle finished, result: {result}")
        return result

    def send(self, data):
        if self.__is_running:
            print("sending serial packet")
            # Send data to the serial send interface
            self.__socket.send(data)
        else:
            print("Couldn't send data, controller is Not running")

    def reliable_send(self, data, ack):
        # Reliable socket data transmission
        # set retransmission
        rtx = 0
        # Send NC packet through serial interface
        self.send(data)
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
                self.send(data)
            sleep(1.2)
        return result

    """ Packet dissector related functionalities """

    @property
    def packet_dissector(self):
        return self.__packet_dissector

    @property
    def sequence(self):
        return self.__packet_dissector.sequence

    @sequence.setter
    def sequence(self, num):
        self.__packet_dissector.sequence = num

    @property
    def cycle_sequence(self):
        return self.__packet_dissector.cycle_sequence

    @cycle_sequence.setter
    def cycle_sequence(self, num):
        self.__packet_dissector.cycle_sequence = num

    def increase_sequence(self):
        self.sequence += 1
        return self.sequence

    def increase_cycle_sequence(self):
        self.cycle_sequence += 1
        return self.cycle_sequence

    def reset_pkt_sequence(self):
        self.sequence = 0

    def get_cycle_sequence(self):
        return self.cycle_sequence

    """ 
    Serial interface methods:
        * Start
        * Stop
        * read
    """

    def comm_interface_start(self):
        # Connect serial
        if self.__socket.connect() != 0:
            print(f'unsuccessful serial connection (host:{self.__socket.host}, port: {self.__socket.port})')
            return 0
        print("Socket up and running")
        # Read serial
        self.__read_socket_thread = threading.Thread(
            target=self.comm_interface_read)
        self.__read_socket_thread.start()
        return 1

    def comm_interface_stop(self):
        if self.__read_socket_thread is not None:
            print(f"start to shutdown thread, running flag = {self.__is_running}")
            self.__read_socket_thread.join()
        self.__socket.shutdown()

    def comm_interface_read(self):
        while(1):
            try:
                msg = self.__socket.recv(0.1)
                if(len(msg) > 0):
                    self.packet_dissector.handle_serial_packet(msg)
            except TypeError:
                pass
            if not self.__is_running:
                break
        print("Socket reading thread exited.")

    """ Database related functionalities """

    def init_db(self):
        self.__db.initialize()

    @property
    def db(self):
        return self.__db

    def get_network_links(self):
        # Get last index of sensor
        N = self.db.get_last_index_wsn()+1
        # Neighbor matrix
        nbr_rssi_matrix = np.zeros(shape=(N, N))
        # We first loop through all sensor nodes
        nodes = self.db.find(NODES_INFO, {})
        for node in nodes:
            # Get last neighbors
            nbr = self.db.get_last_nbr(node["node_id"])
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

    """ TSCH related functionalities """

    def last_active_tsch_slot(self):
        return self.tsch_scheduler.schedule_last_active_ts()

    def compute_tsch_schedule(self, path, current_sf_size):
        # We clean previous schedule first
        self.tsch_scheduler.schedule_clear_schedule()
        self.tsch_scheduler.run(path, current_sf_size)

    @property
    def tsch_scheduler(self):
        return self.__tsch_scheduler

    def send_tsch_schedules(self, sf_size):
        num_pkts = 0
        payload = []
        rows, cols = (self.tsch_scheduler.num_channel_offsets,
                      self.tsch_scheduler.slotframe_size)
        for i in range(rows):
            for j in range(cols):
                if (self.tsch_scheduler.schedule[i][j]):
                    for elem in self.tsch_scheduler.schedule[i][j]:
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
                            self.reliable_send(
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
            self.reliable_send(
                packedData, serial_pkt.reserved0+1)

    """ Routing related functions """
    @property
    def router(self):
        return self.__router

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
                self.reliable_send(
                    packedData, serial_pkt.reserved0+1)
        # Send the remain payload if there is one
        if payload:
            num_pkts += 1
            print(f'Sending routing packet {num_pkts}')
            packedData, serial_pkt = common.routing_build_pkt(
                payload, self.increase_cycle_sequence())
            # Send NC packet
            self.reliable_send(
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

    """ Reinforcement learning functionalities """

    def calculate_reward(self, alpha, beta, delta):
        return self.__reward_processing.calculate_reward(alpha, beta, delta, self.cycle_sequence)
