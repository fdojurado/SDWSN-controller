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
            (state, action, reward, next_state, done))

    def _build_compile_model(self):
        # init = tf.keras.initializers.HeUniform()
        model = Sequential()
        model.add(Dense(32, input_shape=(4,), activation='relu'))
        # model.add(Dense(32, input_shape=self._state_size,
        #           activation='relu', kernel_initializer=init))
        # model.add(Embedding(self._state_size, 10, input_length=1))
        # model.add(Reshape((10,)))
        model.add(Dense(32, activation='relu'))
        # model.add(Dense(2, activation='relu'))
        model.add(Dense(self._action_size, activation='linear'))

        model.compile(loss='mse', optimizer=self._optimizer)
        return model

    def align_target_model(self):
        self.target_network.set_weights(self.q_network.get_weights())

    def save_exp_model(self):
        np.save('memory', self.experience_replay)
        self.q_network.save('tmp_model')

    def epsilon_greedy(self, state):
        # exploration
        if np.random.random() < self.epsilon:
            # exploration
            action = np.random.randint(0, self.env.action_space.n)
            return action
        else:
            # exploitation
            # use expand_dims here to add a dimension for input layer
            q_vals = self.q_network.predict(state)
            action = np.argmax(q_vals)
            return action

    def retrain(self, batch_size):
        # if memory is less than batch size, return nothing
        if len(self.experience_replay) < batch_size:
            return

        # sample a batch
        minibatch = random.sample(self.experience_replay, batch_size)

        # iterate through batch
        for state, action, reward, new_state, done in minibatch:
            # scale states to be [0,1]. We only scale before fitting cuz storing uint8 is cheaper
            # state = state/255
            # new_state = new_state/255

            target = reward

            # if game not over, target q val includes discounted future utility
            # we use a cloned model to predict here for stability. Model is changed every C frames
            # we use the online model to choose best action to deal with overestimation error (Double-Q learning)
            if not done:
                best_future_action = np.argmax(
                    self.q_network.predict(new_state))

                target = reward + self.discount_factor * \
                    self.target_network.predict(
                        new_state)[0][best_future_action]

            # get current actions vector
            target_vector = self.q_network.predict(state)[0]

            # update current action q val with target q val
            target_vector[action] = target
            # fit model
            # train the model with the batch
            self.q_network.fit(
                state, target_vector.reshape(-1, self.env.action_space.n), epochs=1, verbose=0)
