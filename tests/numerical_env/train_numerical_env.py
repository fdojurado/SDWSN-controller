# To get the parameters, we used Optuna (rl-stablebaseline3-zoo)
# python3 train.py --algo dqn --env sdwsn-v2 -n 50000 -optimize --n-trials 1000 --n-jobs 2 --sampler tpe --pruner median
# In dqn.yml, we added
# Almost Tuned
# sdwsn-v2:
#   n_timesteps: !!float 5e4
#   policy: 'MlpPolicy'
#   learning_rate: !!float 2.3e-3
#   batch_size: 64
#   buffer_size: 100000
#   learning_starts: 1000
#   gamma: 0.99
#   target_update_interval: 10
#   train_freq: 256
#   gradient_steps: 128
#   exploration_fraction: 0.16
#   exploration_final_eps: 0.04
#   policy_kwargs: "dict(net_arch=[256, 256])"
# In import_envs.py, we added,
# import sys
# sys.path.append('/Users/fernando/SDWSN-controller')
# try:
#     import sdwsn_controller
#     print("sdwsn package imported")
# except ImportError:
#     print("sdwsn package not imported")
#     sdwsn_gym = None
# register(
#         # unique identifier for the env `name-version`
#         id="sdwsn-v2",
#         # path to the class for creating the env
#         # Note: entry_point also accept a class as input (and not only a string)
#         entry_point="sdwsn_controller.reinforcement_learning.env_numerical:Env",
#         # Max number of steps per episode, using a `TimeLimitWrapper`
#         max_episode_steps=50
#     )
#
import sys
import argparse
import gym
from torch import nn as nn
import os
import numpy as np
from sdwsn_controller.controller.rl_numerical_controller import RLNumericalController 

from sdwsn_controller.reinforcement_learning.wrappers import SaveModelSaveBuffer, SaveOnBestTrainingRewardCallback
from stable_baselines3 import DQN, A2C, PPO, HerReplayBuffer, DDPG, DQN, SAC, TD3
from stable_baselines3.common.callbacks import EveryNTimesteps
from gym.envs.registration import register
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.envs import BitFlippingEnv


def main():
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

    # Controller instance
    controller = RLNumericalController(
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

    env_kwargs = {
        'simulation_name': args.simulation_name,
        'controller': controller
    }

    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)

    # Wrap the environment to limit the max steps per episode
    # env = gym.wrappers.TimeLimit(env, max_episode_steps=5)

    env = Monitor(env, monitor_log_dir)

    # Callback to save the model and replay buffer every N steps.
    # save_model_replay = SaveModelSaveBuffer(save_path=args.save_model)
    # event_callback = EveryNTimesteps(n_steps=10000, callback=save_model_replay)
    # Create the callback: check every 1000 steps
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
