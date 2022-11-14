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

# python3 train.py --algo dqn --env sdwsn-v2 -n 50000 -optimize --n-trials 1000 --n-jobs 2 --sampler tpe --pruner median

from sdwsn_controller.controller.numerical_controller import NumericalController, NumericalRewardProcessing
from sdwsn_controller.reinforcement_learning.wrappers import SaveOnBestTrainingRewardCallback
from stable_baselines3 import DQN, A2C, PPO, HerReplayBuffer, DDPG, DQN, SAC, TD3
from stable_baselines3.common.envs import BitFlippingEnv
from stable_baselines3.common.monitor import Monitor
from gym.envs.registration import register
from sdwsn_controller import about

from torch import nn as nn
import numpy as np

import argparse
import pyfiglet
import sys
import gym
import os


def main():

    # Set banner
    fig = pyfiglet.Figlet(font='standard')
    print(fig.renderText('SDWSN Controller'))
    print(about.__info_for_scripts__)

    parser = argparse.ArgumentParser(
        description='This trains the numerical environment based on the polynomial \
        coefficients found for the hard coded schedule.')

    parser.add_argument('-ms', '--simulation-name', type=str, default='training',
                        help='Name of your simulation')
    parser.add_argument('-t', '--tensorboard', type=str, default='./tensorlog/',
                        help='Path to log TensorBoard logging')
    parser.add_argument('-svm', '--save-model', type=str, default='./logs/',
                        help='Path to save the trained model')
    parser.add_argument('-m', '--model', type=str, default=None,
                        help='Path to the trained model to continue learning. Otherwise star fresh.')
    parser.add_argument('-mt', '--model_type', type=str, default='DQN',
                        help='model type to train.')

    args = parser.parse_args()

    # Example for the CartPole environment
    register(
        # unique identifier for the env `name-version`
        id="sdwsn-v1",
        # path to the class for creating the env
        # Note: entry_point also accept a class as input (and not only a string)
        entry_point="sdwsn_controller.reinforcement_learning.env:Env",
        # Max number of steps per episode, using a `TimeLimitWrapper`
        max_episode_steps=50
    )

    # Tensorboard the environment
    tensor_log_dir = args.tensorboard
    os.makedirs(tensor_log_dir, exist_ok=True)

    # Monitor the environment
    monitor_log_dir = args.save_model
    os.makedirs(monitor_log_dir, exist_ok=True)

    # -------------------- setup controller --------------------
    reward_processing = NumericalRewardProcessing(
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

    # Controller instance
    controller = NumericalController(
        reward_processing=reward_processing
    )

    env_kwargs = {
        'simulation_name': args.simulation_name,
        'controller': controller
    }

    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)

    env = Monitor(env, monitor_log_dir)

    best_model = SaveOnBestTrainingRewardCallback(
        check_freq=1000, log_dir=monitor_log_dir)

    # Params:
    # gamma: 0.98
    # learning_rate: 5.832985636420814e-05
    # batch_size: 256
    # buffer_size: 1000000
    # exploration_final_eps: 0.06038208749247105
    # exploration_fraction: 0.45629838266368317
    # target_update_interval: 20000
    # learning_starts: 5000
    # train_freq: 1000
    # subsample_steps: 1
    # net_arch: medium
    # Writing report to logs/dqn/report_sdwsn-v2_1000-trials-50000-tpe-median_1656979123
    # Create an instance of the RL model to use
    # model = DQN('MlpPolicy', env, verbose=1, gamma=0.98, learning_rate=5.832985636420814e-05, batch_size=256,
    #             buffer_size=1000000, exploration_final_eps=0.06038208749247105, exploration_fraction=0.45629838266368317, target_update_interval=20000,
    #             learning_starts=5000, train_freq=1000, tensorboard_log=tensor_log_dir)
    # Create an instance of the RL model to use

    if args.model is not None:
        print("loading model")
        match(args.model_type):
            case 'DQN':
                # Continue learning
                print("DQN")
                model = DQN.load(args.model, env=env)
            case 'PPO':
                print("PPO")
                model = PPO.load(args.model, env=env)
    else:
        print("no loading")
        match(args.model_type):
            case 'DQN':
                print("Training DQN")
                model = DQN("MlpPolicy", env,
                            tensorboard_log=tensor_log_dir, verbose=1)
            case 'A2C':
                print("Training A2c")
                model = A2C("MlpPolicy", env,
                            tensorboard_log=tensor_log_dir, verbose=1)
            case 'PPO':
                print("Training PPO")
                model = PPO("MlpPolicy", env,
                            tensorboard_log=tensor_log_dir, verbose=1)

            case 'HER':
                model_class = DQN  # works also with SAC, DDPG and TD3
                N_BITS = 50

                env = BitFlippingEnv(n_bits=N_BITS, continuous=model_class in [
                                     DDPG, SAC, TD3], max_steps=N_BITS)

                # Available strategies (cf paper): future, final, episode
                goal_selection_strategy = 'future'  # equivalent to GoalSelectionStrategy.FUTURE

                # If True the HER transitions will get sampled online
                online_sampling = True
                # Time limit for the episodes
                max_episode_length = N_BITS

                # Initialize the model
                model = model_class(
                    "MultiInputPolicy",
                    env,
                    replay_buffer_class=HerReplayBuffer,
                    # Parameters for HER
                    replay_buffer_kwargs=dict(
                        n_sampled_goal=4,
                        goal_selection_strategy=goal_selection_strategy,
                        online_sampling=online_sampling,
                        max_episode_length=max_episode_length,
                    ),
                    verbose=1,
                )

    model.learn(total_timesteps=int(5e4),
                tb_log_name=args.simulation_name, callback=best_model)


if __name__ == '__main__':
    main()
    sys.exit(0)
