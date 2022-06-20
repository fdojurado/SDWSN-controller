from time import sleep
from sdwsn_reinforcement_learning.env import Env
import multiprocessing as mp


class ReinforcementLearning(mp.Process):
    def __init__(self, controller_input=mp.Queue(), controller_output=mp.Queue(), env=Env(), model=None, processing_window=100) -> None:
        mp.Process.__init__(self)
        self.env = env
        self.model = model
        self.processing_window = processing_window
        self.controller_input = controller_input
        self.controller_output = controller_output
        print('Number of states: {}'.format(self.env.observation_space))
        print('Number of actions: {}'.format(self.env.action_space))

    def run(self):
        while(1):
            if self.packet_dissector.sequence > self.processing_window:
                print('time to run the RL algorithm')
            sleep(0.1)

        pass
