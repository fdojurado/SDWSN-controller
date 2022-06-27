import sys
import argparse
import gym
import os

from stable_baselines3.common.monitor import Monitor
from sdwsn_reinforcement_learning.env import Env
from sdwsn_reinforcement_learning.wrappers import SaveModelSaveBuffer
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EveryNTimesteps
from sdwsn_controller.controller import ContainerController
from stable_baselines3.common.logger import configure
import signal


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', type=str, default='127.0.0.1',
                        help='socket address')
    parser.add_argument('-p', '--port', type=int, default=60001,
                        help='socket port')
    parser.add_argument('-db', '--db', type=str, default='127.0.0.1',
                        help='Database address')
    parser.add_argument('-dbp', '--dbPort', type=int, default=27017,
                        help='Database port')
    parser.add_argument('-tmc', '--tschmaxchannel', type=int, default=3,
                        help='Maximum TSCH channel offset')
    parser.add_argument('-tsfs', '--tschmaxslotframe', type=int, default=100,
                        help='Maximum TSCH slotframe size')

    args = parser.parse_args()

    print(args)

    # Monitor the environment
    log_dir = "./monitor/"
    os.makedirs(log_dir, exist_ok=True)

    container_controller = ContainerController(
        cooja_host=args.socket, cooja_port=args.port,
        max_channel_offsets=args.tschmaxchannel, max_slotframe_size=args.tschmaxslotframe,
        log_dir=log_dir)
    # controller = BaseController(cooja_host=args.socket, cooja_port=args.port)

    def exit_process(signal_number, frames):
        # pylint: disable=no-member
        print('Received %s signal. Exiting...',
              signal.Signals(signal_number).name)
        container_controller.container_controller_shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, exit_process)
    signal.signal(signal.SIGQUIT, exit_process)
    signal.signal(signal.SIGTERM, exit_process)

    # Create an instance of the environment
    env = Env(container_controller=container_controller)

    # Wrap the environment to limit the max steps per episode
    env = gym.wrappers.TimeLimit(env, max_episode_steps=2)

    env = Monitor(env, log_dir)

    # Callback to save the model and replay buffer every N steps.
    save_model_replay = SaveModelSaveBuffer(save_path='./logs/')
    event_callback = EveryNTimesteps(n_steps=50, callback=save_model_replay)

    # Create an instance of the RL model to use
    model = DQN('MlpPolicy', env, verbose=1, learning_starts=10,
                target_update_interval=8, exploration_fraction=0.1)

    model.learn(total_timesteps=int(50000),
                log_interval=1, callback=event_callback)


if __name__ == '__main__':
    main()
    sys.exit(0)
