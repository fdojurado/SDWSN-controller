from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import gym
import numpy as np
from keras.models import Sequential
from keras.layers import InputLayer
from keras.layers import Dense
from tqdm import tqdm
from collections import deque
import random

env = gym.make('CartPole-v1')
env.reset()

discount_factor = 0.95
eps = 0.5
eps_min = 0.01
eps_decay = 0.99
learning_rate = 0.8
num_episodes = 50
batch_size = 32

model = Sequential()
model.add(Dense(32, input_shape=(4,), activation='relu'))
model.add(Dense(32, activation='relu'))
model.add(Dense(2, activation='linear'))
model.compile(loss='mse', optimizer='adam')

scores = []

memory = deque(maxlen=2000)

for i in tqdm(range(num_episodes), position=0, leave=True):
    total_training_rewards = 0
    state = env.reset()
    done = False
    eps *= eps_decay
    score = 0
    # while game not ended
    while not done:
        # env.render()
        # choose move with epsilon greedy
        if np.random.random() < eps:
            # exploration
            action = np.random.randint(0, env.action_space.n)
        else:
            # exploitation
            # use expand_dims here to add a dimension for input layer
            q_vals = model.predict(np.expand_dims(state, axis=0))
            action = np.argmax(q_vals)

        # execute move
        new_state, reward, done, _ = env.step(action)
        score += reward

        # modify reward so it scales with pole angle. Pole angle range [-0.418, 0.418]
        reward = 1 - abs(state[2])/0.418

        total_training_rewards += reward

        # memorize
        memory.append([np.expand_dims(state, axis=0), action,
                      reward, np.expand_dims(new_state, axis=0), done])

        # update
        # instead of training every state, we train in batch_size
        if len(memory) > batch_size:
            # sample batch_size so model could be fit on any random states in memory not just the latest state
            minibatch = random.sample(memory, batch_size)

            # iterate through the sampled batch
            for b_state, b_action, b_reward, b_new_state, b_done in minibatch:

                # if current game is done then target = reward cuz theres no future utility
                if b_done:
                    target = b_reward
                else:
                    # what we think the state's q_val should be, reward + discounted future utility
                    target = b_reward + discount_factor * \
                        np.max(model.predict(b_new_state))

                # what we thought the current state's q_val should be
                target_vector = model.predict(b_state)[0]

                # update the target_vector
                target_vector[b_action] = target

                # instead of finding temporal difference between new q_val and old q_val, we train the model by giving it the new q_val
                # and let the network do the updating
                # train the model with the batch
                model.fit(b_state, target_vector.reshape(-1,
                          env.action_space.n), epochs=1, verbose=0)

            # update epsilon
            if eps > eps_min:
                eps *= eps_decay
        if done:
            print('Total training rewards: {} after n steps = {} with final reward = {}'.format(
                total_training_rewards, i, reward))

        # new state
        state = new_state
    scores.append(score)


plt.plot(scores)
plt.ylabel('score')
plt.xlabel('episodes')
plt.title('Score of RL Agent over episodes')

reg = LinearRegression().fit(np.arange(len(scores)).reshape(-1, 1),
                             np.array(scores).reshape(-1, 1))
y_pred = reg.predict(np.arange(len(scores)).reshape(-1, 1))
plt.plot(y_pred)

scores = []
while len(scores) < 50:
    try:
        state = env.reset()
        done = False
        score = 0
        while not done:
            score += 1
            # env.render()
            q_vals = model.predict(np.expand_dims(state, axis=0))
            action = np.argmax(q_vals)

            new_state, _, done, _ = env.step(action)
            state = new_state
        scores.append(score)
    except KeyboardInterrupt:
        # env.close()
        break

print("mean")
print(np.array(scores).mean())
