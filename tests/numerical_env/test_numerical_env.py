import sys
import argparse
import gym
import os

from sdwsn_reinforcement_learning.wrappers import SaveModelSaveBuffer
from stable_baselines3 import DQN
from stable_baselines3.common.evaluation import evaluate_policy
from gym.envs.registration import register
from stable_baselines3.common.monitor import Monitor


def main():
    parser = argparse.ArgumentParser(
        description='Loads previous trained model and evaluate it.')

    parser.add_argument('model', type=str,
                        help='Path to the trained model to load')

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

    # Create an instance of the environment
    env = gym.make('sdwsn-v2')

    env = Monitor(env, log_dir)

    loaded_model = DQN.load(args.model, env=env)

    # # Evaluate the trained agent
    # mean_reward, std_reward = evaluate_policy(
    #     loaded_model, env, n_eval_episodes=1, deterministic=True, render=True)

    # print(f"after training mean_reward={mean_reward:.2f} +/- {std_reward}")

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
                obs = env.reset()

    env.close()


if __name__ == '__main__':
    main()
    sys.exit(0)
