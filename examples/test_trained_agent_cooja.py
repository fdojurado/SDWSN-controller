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

"""
This script test the trained agent in Cooja Network Simulator.
"""
from sdwsn_controller.controller.container_controller import ContainerController
from sdwsn_controller.tsch.hard_coded_schedule import HardCodedScheduler
from stable_baselines3 import DQN, A2C, PPO
from gym.envs.registration import register
from rich.logging import RichHandler
from sdwsn_controller import about
from signal import signal, SIGINT

import sys
import gym
import pyfiglet
import os
import argparse
import logging
import logging.config


def main():

    # Set banner
    fig = pyfiglet.Figlet(font='standard')
    print(fig.renderText('SDWSN Controller'))
    print(about.__info_for_scripts__)
    parser = argparse.ArgumentParser(
        description='This script tests the trained agent in Cooja environment.')

    parser.add_argument('model', type=str,
                        help="Path to the trained model")
    parser.add_argument('-d', '--docker-image', type=str, default='contiker/contiki-ng',
                        help="Name of the docker image ('contiker/contiki-ng')")
    parser.add_argument('-dc', '--docker-command', type=str, default='examples/elise',
                        help="Simulation script to run inside the container")
    parser.add_argument('-dmt', '--docker-mount-target', type=str, default='/home/user/contiki-ng',
                        help="Docker mount target")
    parser.add_argument('-dms', '--docker-mount-source', type=str, default='/Users/fernando/contiki-ng',
                        help="Docker mount source")
    parser.add_argument('-c', '--cooja', type=str, default='127.0.0.1',
                        help='Cooja host address')
    parser.add_argument('-p', '--cooja-port', type=int, default=60001,
                        help='Cooja socket port')
    parser.add_argument('-dbn', '--db-name', type=str, default='mySDN',
                        help='Give a name to your DB')
    parser.add_argument('-db', '--db-host', type=str, default='127.0.0.1',
                        help='Database address')
    parser.add_argument('-dbp', '--db-port', type=int, default=27017,
                        help='Database port')
    parser.add_argument('-ms', '--simulation-name', type=str, default='test_agent',
                        help='Name of your simulation')
    parser.add_argument('-w', '--processing-window', type=int, default=200,
                        help='Set the window for processing the reward')
    parser.add_argument('-mtc', '--maximum-tsch-channels', type=int, default=3,
                        help='Maximum TSCH channel offsets')
    parser.add_argument('-mfs', '--maximum-slotframe-size', type=int, default=500,
                        help='Maximum TSCH slotframe size')
    parser.add_argument('-te', '--maximum-timesteps-episode', type=int, default=50,
                        help='Maximum timesteps per episode')
    parser.add_argument('-fp', '--output-path', type=str, default='./output/',
                        help='Path to save results')
    parser.add_argument('-mt', '--model_type', type=str, default='PPO',
                        help='model type to train.')
    parser.add_argument('-dbg', '--debug_level', default='NOTSET',
                        help='Debug level, default NOTSET.')

    args = parser.parse_args()

    assert args.debug_level in ['CRITICAL',
                                'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'], "Incorrect debug level"
    # Set debug level
    logging.basicConfig(
        level=args.debug_level,
        format='%(asctime)s - %(message)s',
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    # Create logger
    logger = logging.getLogger(__name__)
    # Example for the CartPole environment
    register(
        # unique identifier for the env `name-version`
        id="sdwsn-v1",
        # path to the class for creating the env
        # Note: entry_point also accept a class as input (and not only a string)
        entry_point="sdwsn_controller.reinforcement_learning.env:Env",
        # Max number of steps per episode, using a `TimeLimitWrapper`
        max_episode_steps=160
    )

    # Create output folder
    log_dir = args.output_path
    os.makedirs(log_dir, exist_ok=True)

    simulation_command = '/bin/sh -c '+'"cd ' + \
        args.docker_command+' && ./run-cooja.py cooja-elise.csc"'

    tsch_scheduler = HardCodedScheduler(
        sf_size=args.maximum_slotframe_size, channel_offsets=args.maximum_tsch_channels)

    controller = ContainerController(
        image=args.docker_image,
        command=simulation_command,
        target=args.docker_mount_target,
        source=args.docker_mount_source,
        socket_file=args.docker_mount_source+'/'+args.docker_command+'/'+'COOJA.log',
        db_name=args.db_name,
        db_host=args.db_host,
        db_port=args.db_port,
        processing_window=args.processing_window,
        tsch_scheduler=tsch_scheduler
    )

    env_kwargs = {
        'simulation_name': args.simulation_name,
        'folder': args.output_path,
        'controller': controller
    }
    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)

    # Exit signal
    def handler(*args):
        # Handle any cleanup here
        logger.warning('SIGINT or CTRL-C detected. Shutting down ...')
        controller.stop()
        sys.exit(0)

    signal(SIGINT, handler)

    match(args.model_type):
        case 'DQN':
            loaded_model = DQN.load(args.model, env=env)
        case 'A2C':
            loaded_model = A2C.load(args.model, env=env)
        case 'PPO':
            loaded_model = PPO.load(args.model, env=env)

    num_actions = 0
    # Test the trained agent
    for i in range(1):
        obs = env.reset()
        done = False
        acc_reward = 0
        # Set initial user requirements
        controller.user_requirements = (0.4, 0.3, 0.3)
        while(not done):
            if num_actions == 40:
                controller.user_requirements = (0.1, 0.8, 0.1)
            if num_actions == 80:
                controller.user_requirements = (0.8, 0.1, 0.1)
            if num_actions == 120:
                controller.user_requirements = (0.1, 0.1, 0.8)
            num_actions += 1
            action, _ = loaded_model.predict(obs, deterministic=True)
            obs, reward, done, _ = env.step(action)
            acc_reward += reward
            if done:
                print(f"episode done. reward: {acc_reward}")
                env.render()

    env.close()


if __name__ == '__main__':
    main()
    sys.exit(0)
