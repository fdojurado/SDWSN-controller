import numpy as np
import random
from collections import deque
import tensorflow as tf
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Dense, Embedding, Reshape
from tensorflow.keras.optimizers import Adam


class Agent:
    def __init__(self, env, optimizer, max_epsilon, min_epsilon, decay):

        # Initialize attributes
        self._state_size = env.env.observation_space.shape
        self._action_size = env.env.action_space.n
        self._optimizer = optimizer
        self.env = env

        self.experience_replay = deque(maxlen=5000)

        # Initialize discount and learning
        self.discount_factor = 0.95
        self.learning_rate = 0.8
        # Epsilon
        self.max_epsilon = max_epsilon
        self.min_epsilon = min_epsilon
        self.decay = decay
        self.epsilon = max_epsilon

        # Build networks
        self.q_network = self._build_compile_model()
        self.target_network = self._build_compile_model()
        self.align_target_model()

    def update_epsilon(self, episode):
        self.epsilon = self.min_epsilon + \
            (self.max_epsilon - self.min_epsilon) * np.exp(-self.decay * episode)
        return

    def store(self, state, action, reward, next_state, done):
        self.experience_replay.append(
            (np.expand_dims(state, axis=0), action, reward, np.expand_dims(next_state, axis=0), done))

    def _build_compile_model(self):
        init = tf.keras.initializers.HeUniform()
        model = Sequential()
        model.add(Dense(24, input_shape=self._state_size, activation='relu', kernel_initializer=init))
        # model.add(Embedding(self._state_size, 10, input_length=1))
        # model.add(Reshape((10,)))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(self._action_size, activation='linear'))

        model.compile(loss='mse', optimizer=self._optimizer)
        return model

    def align_target_model(self):
        self.target_network.set_weights(self.q_network.get_weights())

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return self.env.action_space.sample()

        q_values = self.q_network.predict(np.expand_dims(state, axis=0))
        return np.argmax(q_values[0])

    def retrain(self, batch_size):
        if len(self.experience_replay) < batch_size:
            return

        minibatch = random.sample(self.experience_replay, batch_size)

        for state, action, reward, next_state, done in minibatch:

            if done:
                max_future_q = reward
            else:
                # what we think the state's q_val should be, reward + discounted future utility
                max_future_q = reward + self.discount_factor * \
                    np.max(self.q_network.predict(next_state))

            # what we thought the current state's q_val should be
            target_vector = self.target_network.predict(next_state)[0]

            # update the target_vector
            target_vector[action] = max_future_q

            # instead of finding temporal difference between new q_val and old q_val, we train the model by giving it the new q_val
            # and let the network do the updating
            # train the model with the batch
            self.q_network.fit(
                state, target_vector.reshape(-1, self.env.action_space.n), epochs=1, verbose=0)
