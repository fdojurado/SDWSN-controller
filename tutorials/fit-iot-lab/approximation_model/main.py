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
from sdwsn_controller.reinforcement_learning.reward_processing \
    import EmulatedRewardProcessing
from sdwsn_controller.result_analysis import run_analysis
from sdwsn_controller.routing.dijkstra import Dijkstra
from sdwsn_controller.controller.fit_iot_lab_controller import FitIoTLABController
from sdwsn_controller.tsch.hard_coded_schedule import HardCodedScheduler
from stable_baselines3.common.monitor import Monitor
from gymnasium.envs.registration import register
from rich.logging import RichHandler
from fit_iot_lab import common
import pandas as pd
import numpy as np

import logging
# import shutil
import sys
import gymnasium as gym
import os
import argparse

# Create logger
logger = logging.getLogger(__name__)

# get the path of this example
SELF_PATH = os.path.dirname(os.path.abspath(__file__))
# move three levels up
ELISE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(SELF_PATH)))
ARCH_PATH = os.path.normpath(os.path.join(
    ELISE_PATH, "iot-lab-contiki-ng", "arch"))
CONTIKI_PATH = os.path.normpath(os.path.join(ELISE_PATH, "contiki-ng"))


MAX_SLOTFRAME_SIZE = 70


def main():

    parser = argparse.ArgumentParser(
        description='This runs the SDWSN approximation model in the FIT IoT LAB.')

    # Arguments for the FIT IoT LAB platform
    parser.add_argument('username', type=str,
                        help='Username')
    parser.add_argument('password', type=str,
                        help='Password')
    parser.add_argument('node_list', nargs='+',
                        help='Sensor nodes list, the first node is assigned to the sink')

    parser.add_argument('-pt', '--platform-target', type=str,
                        default='iotlab', help='Sensor platform to use')
    parser.add_argument('-t', '--time', type=int,
                        default=10, help='Length in minutes of the experiment')
    parser.add_argument('-s', '--site', type=str,
                        default='grenoble', help='FIT IoT LAB site')
    parser.add_argument('-b', '--board', type=str,
                        default='m3', help='Sensor board name')
    parser.add_argument('-e', '--end-node', type=str,
                        default='/examples/sdn-tsch-node/', help='Path, within Contiki folder, to the end node example')
    parser.add_argument('-c', '--controller', type=str,
                        default='/examples/sdn-tsch-sink/', help='Path, within Contiki folder, to sink example')
    parser.add_argument('-dbg', '--debug_level', default='NOTSET',
                        help='Debug level, default NOTSET.')
    parser.add_argument('-hp', '--home-port', type=int,
                        default=2000, help='home port')
    # Arguments for Contiki
    parser.add_argument('-p', '--target-port', type=int, default=20000,
                        help='target port')

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
    # Compile firmware
    firmware_dir = os.path.normpath(os.path.join(
        SELF_PATH, "firmware"))
    logger.info(f'firmware folder: {firmware_dir}')
    os.makedirs(firmware_dir, exist_ok=True)
    # The NODE ID for the end node starts with 2.
    N = len(args.node_list)
    count = 2
    app = CONTIKI_PATH+args.end_node
    while (count <= N):
        node_id = count
        common.compile_firmware(firmware_dir, ARCH_PATH, 'sdn-tsch-node.iotlab', app,
                                args.platform_target, str(1), args.board, str(node_id))
        count += 1

    # We now build the `tsch-sdn-controller` application
    app = CONTIKI_PATH+args.controller
    common.compile_firmware(firmware_dir, ARCH_PATH, 'sdn-tsch-sink.iotlab', app,
                            args.platform_target, str(1), args.board, str(1))

    return args, firmware_dir


def run(env, controller, output_folder, simulation_name):
    # Pandas df to store results at each iteration
    df = pd.DataFrame()
    # Reset environment
    obs, _ = env.reset()
    assert np.all(obs)
    # Get last observations (not normalized) including the SF size
    observations = controller.get_state()
    assert 0 <= observations['alpha'] <= 1
    assert 0 <= observations['beta'] <= 1
    assert 0 <= observations['delta'] <= 1
    assert observations['last_ts_in_schedule'] > 1
    # Current SF size
    sf_size = observations['current_sf_len']
    last_ts_in_schedule = observations['last_ts_in_schedule']
    controller.user_requirements = (0.4, 0.3, 0.3)
    increase = 1
    for _ in range(200):
        if increase:
            if sf_size < MAX_SLOTFRAME_SIZE - 2:
                action = 0
            else:
                increase = 0
        else:
            if sf_size > last_ts_in_schedule + 2:
                action = 1
            else:
                increase = 1

        _, _, _, info = env.step(action)
        # Get last observations non normalized
        observations = controller.get_state()
        assert 0 <= observations['alpha'] <= 1
        assert 0 <= observations['beta'] <= 1
        assert 0 <= observations['delta'] <= 1
        assert observations['last_ts_in_schedule'] > 1
        # Current SF size
        sf_size = observations['current_sf_len']
        assert sf_size > 1 and sf_size <= MAX_SLOTFRAME_SIZE
        # Add row to DataFrame
        new_cycle = pd.DataFrame([info])
        df = pd.concat([df, new_cycle], axis=0, ignore_index=True)
    df.to_csv(output_folder+simulation_name+'.csv')
    # env.render()
    # env.close()


def result_analysis(path, output_folder):
    df = pd.read_csv(path)
    # Normalized power
    run_analysis.plot_fit_curves(
        df=df,
        title='power',
        path=output_folder,
        x_axis='current_sf_len',
        y_axis='power_normalized',
        x_axis_name=r'$|C|$',
        y_axis_name=r'$\widetilde{P}$',
        degree=4,
        # txt_loc=[8, 0.89],
        # y_axis_limit=[0.86, 0.9]
    )
    # Normalized delay
    run_analysis.plot_fit_curves(
        df=df,
        title='delay',
        path=output_folder,
        x_axis='current_sf_len',
        y_axis='delay_normalized',
        x_axis_name=r'$|C|$',
        y_axis_name=r'$\widetilde{D}$',
        degree=3,
        # txt_loc=[8, 0.045],
        # y_axis_limit=[0, 0.95]
    )
    run_analysis.plot_fit_curves(
        df=df,
        title='reliability',
        path=output_folder,
        x_axis='current_sf_len',
        y_axis='pdr_mean',
        x_axis_name=r'$|C|$',
        y_axis_name=r'$\widetilde{R}$',
        degree=1,
        # txt_loc=[25, 0.7],
        # y_axis_limit=[0.65, 1]
    )
    # Metrics vs. Slotframe Size
    run_analysis.plot_against_sf_size(
        df=df,
        title="slotframe_size",
        path=output_folder
    )


def launch_controller(args):

    # ----------------- RL environment, setup --------------------
    # Register the environment
    register(
        # unique identifier for the env `name-version`
        id="sdwsn-v1",
        entry_point="sdwsn_controller.reinforcement_learning.env:Env",
    )

    # Create output folder
    output_folder = './output/'
    os.makedirs(output_folder, exist_ok=True)

    # Monitor the environment
    log_dir = './tensorlog/'
    os.makedirs(log_dir, exist_ok=True)
    # -------------------- setup controller ---------------------
    # Network
    network = Network(processing_window=200,
                      socket_host='127.0.0.1', socket_port=args.home_port)
    # TSCH scheduler
    tsch_scheduler = HardCodedScheduler()

    # Reward processor
    reward_processor = EmulatedRewardProcessing(network=network)

    # Routing algorithm
    routing = Dijkstra()

    controller = FitIoTLABController(
        network=network,
        reward_processing=reward_processor,
        routing=routing,
        tsch_scheduler=tsch_scheduler
    )
    # ----------------- RL environment ----------------------------
    env_kwargs = {
        'simulation_name': 'approximation_model_cooja',
        'folder': output_folder,
        'controller': controller
    }
    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)
    env = Monitor(env, log_dir)
    # --------------------Start RL --------------------------------
    run(env, controller, output_folder, 'approximation_model_cooja')

    result_analysis(
        output_folder+'approximation_model_cooja.csv', output_folder)

    controller.stop()

    # Delete folders
    # try:
    #     shutil.rmtree(output_folder)
    # except OSError as e:
    #     print("Error: %s - %s." % (e.filename, e.strerror))
    # try:
    #     shutil.rmtree(log_dir)
    # except OSError as e:
    #     print("Error: %s - %s." % (e.filename, e.strerror))


if __name__ == '__main__':
    arguments, firmware_dir = main()
    common.launch_iotlab(arguments, firmware_dir)
    launch_controller(arguments)
    sys.exit(0)
