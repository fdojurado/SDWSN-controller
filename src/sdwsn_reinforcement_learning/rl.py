import sys
from time import sleep
from abc import ABC, abstractmethod
from sdwsn_controller.controller import Controller
from sdwsn_reinforcement_learning.env import Env
from stable_baselines3 import DQN


class BaseReinforcementLearning(ABC):
    @abstractmethod
    def __init__(
        self,
        **kwargs: object
    ):
        pass
