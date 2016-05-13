import random
import numpy as np


class gpsarsa:
    def __init__(self, actions, epsilon=0.1, gamma=0.9, sigma=10):
        self.mean_q = {}
        self.cov_q = {}

        self.pairs = []
        self.actions = actions
        self.epsilon = epsilon
        self.gamma = gamma
        self.sigma = sigma      # Gaussian noise
        self.rewards = []
        self.Kmatrix = None
        self.Hmatrix = None
        pass

    def startEpisode(self, s_state, s_action):
        pair = (s_state, s_action)
        self.pairs.append(pair)
        self.Kmatrix = np.array([[self.kernel(pair, pair)]])
        self.Hmatrix = np.array([[1, -1*self.gamma]])
        pass

    def learn(self, state1, action1, reward, state2, action2):
        pair = (state2, action2)
        self.pairs.append(pair)
        # expand H matrix
        H = self.Hmatrix
        t = len(H[0])-1
        H = np.hstack([H, np.zeros((t, 1))])
        H = np.vstack([H, np.zeros((1, t+2))])
        H[t][t+1] = 1
        H[t][t+2] = -1*self.gamma
        self.Hmatrix = H

        # calculate k vector for later use
        kvector = self.kernel_vector(pair)

        # expand K matrix
        K = self.Kmatrix
        t = len(K)-1
        K = np.hstack([K, kvector])
        K = np.vstack([K, kvector, 0])
        K[t][t] = self.kernel(pair, pair)

        # append reward
        self.rewards.append(reward)

        # calculate Q-function posterior

        pass

    # terminal step in episode
    def endEpisode(self):
        pass

    def chooseAction(self, state):
        pass

    def kernel(self, pair1, pair2):
        # state kernel (s, s') * action kernel (a, a')
        return 0

    def kernel_vector(self, pair):
        V = np.array(len(self.pairs))
        for i, pair0 in enumerate(self.pairs):
            V[i] = self.kernel(pair0, pair)
        return V


