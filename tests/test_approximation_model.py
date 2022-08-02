# This test obtains the chart for the approximation model in Cooja (Docker).
import sys
from sdwsn_controller.controller.controller import ContainerController
from sdwsn_controller.tsch.hard_coded_schedule import HardCodedScheduler
import gym
import os
import argparse
from gym.envs.registration import register
import sdwsn_controller


def main():

    parser = argparse.ArgumentParser(
        description='It trains DQN using the given, or default parameters.')
    parser.add_argument('-d', '--docker-image', type=str, default='contiker/contiki-ng',
                        help="Name of the docker image ('contiker/contiki-ng')")
    parser.add_argument('-dc', '--docker-command', type=str, default='examples/benchmarks/rl-sdwsn',
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
    parser.add_argument('-ms', '--simulation-name', type=str, default='training',
                        help='Name of your simulation')
    parser.add_argument('-w', '--processing-window', type=int, default=200,
                        help='Set the window for processing the reward')
    parser.add_argument('-mtc', '--maximum-tsch-channels', type=int, default=3,
                        help='Maximum TSCH channel offsets')
    parser.add_argument('-mfs', '--maximum-slotframe-size', type=int, default=500,
                        help='Maximum TSCH slotframe size')
    parser.add_argument('-te', '--maximum-timesteps-episode', type=int, default=50,
                        help='Maximum timesteps per episode')
    parser.add_argument('-fp', '--figures-path', type=str, default='./figures/',
                        help='Path to save results')

    args = parser.parse_args()

    # Example for the CartPole environment
    register(
        # unique identifier for the env `name-version`
        id="sdwsn-v1",
        # path to the class for creating the env
        # Note: entry_point also accept a class as input (and not only a string)
        entry_point="sdwsn_controller.reinforcement_learning.env:Env",
        # Max number of steps per episode, using a `TimeLimitWrapper`
        # max_episode_steps=50
    )

    # Create figure folder
    log_dir = args.figures_path
    os.makedirs(log_dir, exist_ok=True)

    simulation_command = '/bin/sh -c '+'"cd ' + \
        args.docker_command+' && ./run-cooja.py"'

    tsch_scheduler = HardCodedScheduler(
        sf_size=args.maximum_slotframe_size, channel_offsets=args.maximum_tsch_channels)

    controller = ContainerController(
        image=args.docker_image,
        command=simulation_command,
        target=args.docker_mount_target,
        source=args.docker_mount_source,
        socket_file=args.docker_mount_source+'/'+args.docker_command+'/'+'COOJA.log',
        db_name=args.db_name,
        tsch_scheduler=tsch_scheduler
    )

    env_kwargs = {
        'simulation_name': args.simulation_name,
        'controller': controller,
        'fig_dir': args.figures_path
    }
    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)

    obs = env.reset()
    # Get last observations including the SF size
    observations = controller.get_last_observations()
    # Current SF size
    sf_size = observations[4]
    last_ts_in_schedule = observations[3]
    increase = 1
    for i in range(5):
        # action, _state = model.predict(obs, deterministic=True)
        if increase:
            if sf_size < 50 - 1:
                action = 0
            else:
                increase = 0
        else:
            if sf_size > last_ts_in_schedule + 1:
                action = 1
            else:
                increase = 1
                # done = True
                # obs = env.reset()

        obs, reward, done, info = env.step(action)
        print(f'Observations: {obs}, reward: {reward}, done: {done}, info: {info}')
        # Get last observations including the SF size
        observations = controller.get_last_observations()
        # Current SF size
        sf_size = observations[4]
        print(f'current SF size: {sf_size}')

    env.render()


if __name__ == '__main__':
    main()
    sys.exit(0)
