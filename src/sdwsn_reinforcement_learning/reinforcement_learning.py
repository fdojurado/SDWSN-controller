import sys
from time import sleep
from sdwsn_controller.controller import Controller
from sdwsn_reinforcement_learning.env import Env


class ReinforcementLearning(Controller):
    def __init__(self, serial_interface, network_reconfiguration, database, packet_dissector,
                 env=None, model=None, processing_window=100) -> None:
        super().__init__(serial_interface, network_reconfiguration, database, packet_dissector)
        self.env = env
        self.model = model
        self.processing_window = processing_window
        print('Number of states: {}'.format(self.env.observation_space))
        print('Number of actions: {}'.format(self.env.action_space))

    def exec(self):
        # Initialize the serial
        # if not self.serial_start():
        #     sys.exit(1)

        # # Wait until network has stabilized
        # while(1):
        #     if self.packet_dissector.sequence > self.processing_window:
        #         print('time to run the RL algorithm')
        #         break
        #     sleep(0.1)

         # Train the agent
        self.model.learn(total_timesteps=int(1e6))

        pass
