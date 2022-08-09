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
    parser.add_argument('-fp', '--figures-path', type=str, default='./figures/',
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
        max_episode_steps=50
    )

    # Create figure folder
    log_dir = args.figures_path
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
        'fig_dir': args.figures_path,
        'controller': controller
    }

    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)

    env = Monitor(env, log_dir)

    # model = DQN('MlpPolicy', env, verbose=1, batch_size=256,
    #             exploration_fraction=0.1)

    loaded_model = DQN.load(args.model, env=env)

    # Test the trained agent
    for i in range(10):
        obs = env.reset()
        done = False
        while(not done):
            action, _states = loaded_model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            if done:
                print(f"episode done. reward: {reward}")
                env.render()

    env.close()


if __name__ == '__main__':
    main()
    sys.exit(0)
