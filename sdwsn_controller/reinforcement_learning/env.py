""" This is the implementation of the Software-Defined Wireless Sensor Network
environment """
from typing import Type
import gym
from gym import spaces
import numpy as np
from time import sleep
from datetime import datetime
import random

from sdwsn_controller.common.common import common
from sdwsn_controller.controller.controller import ContainerController
from sdwsn_controller.result_analysis.run_analysis import run_analysis
from random import randrange

# These are the size of other schedules in orchestra
eb_size = 397
common_size = 31
control_plane_size = 27


class Env(gym.Env):
    """Custom SDWSN Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(
            self,
            target: str,
            source: str,
            simulation_command: str,
            host: str,
            port: int,
            socket_file: str,
            db_name: str,
            simulation_name: str,
            tsch_scheduler: str,
            fig_dir: str = './figures/'
    ):
        super(Env, self).__init__()
        self.container_controller = ContainerController(
            target=target,
            source=source,
            command=simulation_command,
            cooja_host=host,
            cooja_port=port,
            socket_file=socket_file,
            db_name=db_name,
            simulation_name=simulation_name,
            tsch_scheduler=tsch_scheduler
        )
        self.fig_dir = fig_dir
        self.simulation_name = simulation_name
        # We define the number of actions
        n_actions = 2  # increase and decrease slotframe size
        self.action_space = spaces.Discrete(n_actions)
        # We define the observation space
        # They will be the user requirements, power, delay, pdr, last ts active in schedule
        self.n_observations = 7
        self.observation_space = spaces.Box(low=0, high=1,
                                            shape=(self.n_observations, ), dtype=np.float32)

    """ Step action """

    def step(self, action):
        sample_time = datetime.now().timestamp() * 1000.0
        # We now get the last observations
        alpha, beta, delta, last_ts_in_schedule, current_sf_len, _, _ = self.container_controller.get_last_observations()
        print(f"Performing action {action} (current sf: {current_sf_len})")
        if action == 0:
            print("increasing slotframe size")
            sf_len = common.next_coprime(current_sf_len)
        if action == 1:
            print("decreasing slotframe size")
            sf_len = common.previous_coprime(current_sf_len)
        if action == 2:
            sf_len = current_sf_len
        user_requirements = np.array([alpha, beta, delta])
        # the last slot in the current schedule
        # Send the entire TSCH schedule
        self.container_controller.send_schedules(sf_len)
        # Delete the current nodes_info collection from the database
        self.container_controller.delete_info_collection()
        # Reset sequence
        self.container_controller.reset_pkt_sequence()
        # We now wait until we reach the processing_window
        while (not self.container_controller.controller_wait_cycle_finishes()):
            print("resending schedules")
            self.container_controller.send_schedules(sf_len)
            # Delete the current nodes_info collection from the database
            self.container_controller.delete_info_collection()
            # Reset sequence
            self.container_controller.reset_pkt_sequence()
        print("process reward")
        sleep(1)
        # Calculate the reward
        reward, cycle_power, cycle_delay, cycle_pdr = self.container_controller.calculate_reward(
            alpha, beta, delta)
        # Append to the observations
        sample_time = datetime.now().timestamp() * 1000.0
        observation = np.append(user_requirements, cycle_power[2])
        observation = np.append(observation, cycle_delay[2])
        observation = np.append(observation, cycle_pdr[1])
        observation = np.append(observation, last_ts_in_schedule/15)
        self.container_controller.save_observations(
            timestamp=sample_time,
            alpha=alpha,
            beta=beta,
            delta=delta,
            power_mean=cycle_power[2],
            delay_mean=cycle_delay[2],
            pdr_mean=cycle_pdr[1],
            current_sf_len=sf_len,
            last_ts_in_schedule=last_ts_in_schedule,
            reward=reward
        )
        done = False
        info = {}
        # 50 is the maximum slotframe size
        # TODO: Set the maximum slotframe size at the creation
        # of the environment
        if (sf_len < last_ts_in_schedule or sf_len > 50):
            done = True
            reward = -4
        return observation, reward, done, info

    """ Reset the environment, reset the routing and the TSCH schedules """

    def reset(self):
        # Reset the container controller
        self.container_controller.container_reset()
        # We now wait until we reach the processing_window
        self.container_controller.controller_wait_cycle_finishes()
        # We get the network links, useful when calculating the routing
        G = self.container_controller.controller_get_network_links()
        # Run the dijkstra algorithm with the current links
        path = self.container_controller.compute_dijkstra(G)
        # Lets set the type of scheduler
        types_scheduler = ['Contention Free', 'Unique Schedule']
        # type_scheduler = random.choice(types_scheduler)
        # self.container_controller.scheduler = type_scheduler
        self.container_controller.scheduler = 'Contention Free'
        # Set the slotframe size
        slotframe_size = 15
        # We now set the TSCH schedules for the current routing
        self.container_controller.compute_schedule(path, slotframe_size)
        # We now set and save the user requirements
        balanced = [0.4, 0.3, 0.3]
        energy = [0.8, 0.1, 0.1]
        delay = [0.1, 0.8, 0.1]
        reliability = [0.1, 0.1, 0.8]
        user_req = [balanced, energy, delay, reliability]
        select_user_req = random.choice(user_req)
        # Send the entire routes
        self.container_controller.send_routes()
        # Send the entire TSCH schedule
        self.container_controller.send_schedules(slotframe_size)
        # Delete the current nodes_info collection from the database
        self.container_controller.delete_info_collection()
        self.container_controller.reset_pkt_sequence()
        # Wait for the network to settle
        self.container_controller.controller_wait_cycle_finishes()
        # We now save all the observations
        # Get last active ts
        last_ts_in_schedule = self.container_controller.get_last_active_ts()
        # Set the slotframe size
        slotframe_size = randrange(last_ts_in_schedule+1, 45)
        # They are of the form "time, user requirements, routing matrix, schedules matrix, sf len"
        sample_time = datetime.now().timestamp() * 1000.0
        # We now save the user requirements
        user_requirements = np.array(select_user_req)
        # We now save the observations with reward None
        _, cycle_power, cycle_delay, cycle_pdr = self.container_controller.calculate_reward(
            select_user_req[0], select_user_req[1], select_user_req[2])
       # Append to the observations
        sample_time = datetime.now().timestamp() * 1000.0
        observation = np.append(user_requirements, cycle_power[2])
        observation = np.append(observation, cycle_delay[2])
        observation = np.append(observation, cycle_pdr[1])
        observation = np.append(observation, last_ts_in_schedule/15)
        self.container_controller.save_observations(
            timestamp=sample_time,
            alpha=select_user_req[0],
            beta=select_user_req[1],
            delta=select_user_req[2],
            power_mean=cycle_power[2],
            delay_mean=cycle_delay[2],
            pdr_mean=cycle_pdr[1],
            current_sf_len=slotframe_size,
            last_ts_in_schedule=last_ts_in_schedule,
            reward=None
        )
        return observation  # reward, done, info can't be included

    def render(self, mode='console'):
        print(f"mode: {mode}")
        # if mode != 'console':
        #     raise NotImplementedError()
        # agent is represented as a cross, rest as a dot
        print('rendering')
        number = random.randint(0, 100)
        run_analysis(self.container_controller.packet_dissector,
                     self.simulation_name+str(number), self.fig_dir, True)
