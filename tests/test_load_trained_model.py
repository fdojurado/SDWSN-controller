import sys
import argparse


from sdwsn_reinforcement_learning.env import Env
from sdwsn_reinforcement_learning.wrappers import TimeLimitWrapper, SaveModelSaveBuffer
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EveryNTimesteps
from sdwsn_controller.controller import ContainerController
import signal
from stable_baselines3.common.vec_env import DummyVecEnv


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
    parser.add_argument('-m', '--model', type=str, default=100,
                        help='Path to the trained model to load')

    args = parser.parse_args()

    print(args)

    container_controller = ContainerController(
        cooja_host=args.socket, cooja_port=args.port,
        max_channel_offsets=args.tschmaxchannel, max_slotframe_size=args.tschmaxslotframe)
    # controller = BaseController(cooja_host=args.socket, cooja_port=args.port)

    def exit_process(signal_number):
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
    env = TimeLimitWrapper(env, max_steps=80)

    # Callback to save the model and replay buffer every N steps.
    save_model_replay = SaveModelSaveBuffer(
        save_path='./logs/', name_prefix='continue_learning')
    event_callback = EveryNTimesteps(n_steps=50, callback=save_model_replay)

    # the saved model does not contain the replay buffer
    loaded_model = DQN.load(args.model, env=env, print_system_info=True)
    print(f"The loaded_model has {loaded_model.replay_buffer.size()} transitions in its buffer")

    # show the save hyperparameters
    print("loaded:", "gamma =", loaded_model.gamma)

    # load it into the loaded_model
    loaded_model.load_replay_buffer("logs/rl_model_buffer_300_steps.pkl")

    # now the loaded replay is not empty anymore
    print(f"The loaded_model has {loaded_model.replay_buffer.size()} transitions in its buffer")

    # as the environment is not serializable, we need to set a new instance of the environment
    loaded_model.set_env(env)

    # and continue training
    loaded_model.learn(total_timesteps=int(400),
                       log_interval=2, callback=event_callback)


if __name__ == '__main__':
    main()
    sys.exit(0)
