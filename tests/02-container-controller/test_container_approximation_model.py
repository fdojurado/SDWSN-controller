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
import pandas as pd

from gym.envs.registration import register
import gym

import numpy as np

import os

from sdwsn_controller.network.network import Network

from sdwsn_controller.controller.container_controller \
    import ContainerController
from sdwsn_controller.reinforcement_learning.reward_processing \
    import EmulatedRewardProcessing
from sdwsn_controller.result_analysis import run_analysis
from sdwsn_controller.routing.dijkstra import Dijkstra
from sdwsn_controller.tsch.hard_coded_schedule import HardCodedScheduler


import shutil

from stable_baselines3.common.monitor import Monitor

# This number has to be unique across all test
# otherwise, the github actions will fail
# TEST: This might not be necessary anymore.
PORT = 60004

MAX_SLOTFRAME_SIZE = 70


def run(env, controller, output_folder, simulation_name):
    # Pandas df to store results at each iteration
    df = pd.DataFrame()
    # Reset environment
    obs = env.reset()
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
    for _ in range(20):
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
        df,
        'power',
        output_folder,
        'current_sf_len',
        'power_normalized',
        r'$|C|$',
        r'$\widetilde{P}$',
        4,
        [8, 0.89],
        [0.86, 0.9]
    )
    # Normalized delay
    run_analysis.plot_fit_curves(
        df,
        'delay',
        output_folder,
        'current_sf_len',
        'delay_normalized',
        r'$|C|$',
        r'$\widetilde{D}$',
        3,
        [8, 0.045],
        [0, 0.95]
    )
    run_analysis.plot_fit_curves(
        df,
        'reliability',
        output_folder,
        'current_sf_len',
        'pdr_mean',
        r'$|C|$',
        r'$\widetilde{R}$',
        1,
        [25, 0.7],
        [0.65, 1]
    )


def test_container_approximation_model():
    assert os.getenv('CONTIKI_NG')
    contiki_source = os.getenv('CONTIKI_NG')
    assert os.getenv('DOCKER_BASE_IMG')
    docker_image = os.getenv('DOCKER_BASE_IMG')
    docker_target = '/home/user/contiki-ng'
    # use different port number to avoid interfering with
    # the native controller
    simulation_folder = 'examples/elise'
    simulation_script = 'cooja-elise.csc'
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
                      socket_host='127.0.0.1', socket_port=PORT)

    # TSCH scheduler
    tsch_scheduler = HardCodedScheduler()

    # Reward processor
    reward_processor = EmulatedRewardProcessing(network=network)

    # Routing algorithm
    routing = Dijkstra()

    controller = ContainerController(
        docker_image=docker_image,
        simulation_script=simulation_script,
        simulation_folder=simulation_folder,
        docker_target=docker_target,
        contiki_source=contiki_source,
        port=PORT,
        # Reward processor
        network=network,
        reward_processing=reward_processor,
        routing=routing,
        tsch_scheduler=tsch_scheduler
    )
    # ----------------- RL environment ----------------------------
    env_kwargs = {
        'simulation_name': 'test_container_approximation_model',
        'folder': output_folder,
        'controller': controller
    }
    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)
    env = Monitor(env, log_dir)
    # --------------------Start RL --------------------------------
    run(env, controller, output_folder, 'test_container_approximation_model')

    result_analysis(
        output_folder+'test_container_approximation_model.csv', output_folder)

    controller.stop()

    # Delete folders
    try:
        shutil.rmtree(output_folder)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    try:
        shutil.rmtree(log_dir)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
