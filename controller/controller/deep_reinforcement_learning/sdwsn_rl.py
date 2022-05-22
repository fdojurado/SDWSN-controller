from time import sleep
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.callbacks import BaseCallback
import multiprocessing as mp
from controller.deep_reinforcement_learning.sdwsn_env import sdwsnEnv
from controller.serial.serial_packet_dissector import *
import networkx as nx
from stable_baselines3 import DQN

# env = sdwsnEnv(10, 3, [10,17,31], None)
# check_env(env, warn=True)


class MonitorCallback(BaseCallback):
    """
    A custom callback that derives from ``BaseCallback``.

    :param verbose: (int) Verbosity level 0: not output 1: info 2: debug
    """

    def __init__(self, verbose=0):
        super(MonitorCallback, self).__init__(verbose)
        # Those variables will be accessible in the callback
        # (they are defined in the base class)
        # The RL model
        # self.model = None  # type: BaseAlgorithm
        # An alias for self.model.get_env(), the environment used for training
        # self.training_env = None  # type: Union[gym.Env, VecEnv, None]
        # Number of time the callback was called
        # self.n_calls = 0  # type: int
        # self.num_timesteps = 0  # type: int
        # local and global variables
        # self.locals = None  # type: Dict[str, Any]
        # self.globals = None  # type: Dict[str, Any]
        # The logger object, used to report things in the terminal
        # self.logger = None  # stable_baselines3.common.logger
        # # Sometimes, for event callback, it is useful
        # # to have access to the parent object
        # self.parent = None  # type: Optional[BaseCallback]

    def _on_training_start(self) -> None:
        """
        This method is called before the first rollout starts.
        """
        print("training has started")
        pass

    def _on_rollout_start(self) -> None:
        """
        A rollout is the collection of environment interaction
        using the current policy.
        This event is triggered before collecting new samples.
        """
        print("rollout started")
        pass

    def _on_step(self) -> bool:
        """
        This method will be called by the model after each call to `env.step()`.

        For child callback (of an `EventCallback`), this will be called
        when the event is triggered.

        :return: (bool) If the callback returns False, training is aborted early.
        """
        print("_on_step")
        return True

    def _on_rollout_end(self) -> None:
        """
        This event is triggered before updating the policy.
        """
        print("_on_rollout_end")
        pass

    def _on_training_end(self) -> None:
        """
        This event is triggered before exiting the `learn()` method.
        """
        pass


class SDWSN_RL(mp.Process):
    def __init__(self, config, verbose, input_queue, output_queue, nc_job_queue, nc_job_completion):
        mp.Process.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.nc_job_queue = nc_job_queue
        self.nc_job_completion = nc_job_completion
        self.verbose = verbose
        self.first_time_run = 0
        self.max_channel_offsets = config.tsch.num_of_channels
        self.max_slotframe_size = 100

    def configure_env(self):
        print("configuring the environment")
        self.first_time_run = 1
        # 13, 17 and 41 are coprime with the other slotframes
        # Get last index of sensor
        N = get_last_index_wsn()+1
        self.env = sdwsnEnv(N, self.max_channel_offsets,
                            self.max_slotframe_size, self.nc_job_queue, self.input_queue, self.nc_job_completion)
        print('Number of states: {}'.format(self.env.observation_space))
        print('Number of actions: {}'.format(self.env.action_space))
        self.model = DQN('MlpPolicy', self.env, verbose=2)
        # Create the callback: check every 1000 steps
        self.callback = MonitorCallback()

    def run(self):
        while(1):
            # look for incoming jobs
            if not self.input_queue.empty():
                self.input_queue.get()
                print("time to compute reward RL")
                if self.first_time_run == 0:
                    self.configure_env()
                    # Train the agent
                    self.model.learn(total_timesteps=int(
                        2), callback=self.callback)
            # sleep(0.1)
