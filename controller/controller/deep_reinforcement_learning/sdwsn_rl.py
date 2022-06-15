from time import sleep
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.callbacks import BaseCallback
import multiprocessing as mp
from controller.deep_reinforcement_learning.sdwsn_env import sdwsnEnv
from controller.serial.serial_packet_dissector import *
import networkx as nx
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.evaluation import evaluate_policy
import gym

# env = sdwsnEnv(10, 3, [10,17,31], None)
# check_env(env, warn=True)


class TimeLimitWrapper(gym.Wrapper):
    """
    :param env: (gym.Env) Gym environment that will be wrapped
    :param max_steps: (int) Max number of steps per episode
    """

    def __init__(self, env, max_steps=100):
        # Call the parent constructor, so we can access self.env later
        super(TimeLimitWrapper, self).__init__(env)
        self.max_steps = max_steps
        # Counter of steps per episode
        self.current_step = 0

    def reset(self):
        """
        Reset the environment 
        """
        # Reset the counter
        self.current_step = 0
        return self.env.reset()

    def step(self, action):
        """
        :param action: ([float] or int) Action taken by the agent
        :return: (np.ndarray, float, bool, dict) observation, reward, is the episode over?, additional information
        """
        self.current_step += 1
        obs, reward, done, info = self.env.step(action)
        # Overwrite the done signal when
        if self.current_step >= self.max_steps:
            done = True
            # Update the info dict to signal that the limit was exceeded
            info['time_limit_reached'] = True
        return obs, reward, done, info


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
    def __init__(self, config, verbose, input_queue, output_queue,
                 nc_job_queue, nc_job_completion, sequence_number, type_exec):
        mp.Process.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.nc_job_queue = nc_job_queue
        self.nc_job_completion = nc_job_completion
        self.sequence_number = sequence_number
        self.verbose = verbose
        self.first_time_run = 0
        self.max_channel_offsets = config.tsch.num_of_channels
        self.max_slotframe_size = 100
        self.type_exec = type_exec

    def load_env(self):
        self.first_time_run = 1
        print("loading saved model")
        # self.model = DQN.load("./logs/rl_energy_300_steps")
        self.model = DQN.load("./logs/continue/2/rl_energy_260_steps")
        N = get_last_index_wsn()+1
        self.env = sdwsnEnv(N, self.max_channel_offsets,
                            self.max_slotframe_size, self.nc_job_queue, self.input_queue, self.nc_job_completion, self.sequence_number)
        print('Number of states: {}'.format(self.env.observation_space))
        print('Number of actions: {}'.format(self.env.action_space))
        # Create the callback: check every 1000 steps
        # Save a checkpoint every 1000 steps
        self.checkpoint_callback = CheckpointCallback(save_freq=20, save_path='./logs/continue/2/',
                                                      name_prefix='rl_energy')
        # Create the callback: check every 1000 steps
        self.callback = MonitorCallback()

    def configure_env(self):
        print("configuring the environment")
        self.first_time_run = 1
        # 13, 17 and 41 are coprime with the other slotframes
        # Get last index of sensor
        N = get_last_index_wsn()+1
        self.env = sdwsnEnv(N, self.max_channel_offsets,
                            self.max_slotframe_size, self.nc_job_queue, self.input_queue, self.nc_job_completion, self.sequence_number)

        self.env = TimeLimitWrapper(self.env, max_steps=4)
        print('Number of states: {}'.format(self.env.observation_space))
        print('Number of actions: {}'.format(self.env.action_space))
        self.model = DQN('MlpPolicy', self.env, verbose=1)
        # Save a checkpoint every 1000 steps
        # self.checkpoint_callback = CheckpointCallback(save_freq=20, save_path='./logs/',
        #                                               name_prefix='rl_energy')
        # Create the callback: check every 1000 steps
        # self.callback = MonitorCallback()

    def run(self):
        while(1):
            # look for incoming jobs
            if not self.input_queue.empty():
                self.input_queue.get()
                print("time to compute reward RL")
                if self.first_time_run == 0:
                    if self.type_exec == 'train':
                        self.configure_env()
                        # Train the agent
                        self.model.learn(total_timesteps=int(
                            500))
                    if self.type_exec == 'eval':
                        # Loading saved model
                        self.load_env()
                        # Evaluate the trained model
                        mean_reward, std_reward = evaluate_policy(
                            self.model, self.env, n_eval_episodes=1, deterministic=True)
                        # sleep(0.1)
                        print(f'reward: {mean_reward}, std reward: {std_reward}')
                    if self.type_exec == 'continue':
                        # Loading saved model
                        self.load_env()
                        self.model.set_env(self.env)
                        # print("n_steps =", self.model.n_steps)
                        # Train the agent
                        self.model.learn(total_timesteps=int(
                            500), callback=[self.callback, self.checkpoint_callback])
