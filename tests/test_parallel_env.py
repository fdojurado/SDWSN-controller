from ast import arguments
import sys
import argparse
import os
import gym
import shutil
from typing import Optional, Dict, Any
import stat
from distutils.dir_util import copy_tree


from sdwsn_reinforcement_learning.env import Env
from sdwsn_reinforcement_learning.wrappers import TimeLimitWrapper, SaveModelSaveBuffer
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EveryNTimesteps
from sdwsn_controller.controller import ContainerController
import signal
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.utils import set_random_seed
from gym.envs.registration import register


def replace_line(file, replace, replacement):
    print(f"replacing {replace} in file: {file} to {replacement}")
    with open(file, "r") as f:
        newline = []
        for word in f.readlines():
            # Replace the keyword while you copy.
            newline.append(word.replace(replace, replacement))

    with open(file, "w") as f:
        for line in newline:
            f.writelines(line)


def generate_cooja_environments(simulation_path, contiki_path, num_env=1):
    print(f'generating env for {simulation_path},{contiki_path},{num_env}')
    environments = []
    simulation_commands = []
    simulation_commands.append(simulation_path)
    cooja_csc_file = contiki_path+'/'+simulation_path+'/cooja.csc'
    cooja_logger_file = contiki_path+'/'+simulation_path+'/coojalogger.js'
    cooja_run_file = contiki_path+'/'+simulation_path+'/run-cooja.py'
    cooja_running_file = contiki_path+'/'+simulation_path+'/COOJA.log'
    print(f'cooja csc file: {cooja_csc_file}')
    # Create num_env-1 copies of the simulation example (path)
    for i in range(1, num_env+1):
        # Increase port number
        port = 60000+i
        name = simulation_path
        db_name = 'mySDN'+str(i)
        simulation_name = 'mySimulation'+str(i)
        simulation_commands.append(name)
        # Lets make the dir in the given path
        dir = contiki_path+'/'+name+'/'
        print(f'dir: {dir}')
        os.makedirs(dir, exist_ok=True)
        # Copy contiki to the new folder
        print("copying to folder")
        new_contiki_path = contiki_path+str(i)
        print(new_contiki_path)
        new_dir = new_contiki_path+'/'+name+'/'
        copy_tree(contiki_path, new_contiki_path)
        # st = os.stat(new_dir+'run-cooja.py')
        # os.chmod(new_dir+'run-cooja.py', st.st_mode | stat.S_IEXEC)
        # Change the port in the csc file
        replacement = '<port>'+str(port)+'</port>'
        replace_line(new_dir+'cooja.csc', "<port>60001</port>", replacement)
        # Simulation command
        simulation_command = '/bin/sh -c '+'"cd '+name+' && ./run-cooja.py"'
        print(f'simulation command: {simulation_command}')
        env_kwargs = {
            'target': '/home/user/contiki-ng',
            'source': new_contiki_path,
            'simulation_command': simulation_command,
            'host': '127.0.0.1',
            'port': port,
            'socket_file': new_dir+'COOJA.log',
            'db_name': db_name,
            'simulation_name': simulation_name
        }
        # env = gym.wrappers.TimeLimit(env, max_episode_steps=50)
        environments.append(env_kwargs)

    return environments


def make_env(env_id, rank, env_kwargs, seed=0):
    """
    Utility function for multiprocessed env.

    :param env_id: (str) the environment ID
    :param seed: (int) the inital seed for RNG
    :param rank: (int) index of the subprocess
    """
    def _init():
        env = gym.make(env_id, **env_kwargs)
        # Important: use a different seed for each environment
        env.seed(seed + rank)
        return env
    set_random_seed(seed)
    return _init


def main():

    parser = argparse.ArgumentParser(
        description='Loads previous trained model and replay buffer. \
            Then it starts the simulation using the parameters provided.')
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
    parser.add_argument('-ms', '--simulation-name', type=str, default='continued_learning',
                        help='Name of your simulation')
    parser.add_argument('-w', '--processing-window', type=int, default=200,
                        help='Set the window for processing the reward')
    parser.add_argument('-mtc', '--maximum-tsch-channels', type=int, default=3,
                        help='Maximum TSCH channel offsets')
    parser.add_argument('-mfs', '--maximum-slotframe-size', type=int, default=500,
                        help='Maximum TSCH slotframe size')
    parser.add_argument('-te', '--maximum-timesteps-episode', type=int, default=50,
                        help='Maximum timesteps per episode')
    # parser.add_argument('model', type=str,
    #                     help='Path to the trained model to load')

    args = parser.parse_args()

    # envs = generate_cooja_environments(
    #     args.docker_command, args.docker_mount_source, 2)

    # print(envs)

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

    # env = make_vec_env("sdwsn-v1", n_envs=4, seed=0)

    # Monitor the environment
    log_dir = "./monitor/"
    os.makedirs(log_dir, exist_ok=True)

    env_kwargs = generate_cooja_environments(
        args.docker_command, args.docker_mount_source, 2)

    print("environment kwargs")
    print(env_kwargs)

    # Callback to save the model and replay buffer every N steps.
    save_model_replay = SaveModelSaveBuffer(save_path='./logs/')
    event_callback = EveryNTimesteps(n_steps=50, callback=save_model_replay)

    # The different number of processes that will be used
    PROCESSES_TO_TEST = [2]
    # RL algorithms can often be unstable, so we run several experiments (see https://arxiv.org/abs/1709.06560)
    NUM_EXPERIMENTS = 3
    TRAIN_STEPS = 5000
    env_id = 'sdwsn-v1'
    reward_averages = []
    reward_std = []
    training_times = []
    total_procs = 0
    for n_procs in PROCESSES_TO_TEST:
        total_procs += n_procs
        print('Running for n_procs = {}'.format(n_procs))
        # Here we use the "fork" method for launching the processes, more information is available in the doc
        # This is equivalent to make_vec_env(env_id, n_envs=n_procs, vec_env_cls=SubprocVecEnv, vec_env_kwargs=dict(start_method='fork'))
        train_env = SubprocVecEnv([make_env(env_id, i+total_procs, env_kwargs=env_kwargs[i])
                                  for i in range(n_procs)], start_method='fork')
        # train_env = SubprocVecEnv(
        #     generate_cooja_environments(env_id, args.docker_command, args.docker_mount_source, num_env=2,
        #                                 env_kwargs=env_kwargs), start_method='fork')
        rewards = []
        times = []
        for experiment in range(NUM_EXPERIMENTS):
            # it is recommended to run several experiments due to variability in results
            # train_env.reset()
            # Create an instance of the RL model to use
            model = DQN('MlpPolicy', train_env, verbose=1, learning_starts=10,
                        target_update_interval=50, exploration_fraction=0.1)
            model.learn(total_timesteps=int(50000),
                        log_interval=1)
            # mean_reward, _ = evaluate_policy(
            #     model, eval_env, n_eval_episodes=EVAL_EPS)
            # rewards.append(mean_reward)
        # Important: when using subprocess, don't forget to close them
        # otherwise, you may have memory issues when running a lot of experiments
        train_env.close()
        # reward_averages.append(np.mean(rewards))
        # reward_std.append(np.std(rewards))
        # training_times.append(np.mean(times))


if __name__ == '__main__':
    main()
    sys.exit(0)
