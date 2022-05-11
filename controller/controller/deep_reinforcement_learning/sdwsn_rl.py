from stable_baselines3.common.env_checker import check_env
from sdwsn_env import sdwsnEnv

# 13, 17 and 41 are coprime with the other slotframes
env = sdwsnEnv(10, 3, [13,17,41])

print('Number of states: {}'.format(env.observation_space))
print('Number of actions: {}'.format(env.action_space))

check_env(env, warn=True)
