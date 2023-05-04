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
from sdwsn_controller.config import SDWSNControllerConfig, CONTROLLERS
from sdwsn_controller.result_analysis import run_analysis

from rich.logging import RichHandler

import pandas as pd
import numpy as np

import logging.config
import shutil
import sys
import os


CONFIG_FILE = "native_controller_approx_model.json"


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
    for _ in range(1000000):
        if increase:
            if sf_size < env.max_slotframe_size - 2:
                action = 0
            else:
                increase = 0
        else:
            if sf_size > last_ts_in_schedule + 2:
                action = 1
            else:
                increase = 1

        _, _, _, truncated, info = env.step(action)
        # Get last observations non normalized
        observations = controller.get_state()
        assert 0 <= observations['alpha'] <= 1
        assert 0 <= observations['beta'] <= 1
        assert 0 <= observations['delta'] <= 1
        assert observations['last_ts_in_schedule'] > 1
        # Current SF size
        sf_size = observations['current_sf_len']
        assert sf_size > 1 and sf_size <= env.max_slotframe_size
        # Add row to DataFrame
        new_cycle = pd.DataFrame([info])
        df = pd.concat([df, new_cycle], axis=0, ignore_index=True)
        if truncated:
            # if info['TimeLimit.truncated'] == True:
            print('Number of max episodes reached')
            break
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
    # ----------------- RL environment, setup --------------------
    # Create output folder
    output_folder = './output/'
    os.makedirs(output_folder, exist_ok=True)

    # Monitor the environment
    log_dir = './tensorlog/'
    os.makedirs(log_dir, exist_ok=True)
    # -------------------- setup controller ---------------------
    config = SDWSNControllerConfig.from_json_file(CONFIG_FILE)
    controller_class = CONTROLLERS[config.controller_type]
    with controller_class(config) as controller:
        # ----------------- Environment ----------------------------
        env = controller.reinforcement_learning.env
        # --------------------Start RL --------------------------------
        run(env, controller, output_folder, controller.simulation_name)

        result_analysis(
            output_folder+controller.simulation_name+'.csv', output_folder)

    # Delete folders
    try:
        shutil.rmtree(output_folder)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    try:
        shutil.rmtree(log_dir)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))


if __name__ == '__main__':
    main()
    sys.exit(0)
