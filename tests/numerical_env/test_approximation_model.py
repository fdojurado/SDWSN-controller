import sys
import argparse
import gym
import os
import numpy as np

from sdwsn_controller.reinforcement_learning.wrappers import SaveModelSaveBuffer
from sdwsn_controller.controller.env_numerical_controller import EnvNumericalController
from stable_baselines3 import DQN
from stable_baselines3.common.evaluation import evaluate_policy
from gym.envs.registration import register
from stable_baselines3.common.monitor import Monitor

MAX_SLOTFRAME_SIZE = 70

def main():
    parser = argparse.ArgumentParser(
        description='Loads previous trained model and evaluate it.')

    parser.add_argument('-dbn', '--db-name', type=str, default='mySDN',
                        help='Give a name to your DB')
    parser.add_argument('-dbp', '--db-port', type=int, default=27017,
                        help='Database port')
    parser.add_argument('-db', '--db-host', type=str, default='127.0.0.1',
                        help='Database host address')
    parser.add_argument('-ms', '--simulation-name', type=str, default='training',
                        help='Name of your simulation')
    parser.add_argument('-t', '--monitor-log', type=str, default='./tensorlog/',
                        help='Path to log monitor data')
    parser.add_argument('-fp', '--output-path', type=str, default='./output/',
                        help='Path to save results')
    parser.add_argument('-m', '--model', type=str,
                        help='Path to the trained model to load')

    args = parser.parse_args()

    # Example for the CartPole environment
    register(
        # unique identifier for the env `name-version`
        id="sdwsn-v1",
        # path to the class for creating the env
        # Note: entry_point also accept a class as input (and not only a string)
        entry_point="sdwsn_controller.reinforcement_learning.env:Env",
        # Max number of steps per episode, using a `TimeLimitWrapper`
        # max_episode_steps=50
    )

    # Create output folder
    log_dir = args.output_path
    os.makedirs(log_dir, exist_ok=True)

    # Monitor the environment
    log_dir = args.monitor_log
    os.makedirs(log_dir, exist_ok=True)

    # Controller instance
    controller = EnvNumericalController(
        db_name=args.db_name,
        db_host=args.db_host,
        db_port=args.db_port,
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
        'folder': args.output_path,
        'controller': controller
    }

    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)

    env = Monitor(env, log_dir)

    env.reset()
    # Get last observations including the SF size
    _, _, _, last_ts_in_schedule, current_sf_len = controller.get_state()
    # Current SF size
    sf_size = current_sf_len
    last_ts_in_schedule = last_ts_in_schedule
    controller.user_requirements = (0.4, 0.3, 0.3)
    increase = 1
    for i in range(200):
        # action, _state = model.predict(obs, deterministic=True)
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
                # done = True
                # obs = env.reset()

        obs, reward, done, info = env.step(action)
        print(f'Observations: {obs}, reward: {reward}, done: {done}, info: {info}')
        # Get last observations including the SF size
        _, _, _, last_ts_in_schedule, current_sf_len = controller.get_state()
        # Current SF size
        sf_size = current_sf_len
        print(f'current SF size: {sf_size}')

    env.render()


if __name__ == '__main__':
    main()
    sys.exit(0)
