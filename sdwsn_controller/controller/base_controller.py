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

import gymnasium as gym

import numpy as np

from sdwsn_controller.config import REWARD_PROCESSORS, TSCH_SCHEDULERS, ROUTING_ALGO, SINK_COMMUNICATION
from sdwsn_controller.reinforcement_learning.reinforcement_learning import ReinforcementLearning
from sdwsn_controller.sink_communication.sink_abc import SinkABC
from sdwsn_controller.reinforcement_learning.env import Env
from sdwsn_controller.mqtt.app_layer import AppLayer
from sdwsn_controller.network.network import Network


from time import sleep


logger = logging.getLogger(f'main.{__name__}')


class BaseController(ABC):

    def __init__(
        self,
        config
    ):
        """
        The BaseController class is an abstract class. Some functionalities are
        declared as abstract methods, classes that inherit from the BaseController
        should take care of them. The controller has four main modules: network,
        reward processing, routing, and TSCH scheduler.

        Args:
            config: A configuration object that defines the parameters for the controller.
        """

        # Create sink comm interface
        if config.sink_comm.name:
            sink_comm_class = SINK_COMMUNICATION[config.sink_comm.name]
            self.sink_comm = sink_comm_class(config)
            assert isinstance(self.sink_comm, SinkABC)
            logger.info(f"Sink comm: {self.sink_comm.name}")
        else:
            logger.warn("No sink communication interface running")
            self.sink_comm = None

        # Create network
        if config.network.name:
            self.network = Network(
                config=config,
                socket=self.sink_comm
            )
            assert isinstance(self.network, Network)
            logger.info(f"Network: {self.network.name}")
        else:
            logger.warn("No network running")
            self.network = None

        # Create reward module; only for RL
        reward_processing_class = REWARD_PROCESSORS[
            config.reinforcement_learning.reward_processor
        ]
        reward_processor = reward_processing_class(
            config,
            network=self.network,
        )

        # Reinforcement learning module
        env = Env(
            # config.reinforcement_learning.id,
            controller=self,
            max_slotframe_size=config.tsch.max_slotframe
        )
        env = gym.wrappers.TimeLimit(
            env,
            max_episode_steps=config.reinforcement_learning.max_episode_steps
        )
        self.reinforcement_learning = ReinforcementLearning(
            env=env,
            reward_processor=reward_processor
        )

        # Requirements
        self.__user_requirements = UserRequirements()

        # Create TSCH scheduler module
        if config.tsch.scheduler:
            tsch_scheduler_class = TSCH_SCHEDULERS[config.tsch.scheduler]
            self.tsch_scheduler = tsch_scheduler_class(
                network=self.network
            )
            logger.info(f'TSCH scheduler: {self.tsch_scheduler.name}')
        else:
            logger.warn("No TSCH scheduler running")
            self.tsch_scheduler = None
        # Create an instance of Router
        if config.routing.algo:
            router_class = ROUTING_ALGO[config.routing.algo]
            self.router = router_class(
                network=self.network
            )
            logger.info(f'Routing: {self.router.name}')
        else:
            logger.warn("No routing algorithm running")
            self.router = None

        # MQTT interface
        if config.mqtt.host:
            self.app_layer = AppLayer(
                config=config,
                controller=self
            )
            logger.info(f'MQTT: {self.app_layer.name}')
            # Register callbacks
            if self.network:
                self.network.register_energy_callback(
                    self.app_layer.send_energy)
                self.network.register_delay_callback(
                    self.app_layer.send_latency)
                self.network.register_pdr_callback(
                    self.app_layer.send_pdr)
            if self.reinforcement_learning:
                self.reinforcement_learning.register_callback(
                    self.app_layer.send_rl_info)
        else:
            logger.warn("No MQTT instance running")
            self.app_layer = None

        # Simulation name
        self.simulation_name = config.name

        self.controller_running = False

        super().__init__()

    # --------------------------With statement--------------------------
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    # --------------------------Modules access--------------------------
    @property
    def network(self):
        return self.__network

    @network.setter
    def network(self, val):
        # TODO: Checks to ensure it is valid network class
        # if val is not None:
        self.__network = val

    @property
    def tsch_scheduler(self):
        return self.__tsch_scheduler

    @tsch_scheduler.setter
    def tsch_scheduler(self, val):
        # assert isinstance(val, TSCHScheduler)
        self.__tsch_scheduler = val

    @property
    def router(self):
        return self.__router

    @router.setter
    def router(self, val):
        # assert isinstance(val, Router)
        self.__router = val

    @property
    def app_layer(self):
        return self.__app_layer

    @app_layer.setter
    def app_layer(self, val):
        self.__app_layer = val

    # --------------------------TSCH functions--------------------------

    def send_tsch_schedules(self):
        # FIXME: Function is too complex. We need to split this function.
        """
        It sends the TSCH links to the sink.

        Returns:
            int: 1 is successful; 0 otherwise.
        """
        if self.tsch_scheduler:
            return self.network.tsch_sendall()

    def compute_tsch_schedule(self, path, current_sf_size):
        if self.tsch_scheduler:
            self.tsch_scheduler.run(path, current_sf_size)

    @ property
    def last_tsch_link(self):
        if self.tsch_scheduler:
            return self.network.tsch_last_ts()

    @ last_tsch_link.setter
    def last_tsch_link(self, val):
        # We pass because this is not valid in TSCH network
        # Automatically done by the scheduler
        pass

    @ property
    def current_slotframe_size(self):
        if self.tsch_scheduler:
            return self.network.tsch_slotframe_size

    @ current_slotframe_size.setter
    def current_slotframe_size(self, val):
        if self.tsch_scheduler:
            self.network.tsch_slotframe_size = val

    # --------------------------Routing functions-------------------------

    def send_routes(self):
        """
        It sends the routing paths to the sink.

        Returns:
            int: 1 is successful; 0 otherwise.
        """
        if self.router:
            return self.network.routes_sendall()

    def compute_routes(self, G):
        if self.router:
            return self.router.run(G)

    def get_network_links(self):
        if self.router:
            return self.network.links()

    # --------------------------Controller primitives-----------------------

    def start(self):
        if self.network:
            self.network.start()
        if self.app_layer:
            self.app_layer.start()
        self.controller_running = True

    def stop(self):
        if self.network:
            self.network.stop()
        if self.app_layer:
            self.app_layer.stop()
        # Clear the running flag
        self.controller_running = False

    @ abstractmethod
    def reset(self):
        pass

    def wait(self):
        return self.network.wait()

    @ abstractmethod
    def timeout(self):
        pass

    def processing_wait(self, time):
        sleep(time)

    def wait_seconds(self, seconds):
        sleep(seconds)

    # --------------------------Reinforcement Learning----------------------

    def calculate_reward(self, alpha, beta, delta, sf):
        return self.reinforcement_learning.calculate_reward(alpha, beta, delta, sf)

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
