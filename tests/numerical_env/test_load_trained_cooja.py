import sys
import argparse
import os
import gym


from stable_baselines3 import DQN
import signal
from stable_baselines3.common.monitor import Monitor
from gym.envs.registration import register


def main():

    parser = argparse.ArgumentParser(
        description='Loads previous trained model and evaluate in Cooja.')
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
    parser.add_argument('model', type=str,
                        help='Path to the trained model to load')

    args = parser.parse_args()

    # Example for the CartPole environment
    register(
        # unique identifier for the env `name-version`
        id="sdwsn-v1",
        # path to the class for creating the env
        # Note: entry_point also accept a class as input (and not only a string)
        entry_point="sdwsn_reinforcement_learning.env:Env",
        # Max number of steps per episode, using a `TimeLimitWrapper`
        max_episode_steps=50
    )

    # Monitor the environment
    log_dir = "./tensorlog/"
    os.makedirs(log_dir, exist_ok=True)

    simulation_command = '/bin/sh -c '+'"cd ' + \
        args.docker_command+' && ./run-cooja.py"'

    env_kwargs = {
        'target': args.docker_mount_target,
        'source': args.docker_mount_source,
        'simulation_command': simulation_command,
        'host': args.cooja,
        'port': args.cooja_port,
        'socket_file': args.docker_mount_source+'/'+args.docker_command+'/'+'COOJA.log',
        'db_name': args.db_name,
        'simulation_name': args.simulation_name,
        'tsch_scheduler': 'Unique Schedule'
    }

    # Create an instance of the environment
    env = gym.make('sdwsn-v1', **env_kwargs)

    env = Monitor(env, log_dir)

    loaded_model = DQN.load(args.model, env=env)

    # Test the trained agent
    for i in range(3):
        obs = env.reset()
        done = False
        while(not done):
            action, _states = loaded_model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            if done:
                print(f"episode done. reward: {reward}")
                env.render()
                obs = env.reset()

    env.close()


if __name__ == '__main__':
    main()
    sys.exit(0)
