import sys
from time import sleep
import gym
from typing import Type
from sdwsn_controller.controller import Controller
from sdwsn_reinforcement_learning.env import Env
from stable_baselines3 import DQN
from sdwsn_reinforcement_learning.rl import BaseReinforcementLearning
from stable_baselines3.common.type_aliases import MaybeCallback
from stable_baselines3 import DQN


class BaseDQN(DQN):
    def __init__(
        self,
        env: Type[gym.Env],
        verbose: int = 0,
    ):
        self.env = env
        self.verbose = verbose
        # def __init__(self, env=None, callback=None, processing_window=100) -> None:
        #     self.env = env
        #     self.processing_window = processing_window
        #     self.callback = callback
        #     print('Number of states: {}'.format(self.env.observation_space))
        #     print('Number of actions: {}'.format(self.env.action_space))

    def learn(
        self,
        callback: MaybeCallback = None,
    ):
        # Train the agent
        self.model.learn(total_timesteps=int(1e6), callback=self.callback)

    def continue_learning(self, saved_model, saved_buffer, env):
        # Here, we load previous save model and buffer to continuo learning
        self.model = DQN.load(saved_model)
        print("model")
        print(self.model)
        print(f"The loaded_model has {self.model.replay_buffer.size()} transitions in its buffer")
        print(f'buffer path {saved_buffer}')
        self.model.load_replay_buffer(saved_buffer)
        print(f"The loaded_model has {self.model.replay_buffer.size()} transitions in its buffer")
        # Retrieve the environment
        # self.env = self.model.get_env()
        self.model.env = self.env
        print(self.env)
        self.exec()
