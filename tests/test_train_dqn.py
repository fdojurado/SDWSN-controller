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

import sys
import argparse
import gym
import os

from sdwsn_controller.reinforcement_learning.wrappers import SaveModelSaveBuffer
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EveryNTimesteps
from gym.envs.registration import register
# import signal


def main():

    parser = argparse.ArgumentParser(
        description='It trains DQN using the given, or default parameters.')
    parser.add_argument('-d', '--docker-image', type=str, default='contiker/contiki-ng',
                        help="Name of the docker image ('contiker/contiki-ng')")
    parser.add_argument('-dc', '--docker-command', type=str, default='examples/benchmarks/rl-sdwsn',
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

    args = parser.parse_args()

    # Example for the CartPole environment
    register(
        # unique identifier for the env `name-version`
        id="sdwsn-v1",
        # path to the class for creating the env
        # Note: entry_point also accept a class as input (and not only a string)
        entry_point="sdwsn_reinforcement_learning.env:Env",
        # Max number of steps per episode, using a `TimeLimitWrapper`
        max_episode_steps=50
    )

    # Monitor the environment
    log_dir = "./tensorlog/"
    os.makedirs(log_dir, exist_ok=True)

    # container_controller = ContainerController(
    #     cooja_host=args.socket, cooja_port=args.port,
    #     max_channel_offsets=args.tschmaxchannel, max_slotframe_size=args.tschmaxslotframe,
    #     log_dir=log_dir)
    # controller = BaseController(cooja_host=args.socket, cooja_port=args.port)

    # def exit_process(signal_number, frames):
    #     # pylint: disable=no-member
    #     print('Received %s signal. Exiting...',
    #           signal.Signals(signal_number).name)
    #     container_controller.container_controller_shutdown()
    #     sys.exit(0)

    # signal.signal(signal.SIGINT, exit_process)
    # signal.signal(signal.SIGQUIT, exit_process)
    # signal.signal(signal.SIGTERM, exit_process)

    simulation_command = '/bin/sh -c '+'"cd ' + \
        args.docker_command+' && ./run-cooja.py"'

    env_kwargs = {
        'target': args.docker_mount_target,
        'source': args.docker_mount_source,
        'simulation_command': simulation_command,
        'host': args.cooja,
        'port': args.cooja_port,
        'socket_file': args.docker_mount_source+'/'+args.docker_command+'/'+'COOJA.log',
        'db_name': args.db_name,
        'simulation_name': args.simulation_name,
        'tsch_scheduler': 'Unique Schedule'
    }
    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)

    # Wrap the environment to limit the max steps per episode
    # env = gym.wrappers.TimeLimit(env, max_episode_steps=5)

    # env = Monitor(env, log_dir)

    # Callback to save the model and replay buffer every N steps.
    # save_model_replay = SaveModelSaveBuffer(save_path='./logs/')
    # event_callback = EveryNTimesteps(n_steps=50, callback=save_model_replay)

    # Create an instance of the RL model to use
    model = DQN('MlpPolicy', env, verbose=1, learning_starts=10, tensorboard_log=log_dir,
                target_update_interval=50, exploration_fraction=0.1)

    model.learn(total_timesteps=int(50000),
                log_interval=1)


if __name__ == '__main__':
    main()
    sys.exit(0)
