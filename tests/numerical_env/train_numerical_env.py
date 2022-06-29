import sys
import argparse
import gym
import os

from sdwsn_reinforcement_learning.wrappers import SaveModelSaveBuffer
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EveryNTimesteps
from gym.envs.registration import register
# import signal


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

    # Monitor the environment
    log_dir = "./tensorlog/"
    os.makedirs(log_dir, exist_ok=True)

    env_kwargs = {
        'db_name': args.db,
        'db_host': args.db_host,
        'db_port': args.db_port,
        'simulation_name': args.simulation_name
    }

    # Create an instance of the environment
    env = gym.make('sdwsn-v2', **env_kwargs)

    # Wrap the environment to limit the max steps per episode
    # env = gym.wrappers.TimeLimit(env, max_episode_steps=5)

    # env = Monitor(env, log_dir)

    # Callback to save the model and replay buffer every N steps.
    save_model_replay = SaveModelSaveBuffer(save_path='./logs/')
    event_callback = EveryNTimesteps(n_steps=10000, callback=save_model_replay)

    # Create an instance of the RL model to use
    model = DQN('MlpPolicy', env, verbose=1, batch_size=256,
                tensorboard_log=log_dir, exploration_fraction=0.1)

    model.learn(total_timesteps=int(1e6), callback=event_callback)


if __name__ == '__main__':
    main()
    sys.exit(0)
