import sys
from time import sleep
from sdwsn_controller.controller import Controller
from sdwsn_reinforcement_learning.env import Env


class ReinforcementLearning(Controller):
    def __init__(self, serial_interface, network_reconfiguration, database, packet_dissector,
                 env=None, model=None, callback=None, processing_window=100) -> None:
        super().__init__(serial_interface, network_reconfiguration, database, packet_dissector)
        self.env = env
        self.model = model
        self.processing_window = processing_window
        self.callback = callback
        print('Number of states: {}'.format(self.env.observation_space))
        print('Number of actions: {}'.format(self.env.action_space))

    def exec(self):
        # Train the agent
        self.model.learn(total_timesteps=int(1e6), callback=self.callback)
