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

# This test obtains the chart for the approximation model in Cooja (Docker).

from sdwsn_controller.controller.container_controller import ContainerController
from sdwsn_controller.tsch.hard_coded_schedule import HardCodedScheduler
from sdwsn_controller.routing.dijkstra import Dijkstra
from gym.envs.registration import register
from rich.logging import RichHandler
from sdwsn_controller import about
from signal import signal, SIGINT

import logging.config
import logging
import pyfiglet
import argparse
import sys
import gym
import os

logger = logging.getLogger('main.'+__name__)

MAX_SLOTFRAME_SIZE = 70


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

    # -------------------- Set Banner --------------------
    fig = pyfiglet.Figlet(font='standard')
    print(fig.renderText('SDWSN Controller'))
    print(about.__info_for_scripts__)

    # -------------------- Parse arguments ---------------
    parser = argparse.ArgumentParser(
        description='This script obtains the plot for the approximation model in Cooja.')
    parser.add_argument('-d', '--docker-image', type=str, default='contiker/contiki-ng',
                        help="Name of the docker image ('contiker/contiki-ng')")
    parser.add_argument('-dc', '--contiki-folder', type=str, default='examples/elise',
                        help="Contiki simulaiton folder")
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
    parser.add_argument('-db', '--db', type=str, default='127.0.0.1',
                        help='Database address')
    parser.add_argument('-dbp', '--db-port', type=int, default=27017,
                        help='Database port')
    parser.add_argument('-ms', '--simulation-name', type=str, default='training',
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

    args = parser.parse_args()

    # Example for the CartPole environment
    register(
        # unique identifier for the env `name-version`
        id="sdwsn-v1",
        # path to the class for creating the env
        # Note: entry_point also accept a class as input (and not only a string)
        entry_point="sdwsn_controller.reinforcement_learning.env:Env",
        # Max number of steps per episode, using a `TimeLimitWrapper`
        # max_episode_steps=50
    )

    # Create output folder
    log_dir = args.output_path
    os.makedirs(log_dir, exist_ok=True)

    simulation_command = '/bin/sh -c '+'"cd ' + \
        args.contiki_folder+' && ./run-cooja.py cooja-elise.csc"'

    # Routing algorithm
    routing = Dijkstra()

    tsch_scheduler = HardCodedScheduler(
        sf_size=args.maximum_slotframe_size, channel_offsets=args.maximum_tsch_channels)

    controller = ContainerController(
        # Container related
        image=args.docker_image,
        command=simulation_command,
        target=args.docker_mount_target,
        source=args.docker_mount_source,
        socket_file=args.docker_mount_source+'/'+args.contiki_folder+'/'+'COOJA.log',
        # Sink/socket communication
        socket_address=args.cooja,
        socket_port=args.cooja_port,
        # Database
        db_name=args.db_name,
        db_host=args.db,
        db_port=args.db_port,
        # Routing
        router=routing,
        # TSCH scheduler
        tsch_scheduler=tsch_scheduler,
        # RL related
        processing_window=args.processing_window,
    )

    env_kwargs = {
        'simulation_name': args.simulation_name,
        'controller': controller,
        'folder': args.output_path
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

    obs = env.reset()
    # Get last observations including the SF size
    observations = controller.get_state()
    # Current SF size
    sf_size = observations['current_sf_len']
    last_ts_in_schedule = observations['last_ts_in_schedule']
    increase = 1
    for i in range(200):
        # action, _state = model.predict(obs, deterministic=True)
        if increase:
            if sf_size < MAX_SLOTFRAME_SIZE - 1:
                action = 0
            else:
                increase = 0
        else:
            if sf_size > last_ts_in_schedule + 1:
                action = 1
            else:
                increase = 1
                # done = True
                # obs = env.reset()

        obs, reward, done, info = env.step(action)
        logger.info(f'Observations: {obs}, reward: {reward}, done: {done}, info: {info}')
        # Get last observations including the SF size
        observations = controller.get_state()
        # Current SF size
        sf_size = observations['current_sf_len']
        logger.info(f'current SF size: {sf_size}')

    env.render()

    return


if __name__ == '__main__':
    main()
    sys.exit(0)
