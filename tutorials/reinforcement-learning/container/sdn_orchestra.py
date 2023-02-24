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

from sdwsn_controller.network.network import Network
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.controller.container_controller import ContainerController
from sdwsn_controller.reinforcement_learning.reward_processing import EmulatedRewardProcessing
from sdwsn_controller.packet.packet_dissector import PacketDissector
from sdwsn_controller.routing.dijkstra import Dijkstra
from rich.logging import RichHandler
import logging.config
import sys
import gym
from gym.envs.registration import register

import os

DOCKER_IMAGE = 'contiker/contiki-ng'
SIMULATION_FOLDER = 'examples/elise'
DOCKER_TARGET = '/home/user/contiki-ng'
CONTIKI_SOURCE = '/Users/fernando/contiki-ng'
SIMULATION_SCRIPT = 'cooja-orchestra.csc'
PORT = 60003


def run_data_plane(env):
    num_actions = 0
    for _ in range(1):
        env.reset()
        done = False
        acc_reward = 0
        # Set initial user requirements
        env.controller.user_requirements = (0.4, 0.3, 0.3)
        while (not done):
            if num_actions == 40:
                env.controller.user_requirements = (0.1, 0.8, 0.1)
            if num_actions == 80:
                env.controller.user_requirements = (0.8, 0.1, 0.1)
            if num_actions == 120:
                env.controller.user_requirements = (0.1, 0.1, 0.8)
            num_actions += 1
            action = 2
            obs, reward, done, _ = env.step(action)
            acc_reward += reward
            if done:
                print(f"episode done. reward: {acc_reward}")
                env.render()

    env.close()


def main():

    # -------------------- Create logger --------------------
    logger = logging.getLogger('main')

    formatter = logging.Formatter(
        '%(asctime)s - %(message)s')
    logger.setLevel(logging.DEBUG)

    stream_handler = RichHandler(rich_tracebacks=True)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    logFilePath = "my.log"
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s |  %(levelname)s: %(message)s')
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=logFilePath, when='midnight', backupCount=30)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    # -------------------- setup controller --------------------
    # Register the environment
    register(
        # unique identifier for the env `name-version`
        id="sdwsn-v1",
        entry_point="sdwsn_controller.reinforcement_learning.env:Env",
        max_episode_steps=50
    )
    # Create output folder
    output_folder = './output/'
    os.makedirs(output_folder, exist_ok=True)

    # Monitor the environment
    log_dir = './tensorlog/'
    os.makedirs(log_dir, exist_ok=True)

    # Network
    network = Network(processing_window=200,
                      socket_host='127.0.0.1', socket_port=PORT)

    # TSCH scheduler
    tsch_scheduler = ContentionFreeScheduler()

    # Reward processor
    reward_processor = EmulatedRewardProcessing(network=network)

    # Routing algorithm
    routing = Dijkstra()

    controller = ContainerController(
        docker_image=DOCKER_IMAGE,
        simulation_folder=SIMULATION_FOLDER,
        simulation_script=SIMULATION_SCRIPT,
        docker_target=DOCKER_TARGET,
        contiki_source=CONTIKI_SOURCE,
        port=PORT,
        # Reward processor
        network=network,
        reward_processing=reward_processor,
        routing=routing,
        tsch_scheduler=tsch_scheduler
    )
    env_kwargs = {
        'simulation_name': 'test_numerical_approximation_model',
        'folder': output_folder,
        'controller': controller
    }
    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)
    # --------------------Start data plane ------------------------
    # Let's start the data plane first
    run_data_plane(env)

    logger.info('done, exiting.')

    controller.stop()

    return


if __name__ == '__main__':
    main()
    sys.exit(0)
