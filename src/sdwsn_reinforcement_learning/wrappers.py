from numpy import save
import gym
import os
from stable_baselines3.common.callbacks import BaseCallback


class SaveModelSaveBuffer(BaseCallback):
    def __init__(self, save_path: str, name_prefix: str = "rl_model", verbose: int = 0):
        super().__init__(verbose)
        self.save_path = save_path
        self.name_prefix = name_prefix

    def _init_callback(self) -> None:
        # Create folder if needed
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        path = os.path.join(self.save_path, f"{self.name_prefix}_{self.num_timesteps}_steps")
        self.model.save(path)
        print(f"Saving model checkpoint to {path}")
        # now save the replay buffer too
        path = os.path.join(self.save_path, f"{self.name_prefix}_{self.num_timesteps}_steps_buffer")
        self.model.save_replay_buffer(path)
        print(f"Saving replay buffer checkpoint to {path}")


class TimeLimitWrapper(gym.Wrapper):
    """
    :param env: (gym.Env) Gym environment that will be wrapped
    :param max_steps: (int) Max number of steps per episode
    """

    def __init__(self, env, max_steps=100):
        # Call the parent constructor, so we can access self.env later
        super(TimeLimitWrapper, self).__init__(env)
        self.max_steps = max_steps
        self.env = env
        # self.container = container
        # self.name = name
        # Counter of steps per episode
        self.current_step = 0
        # Number of episodes
        self.num_episodes = 0

    def reset(self):
        """
        Reset the environment 
        """
        self.num_episodes += 1
        # Stop the serial reading thread
        # self.env.stop_serial()
        print('Episode ended, restarting the container application')
        # # Stop the container
        # self.container.shutdown()
        # # Shutdown the socket
        # self.env.stop_serial()
        # Reset the counter
        self.current_step = 0
        # # Run the analysis script
        # if self.db.DATABASE is not None:
        #     run_analysis(self.db, self.name+str(self.num_episodes))
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
