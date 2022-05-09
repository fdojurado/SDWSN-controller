# from controller.deep_reinforcement_learning.agent import Agent
from agent import Agent
import tensorflow as tf
from tensorflow.keras.optimizers import Adam
import gym

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

optimizer = Adam(learning_rate=0.01)
agent = Agent(env, optimizer, max_epsilon, min_epsilon, decay)

batch_size = 32
num_of_episodes = 100
agent.q_network.summary()

steps_to_update_target_model = 0

for episode in range(num_of_episodes):
    total_training_rewards = 0
    state = env.reset()
    reward = 0
    done = False

    while not done:
        steps_to_update_target_model += 1
        if False:
            env.render()
        # Run Action
        action = agent.act(state)

        # Take action
        next_state, reward, done, _ = env.step(action)
        agent.store(state, action, reward, next_state, done)

        state = next_state
        total_training_rewards += reward

        if steps_to_update_target_model % 4 == 0 or done:
            agent.retrain(batch_size)

        if done:
            print('Total training rewards: {} after n steps = {} with final reward = {}'.format(
                total_training_rewards, episode, reward))
            total_training_rewards += 1

            if steps_to_update_target_model >= 100:
                print('Copying main network weights to the target network weights')
                agent.align_target_model()
                steps_to_update_target_model = 0
            break

    agent.update_epsilon(episode)
env.close()
