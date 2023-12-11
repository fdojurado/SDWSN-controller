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
from rich.logging import RichHandler
from stable_baselines3 import PPO

import pandas as pd

import logging.config
import shutil
import sys
import os


CONFIG_FILE = "long_run.json"
TRAINED_MODEL = "./trained_model/best_model.zip"


def run(env, model_path, controller, output_folder, simulation_name):
    # Load model
    model = PPO.load(model_path)
    # Pandas df to store results at each iteration
    df = pd.DataFrame()
    # Reset environment
    obs, _ = env.reset()
    for _ in range(1000000):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, truncated, info = env.step(action)
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
    controller = controller_class(config)
    # ----------------- Environment ----------------------------
    env = controller.reinforcement_learning.env
    # --------------------Start RL --------------------------------
    run(env, TRAINED_MODEL, controller, output_folder, controller.simulation_name)

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


if __name__ == '__main__':
    main()
    sys.exit(0)
