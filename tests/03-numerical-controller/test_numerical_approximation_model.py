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

from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.controller.numerical_controller import \
    NumericalRewardProcessing, NumericalController
from sdwsn_controller.result_analysis import run_analysis

import shutil

from stable_baselines3.common.monitor import Monitor


MAX_SLOTFRAME_SIZE = 70


def run(env, controller):
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

        env.step(action)
        # Get last observations non normalized
        observations = controller.get_state()
        assert 0 <= observations['alpha'] <= 1
        assert 0 <= observations['beta'] <= 1
        assert 0 <= observations['delta'] <= 1
        assert observations['last_ts_in_schedule'] > 1
        # Current SF size
        sf_size = observations['current_sf_len']
        assert sf_size > 1 and sf_size <= MAX_SLOTFRAME_SIZE
    env.render()
    env.close()


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


def test_numerical_approximation_model():
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
    # Database
    db = DatabaseManager()

    # Reward processor
    reward_processor = NumericalRewardProcessing(
        power_weights=np.array(
            [1.14247726e-08, -2.22419840e-06,
             1.60468046e-04, -5.27254015e-03, 9.35384746e-01]
        ),
        delay_weights=np.array(
            # [-2.98849631e-08,  4.52324093e-06,  5.80710379e-04,  1.02710258e-04]
            [-2.98849631e-08,  4.52324093e-06,  5.80710379e-04,
             0.85749587960003453947587046868728]
        ),
        pdr_weights=np.array(
            # [-2.76382789e-04,  9.64746733e-01]
            [-2.76382789e-04,  -0.8609615946299346738365592202098]
        )
    )

    controller = NumericalController(
        db=db,
        reward_processing=reward_processor
    )
    # ----------------- RL environment ----------------------------
    env_kwargs = {
        'simulation_name': 'test_numerical_approximation_model',
        'folder': output_folder,
        'controller': controller
    }
    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)
    env = Monitor(env, log_dir)
    # --------------------Start RL --------------------------------
    run(env, controller)

    result_analysis(
        output_folder+'test_numerical_approximation_model.csv', output_folder)

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
