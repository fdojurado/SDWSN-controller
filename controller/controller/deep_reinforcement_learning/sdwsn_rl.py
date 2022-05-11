from stable_baselines3.common.env_checker import check_env
from sdwsn_env import sdwsnEnv

env = sdwsnEnv(10, 3, 31)

print('Number of states: {}'.format(env.observation_space))
print('Number of actions: {}'.format(env.action_space))

check_env(env, warn=True)
