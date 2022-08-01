import sys
import argparse
import gym
import os

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
    parser.add_argument('-db', '--db', type=str, default='127.0.0.1',
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
        id="sdwsn-v2",
        # path to the class for creating the env
        # Note: entry_point also accept a class as input (and not only a string)
        entry_point="sdwsn_reinforcement_learning.env_numerical:Env",
        # Max number of steps per episode, using a `TimeLimitWrapper`
        max_episode_steps=50
    )

    # Tensorboard the environment
    tensor_log_dir = args.tensorboard
    os.makedirs(tensor_log_dir, exist_ok=True)

    # Monitor the environment
    monitor_log_dir = args.save_model
    os.makedirs(monitor_log_dir, exist_ok=True)

    env_kwargs = {
        'db_name': args.db_name,
        'db_host': args.db,
        'db_port': args.db_port,
        'simulation_name': args.simulation_name
    }

    # Create an instance of the environment
    env = gym.make('sdwsn-v2', **env_kwargs)

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
    model = DQN('MlpPolicy', env, verbose=1, gamma=0.98, learning_rate=5.832985636420814e-05, batch_size=256,
                buffer_size=1000000, exploration_final_eps=0.06038208749247105, exploration_fraction=0.45629838266368317, target_update_interval=20000,
                learning_starts=5000, train_freq=1000, subsample_steps=1, net_arch='medium',
                tensorboard_log=tensor_log_dir, exploration_fraction=0.1)

    model.learn(total_timesteps=int(1e6),
                tb_log_name=args.simulation_name, callback=best_model)


if __name__ == '__main__':
    main()
    sys.exit(0)
