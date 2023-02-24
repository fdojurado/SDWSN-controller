#!/usr/bin/python3
#
# Copyright (C) 2022  Fernando Jurado-Lasso <ffjla@dtu.dk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from abc import ABC, abstractmethod

import logging

import numpy as np

from sdwsn_controller.common import common

from sdwsn_controller.database.database import OBSERVATIONS
from sdwsn_controller.database.database import NODES_INFO
from sdwsn_controller.network.network import Network
from sdwsn_controller.packet.packet import Cell_Packet_Payload
from sdwsn_controller.packet.packet import RA_Packet_Payload
from sdwsn_controller.reinforcement_learning.reward_processing \
    import RewardProcessing

from time import sleep


logger = logging.getLogger('main.'+__name__)


class BaseController(ABC):

    def __init__(
        self,
        # Network instance
        network: object = None,
        # RL related
        reward_processing: object = None,
        # Routing
        routing: object = None,
        # TSCH scheduler
        tsch_scheduler: object = None
    ):
        """
        The BaseController class is an abstract class. Some functionalities are
        declared as abstract methods, classes that inherits from the
        BaseController should take care of them. The controller has six main
        modules: network, reward processing, routing, and TSCH scheduler.

        Args:
            network (Network object, optional): Data plane infrastructure.
                Defaults to None.
            reward_processing (RewardProcessing object, optional):Reward
                processing for RL. Defaults to None.
            processing_window (int, optional): Number of packets for a
                new cycle. Defaults to 200.
            routing (Router object, optional): Centralized routing algorithm.
                Defaults to None.
            tsch_scheduler (Scheduler object, optional): Centralized
                TSCH scheduler. Defaults to None.
        """

        # Create network
        self.network = network
        if self.network is not None:
            assert isinstance(self.network, Network)
            logger.info(f"reward processing: {self.network.name}")
            # Requirements
            self.__user_requirements = UserRequirements()

        # Create reward module; only for RL
        self.__reward_processing = reward_processing
        if reward_processing is not None:
            assert isinstance(self.__reward_processing, RewardProcessing)
            logger.info(f"reward processing: {self.reward_processing.name}")
            # Requirements
            self.__user_requirements = UserRequirements()

        # Create TSCH scheduler module
        self.__tsch_scheduler = tsch_scheduler
        if tsch_scheduler is not None:
            logger.info(f'TSCH scheduler: {self.tsch_scheduler.name}')

        # Create an instance of Router
        self.__routing = routing
        if routing is not None:
            logger.info(f'Routing: {self.routing.name}')

        self.controller_running = False

        super().__init__()

    # --------------------------TSCH functions--------------------------

    def send_tsch_schedules(self):
        # FIXME: Function is too complex. We need to split this function.
        """
        It sends the TSCH links to the sink.

        Returns:
            int: 1 is successful; 0 otherwise.
        """
        if self.tsch_scheduler is not None:
            return self.network.tsch_sendall()

    def compute_tsch_schedule(self, path, current_sf_size):
        if self.tsch_scheduler is not None:
            self.tsch_scheduler.run(path, current_sf_size, self.network)

    @property
    def last_tsch_link(self):
        if self.tsch_scheduler is not None:
            return self.network.tsch_last_ts()

    @last_tsch_link.setter
    def last_tsch_link(self, val):
        # We pass because this is not valid in TSCH network
        # Automatically done by the scheduler
        pass

    @property
    def current_slotframe_size(self):
        if self.tsch_scheduler is not None:
            return self.network.tsch_slotframe_size

    @current_slotframe_size.setter
    def current_slotframe_size(self, val):
        if self.tsch_scheduler is not None:
            self.network.tsch_slotframe_size = val

    @property
    def tsch_scheduler(self):
        return self.__tsch_scheduler

    # --------------------------Routing functions-------------------------

    def send_routes(self):
        """
        It sends the routing paths to the sink.

        Returns:
            int: 1 is successful; 0 otherwise.
        """
        if self.routing is not None:
            return self.network.routes_sendall()

    def compute_routes(self, G):
        if self.routing is not None:
            return self.routing.run(G, self.network)

    def get_network_links(self):
        if self.routing is not None:
            return self.network.links()

    @property
    def routing(self):
        return self.__routing

    # --------------------------Controller primitives-----------------------

    def start(self):
        self.network.start()
        self.controller_running = True

    def stop(self):
        self.network.stop()
        # Clear the running flag
        self.controller_running = False

    @abstractmethod
    def reset(self):
        pass

    def wait(self):
        return self.network.wait()

    @abstractmethod
    def timeout(self):
        pass

    def processing_wait(self, time):
        sleep(time)

    def wait_seconds(self, seconds):
        sleep(seconds)

    # --------------------------Reinforcement Learning----------------------

    @property
    def reward_processing(self):
        return self.__reward_processing

    def export_observations(self, simulation_name, folder):
        if self.db is not None:
            self.db.export_collection(OBSERVATIONS, simulation_name, folder)

    def calculate_reward(self, alpha, beta, delta, _):
        if self.reward_processing is not None:
            return self.reward_processing.calculate_reward(alpha, beta, delta)

    @property
    def user_requirements(self):
        return self.__user_requirements.requirements

    @property
    def user_requirements_type(self):
        return self.__user_requirements.type

    @user_requirements.setter
    def user_requirements(self, val):
        self.__user_requirements.requirements = val

    @property
    def alpha(self):
        return self.__user_requirements.alpha

    @alpha.setter
    def alpha(self, val):
        self.__user_requirements.alpha = val

    @property
    def beta(self):
        return self.__user_requirements.beta

    @beta.setter
    def beta(self, val):
        self.__user_requirements.beta = val

    @property
    def delta(self):
        return self.__user_requirements.delta

    @delta.setter
    def delta(self, val):
        self.__user_requirements.delta = val

    # def save_observations(self, **env_kwargs):
    #     if self.db is not None:
    #         self.db.save_observations(**env_kwargs)

    #     self.__update_observations(**env_kwargs)

    # def __update_observations(self, timestamp, alpha, beta, delta, power_wam, power_mean,
    #                           power_normalized, delay_wam, delay_mean, delay_normalized,
    #                           pdr_wam, pdr_mean, current_sf_len, last_ts_in_schedule, reward):
    #     self.__timestamp = timestamp
    #     self.alpha = alpha
    #     self.beta = beta
    #     self.delta = delta
    #     self.__power_wam = power_wam
    #     self.__power_mean = power_mean
    #     self.__power_normalized = power_normalized
    #     self.__delay_wam = delay_wam
    #     self.__delay_mean = delay_mean
    #     self.__delay_normalized = delay_normalized
    #     self.__pdr_wam = pdr_wam
    #     self.__pdr_mean = pdr_mean
    #     self.current_slotframe_size = current_sf_len
    #     self.last_tsch_link = last_ts_in_schedule
    #     self.__reward = reward

    # def delete_info_collection(self):
    #     if self.db is not None:
    #         self.db.delete_collection(NODES_INFO)

    def get_state(self):
        # Let's return the user requirements, last tsch schedule, current slotframe size
        state = {
            "user_requirements": self.user_requirements,
            "alpha": self.alpha,
            "beta": self.beta,
            "delta": self.delta,
            "last_ts_in_schedule": self.network.tsch_last_ts(),
            "current_sf_len": self.network.tsch_slotframe_size
        }
        return state

# User requirements class; this is only for RL


class UserRequirements():
    def __init__(self):
        self.__alpha = 0
        self.__beta = 0
        self.__delta = 0
        self.__user_requirements = np.array([0.4, 0.4, 0.3])

    @property
    def type(self):
        energy = np.array([0.8, 0.1, 0.1])
        delay = np.array([0.1, 0.8, 0.1])
        reliability = np.array([0.1, 0.1, 0.8])
        balanced = np.array([0.4, 0.3, 0.3])
        user_req = self.requirements
        comparison = user_req == energy
        if comparison.all():
            return "energy"
        comparison = user_req == delay
        if comparison.all():
            return "delay"
        comparison = user_req == reliability
        if comparison.all():
            return "pdr"
        comparison = user_req == balanced
        if comparison.all():
            return "balanced"

    @property
    def requirements(self):
        user_req = [
            self.alpha,
            self.beta,
            self.delta
        ]
        self.__user_requirements = user_req
        return self.__user_requirements

    @requirements.setter
    def requirements(self, val):
        try:
            alpha, beta, delta = val
        except ValueError:
            raise ValueError("Pass an iterable with three items")
        else:
            """ This will run only if no exception was raised """
            self.alpha = alpha
            self.beta = beta
            self.delta = delta

    def check_valid_number(func):
        def inner(self, val):
            if val > 1 or val < 0:
                logger.error("Invalid user requirement value.")
                return

            return func(self, val)
        return inner

    @property
    def alpha(self):
        return self.__alpha

    @alpha.setter
    @check_valid_number
    def alpha(self, val):
        self.__alpha = val

    @property
    def beta(self):
        return self.__beta

    @beta.setter
    @check_valid_number
    def beta(self, val):
        self.__beta = val

    @property
    def delta(self):
        return self.__delta

    @delta.setter
    @check_valid_number
    def delta(self, val):
        self.__delta = val
