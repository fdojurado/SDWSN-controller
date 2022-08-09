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
import os
import numpy as np
from sdwsn_controller.controller.env_numerical_controller import EnvNumericalController

from sdwsn_controller.reinforcement_learning.wrappers import SaveModelSaveBuffer, SaveOnBestTrainingRewardCallback
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EveryNTimesteps
from gym.envs.registration import register
from stable_baselines3.common.monitor import Monitor


def main():
    parser = argparse.ArgumentParser(
        description='This trains the numerical environment based on the polynomial \
        coefficients found for the hard coded schedule.')
    parser.add_argument('-dbn', '--db-name', type=str, default='mySDN',
                        help='Give a name to your DB')
    parser.add_argument('-dbp', '--db-port', type=int, default=27017,
                        help='Database port')
    parser.add_argument('-db', '--db-host', type=str, default='127.0.0.1',
                        help='Database host address')
    parser.add_argument('-ms', '--simulation-name', type=str, default='training',
                        help='Name of your simulation')
    parser.add_argument('-t', '--tensorboard', type=str, default='./tensorlog/',
                        help='Path to log TensorBoard logging')
    parser.add_argument('-svm', '--save-model', type=str, default='./logs/',
                        help='Path to save the trained model')

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
    controller = EnvNumericalController(
        db_name=args.db_name,
        db_host=args.db_host,
        db_port=args.db_port,
        power_weights=np.array(
            [3.72158335e-08, -5.52679120e-06,
                3.06757888e-04, -7.85850498e-03, 9.50518299e-01]
        ),
        delay_weights=np.array(
             [3.17334712e-07, -2.40848429e-05,  1.27791635e-03, -4.89649727e-03]
        ),
        pdr_weights=np.array(
            [-5.85240204e-04,  9.65952384e-01]
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
    model = DQN('MlpPolicy', env, verbose=1, batch_size=256,
                tensorboard_log=tensor_log_dir, exploration_fraction=0.6)

    model.learn(total_timesteps=int(1e6),
                tb_log_name=args.simulation_name, callback=best_model)


if __name__ == '__main__':
    main()
    sys.exit(0)
