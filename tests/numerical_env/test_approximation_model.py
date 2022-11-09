import argparse

from gym.envs.registration import register
import gym

import logging

import numpy as np

import os

from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.controller.numerical_controller import NumericalController, NumericalRewardProcessing

from signal import signal, SIGINT

from stable_baselines3.common.monitor import Monitor

import sys

MAX_SLOTFRAME_SIZE = 70

logger = logging.getLogger('main.'+__name__)


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

    # -------------------- setup controller --------------------
    # Reward processor
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
            [-2.76382789e-04,  9.64746733e-01]
            # [-2.76382789e-04,  -0.8609615946299346738365592202098]
        )
    )

    # Database
    db = DatabaseManager(
        name=args.db_name,
        host=args.db_host,
        port=args.db_port
    )

    # Controller instance
    controller = NumericalController(
        db=db,
        reward_processing=reward_processing
    )

    env_kwargs = {
        'simulation_name': args.simulation_name,
        'folder': args.output_path,
        'controller': controller
    }

    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)

    env = Monitor(env, log_dir)

    # Exit signal
    def handler(*args):
        # Handle any cleanup here
        logger.warning('SIGINT or CTRL-C detected. Shutting down ...')
        controller.stop()
        sys.exit(0)

    signal(SIGINT, handler)

    env.reset()
    # Get last observations including the SF size
    observations = controller.get_state()
    # Current SF size
    sf_size = observations['current_sf_len']
    last_ts_in_schedule = observations['last_ts_in_schedule']
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

        env.step(action)
        # Get last observations including the SF size
        observations = controller.get_state()
        # Current SF size
        sf_size = observations['current_sf_len']

    env.render()

    return


if __name__ == '__main__':
    main()
    sys.exit(0)
