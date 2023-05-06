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
import os

from sdwsn_controller.config import SDWSNControllerConfig, CONTROLLERS

import numpy as np

import shutil

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor


SELF_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.normpath(os.path.join(
    SELF_PATH, "numerical_controller_rl.json"))


def train(env, log_dir):
    """
    Just use the PPO algorithm.
    """
    model = PPO("MlpPolicy", env,
                tensorboard_log=log_dir, verbose=0)

    model.learn(total_timesteps=int(1e5),
                tb_log_name='training')
    # Let's save the model
    path = "".join([log_dir, "ppo_sdwsn"])
    model.save(path)

    del model  # remove to demonstrate saving and loading

    return path


def evaluation(env, model_path):
    model = PPO.load(model_path)

    total_reward = 0

    # Test the trained agent
    for _ in range(50):
        obs, _ = env.reset()
        done = False
        acc_reward = 0
        # Get last observations non normalized
        observations = env.controller.get_state()
        assert 0 <= observations['alpha'] <= 1
        assert 0 <= observations['beta'] <= 1
        assert 0 <= observations['delta'] <= 1
        assert observations['last_ts_in_schedule'] > 1
        # get requirements
        user_req_type = env.controller.user_requirements_type
        match user_req_type:
            case 'energy':
                env.controller.current_slotframe_size = env.controller.last_tsch_link+5
            case 'delay':
                env.controller.current_slotframe_size = env.max_slotframe_size-5
            case 'pdr':
                env.controller.current_slotframe_size = env.max_slotframe_size-5
            case 'balanced':
                env.controller.current_slotframe_size = env.max_slotframe_size-5
            case _:
                print("Unknow user requirements.")
        while (not done):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            # Get last observations non normalized
            observations = env.controller.get_state()
            acc_reward += reward
            # Get last observations non normalized
            observations = env.controller.get_state()
            assert 0 <= observations['alpha'] <= 1
            assert 0 <= observations['beta'] <= 1
            assert 0 <= observations['delta'] <= 1
            assert observations['last_ts_in_schedule'] > 1
            if done:
                total_reward += acc_reward

    # Total reward, for this scenario, should be above 65.
    assert total_reward/50 > 30


def test_numerical_reinforcement_learning():
    """
    This test the training, loading and testing of RL env.
    We dont use DB to avoid reducing the processing speed
    """
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
    # ----------------- RL environment ----------------------------
    train_env = controller.reinforcement_learning.env
    train_env = Monitor(train_env, log_dir)
    # Train the agent
    model_path = train(train_env, log_dir)
    # ----------------- Test environment ----------------------------
    controller.reinforcement_learning.reward_processor.power_trendpoly = np.poly1d(
        np.array(
            [1.14247726e-08, -2.22419840e-06,
             1.60468046e-04, -5.27254015e-03, 9.35384746e-01]
        )
    )
    controller.reinforcement_learning.reward_processor.delay_trendpoly = np.poly1d(
        np.array(
            # [-2.98849631e-08,  4.52324093e-06,  5.80710379e-04,  1.02710258e-04]
            [-2.98849631e-08,  4.52324093e-06,  5.80710379e-04,
             0.85749587960003453947587046868728]
        )
    )
    controller.reinforcement_learning.reward_processor.pdr_trendpoly = np.poly1d(
        np.array(
            [-2.76382789e-04,  9.64746733e-01]
            # [-2.76382789e-04,  -0.8609615946299346738365592202098]
        )
    )
    test_env = controller.reinforcement_learning.env
    evaluation(test_env, model_path)
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
