# from controller.deep_reinforcement_learning.agent import Agent
from agent import Agent
import tensorflow as tf
from tqdm import tqdm
from tensorflow.keras.optimizers import Adam
import gym
import numpy as np

DISABLE_GPU = True

if DISABLE_GPU:
    try:
        # Disable all GPUS
        tf.config.set_visible_devices([], 'GPU')
        visible_devices = tf.config.get_visible_devices()
        for device in visible_devices:
            assert device.device_type != 'GPU'
    except:
        # Invalid device or cannot modify virtual devices once initialized.
        pass

print(tf.__version__)


env = gym.make("CartPole-v1").env
# env.render()

print('Number of states: {}'.format(env.observation_space))
print('Number of actions: {}'.format(env.action_space))

# epsilon = 0.5  # Epsilon-greedy algorithm in initialized at 1 meaning every step is random at the start
max_epsilon = 0.5  # You can't explore more than 100% of the time
min_epsilon = 0.01  # At a minimum, we'll always explore 1% of the time
decay = 0.01

# Frequency of target update

TARGET_UPDATE = 100

optimizer = Adam()
agent = Agent(env, optimizer, max_epsilon, min_epsilon, decay)

batch_size = 32
num_episodes = 50
agent.q_network.summary()

# init num_updates
num_updates = 0

for episode in tqdm(range(num_episodes), position=0, leave=True):
    total_training_rewards = 0
    state = env.reset()
    done = False

    while not done:

        if False:
            env.render()

        # Run Action
        action = agent.epsilon_greedy(np.expand_dims(state, axis=0))

        # Take action
        next_state, reward, done, _ = env.step(action)
        # modify reward so it scales with pole angle. Pole angle range [-0.418, 0.418]
        reward = 1 - abs(state[2])/0.418

        # memorize
        agent.store(np.expand_dims(state, axis=0), action, reward,
                    np.expand_dims(next_state, axis=0), done)

        # Experience replay
        agent.retrain(batch_size)

        # clone target network every C frames
        num_updates += 1

        if num_updates >= TARGET_UPDATE:
            num_updates = 0
            agent.align_target_model()
            # save memory and model
            agent.save_exp_model()

        total_training_rewards += reward

        if done:
            print('Total training rewards: {} after n steps = {} with final reward = {}'.format(
                total_training_rewards, episode, reward))

        # update state
        state = next_state

    # decay epsilon
    agent.update_epsilon(episode)

# env.close()
