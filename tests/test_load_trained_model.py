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

    parser = argparse.ArgumentParser(
        description='Loads previous trained model and replay buffer. \
            Then it starts the simulation using the parameters provided.')
    parser.add_argument('-d', '--docker-image', type=str, default='contiker/contiki-ng',
                        help="Name of the docker image ('contiker/contiki-ng')")
    parser.add_argument('-dc', '--docker-command', type=str, default='/bin/sh -c "cd examples/benchmarks/rl-sdwsn && ./run-cooja.py"',
                        help="Simulation script to run inside the container")
    parser.add_argument('-dmt', '--docker-mount-target', type=str, default='/home/user/contiki-ng',
                        help="Docker mount target")
    parser.add_argument('-dms', '--docker-mount-source', type=str, default='/Users/fernando/contiki-ng',
                        help="Docker mount source")
    parser.add_argument('-c', '--cooja', type=str, default='127.0.0.1',
                        help='Cooja host address')
    parser.add_argument('-p', '--cooja-port', type=int, default=60001,
                        help='Cooja socket port')
    parser.add_argument('-dbn', '--db-name', type=str, default='mySDN',
                        help='Give a name to your DB')
    parser.add_argument('-db', '--db', type=str, default='127.0.0.1',
                        help='Database address')
    parser.add_argument('-dbp', '--db-port', type=int, default=27017,
                        help='Database port')
    parser.add_argument('-ms', '--simulation-name', type=str, default='continued_learning',
                        help='Name of your simulation')
    parser.add_argument('-w', '--processing-window', type=int, default=200,
                        help='Set the window for processing the reward')
    parser.add_argument('-mtc', '--maximum-tsch-channels', type=int, default=3,
                        help='Maximum TSCH channel offsets')
    parser.add_argument('-mfs', '--maximum-slotframe-size', type=int, default=500,
                        help='Maximum TSCH slotframe size')
    parser.add_argument('model', type=str,
                        help='Path to the trained model to load')

    args = parser.parse_args()

    print(args)

    mount = {
        'target': args.docker_mount_target,
        'source': args.docker_mount_source,
        'type': 'bind'
    }

    container_ports = {
        'container': args.cooja_port,
        'host': args.cooja_port
    }

    container_controller = ContainerController(
        image=args.docker_image,
        command=args.docker_command,
        mount=mount,
        container_ports=container_ports,
        cooja_host=args.cooja,
        cooja_port=args.cooja_port,
        db_name=args.db_name,
        db_host=args.db,
        db_port=args.db_port,
        simulation_name=args.simulation_name,
        processing_window=args.processing_window,
        max_channel_offsets=args.maximum_tsch_channels,
        max_slotframe_size=args.maximum_slotframe_size)

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
    env = TimeLimitWrapper(env, max_steps=80)

    # Callback to save the model and replay buffer every N steps.
    save_model_replay = SaveModelSaveBuffer(
        save_path='./logs/', name_prefix='continue_learning')
    event_callback = EveryNTimesteps(n_steps=50, callback=save_model_replay)

    # the saved model does not contain the replay buffer
    loaded_model = DQN.load(args.model, env=env, print_system_info=True)
    print(f"The loaded_model has {loaded_model.replay_buffer.size()} transitions in its buffer")

    # show the save hyperparameter
    print("loaded:", "gamma =", loaded_model.gamma)

    # load buffer into the loaded_model
    buffer_name = args.model+"_buffer.pkl"
    print(f'buffer name: {buffer_name}')
    loaded_model.load_replay_buffer(buffer_name)

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
