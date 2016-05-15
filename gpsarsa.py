import random
import numpy as np
import math

class gpsarsa:
    def __init__(self, actions, nstates=0, epsilon=0.1, gamma=0.9, sigma=5, p=4):
        self.mean_q = {}
        self.cov_q = {}

        self.states_vectors = {}        # states vector representation
        self.action_vectors = {}        # actions vector representation
        self.pairs = []
        self.actions = actions
        self.nstates = nstates      # num of states
        self.epsilon = epsilon
        self.gamma = gamma
        self.sigma = sigma      # Gaussian noise
        self.p = p

        self.rewards = [0, -1]
        self.Kmatrix = None
        self.Hmatrix = None
        pass

    def getMeanQ(self, state, action):
        return self.mean_q.get((state, action), 0.0)

    def getCovQ(self, state, action):
        return self.cov_q.get((state, action), 0.0)

    def startEpisode(self, s_state, s_action):
        pair = (s_state, s_action)
        # self.pairs.append(pair)
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
        H[t][t] = 1
        H[t][t+1] = -1*self.gamma
        self.Hmatrix = H

        # calculate k vector for later use
        kvector = self.kernel_vector(pair)

        # expand K matrix
        K = self.Kmatrix
        t = len(K)-1
        K = np.hstack([K, np.transpose([kvector])])
        K = np.vstack([K, [np.append(kvector, 0)]])
        knew = self.kernel(pair, pair)
        K[t+1][t+1] = knew
        kvector = np.append(kvector, knew)
        self.Kmatrix = K

        # append reward
        self.rewards.append(reward)

        # calculate Q-function posterior
        self.calcQposterior(pair, kvector, H, K, self.rewards)
        pass

    # terminal step in episode
    def endEpisode(self):
        pass

    def chooseAction(self, state):
        if random.random() < self.epsilon:
            action = random.choice(self.actions)
        else:
            q = [self.getMeanQ(state, a) for a in self.actions]
            maxQ = min(q)
            count = q.count(maxQ)
            if count > 1:
                best = [i for i in range(len(self.actions)) if q[i] == maxQ]
                i = random.choice(best)
            else:
                i = q.index(maxQ)

            action = self.actions[i]
        return action

    def kernel_vector(self, pair):
        V = np.zeros(len(self.pairs))
        for i, pair0 in enumerate(self.pairs):
            print 'i: %d' % i
            V[i] = self.kernel(pair0, pair)
        return V

    def kernel(self, pair1, pair2):
        # state kernel (s, s') * action kernel (a, a')
        state1 = pair1[0]
        action1 = pair1[1]
        state2 = pair2[0]
        action2 = pair2[1]
        state1vec = self.stateToVector(state1)
        state2vec = self.stateToVector(state2)
        action1vec = self.actionToVector(action1)
        action2vec = self.actionToVector(action2)
        ka = self.gaussian_kernel(action1vec, action2vec)
        ks = self.gaussian_kernel(state1vec, state2vec)
        return ks * ka

    def calcQposterior(self, pair, kvec, H, K, rvec):
        # H*K*H_trans
        HT = np.transpose(H)
        hkh = np.dot(np.dot(HT, K), H)
        # sigma^2*H*H_trans
        shh = math.pow(self.sigma, 2) * np.dot(HT, H)
        W = np.linalg.inv(np.add(hkh, shh))
        val = np.dot(np.dot(H, W), rvec)
        mu = np.dot(np.transpose(kvec), val)
        self.mean_q[pair] = mu

        pass

    def gaussian_kernel(self, vec1, vec2):
        dist = np.linalg.norm(vec1-vec2)
        val = -1 * dist/(2*math.pow(self.sigma, 2))
        return math.pow(self.p, 2) * math.exp(val)

    def stateToVector(self, state):
        if self.states_vectors.get(state) is None:
            v = np.zeros(self.nstates)
            v[len(self.states_vectors)] = 1
            self.states_vectors[state] = v
        return self.states_vectors[state]

    def actionToVector(self, action):
        if len(self.action_vectors) == 0:
            for i, act in enumerate(self.actions):
                v = np.zeros(len(self.actions))
                v[i] = 1
                self.action_vectors[act] = v
        return self.action_vectors[action]


def main():
    import gpsarsa
    actions = (1, 2, 3, 4)
    gpsarsa = gpsarsa.gpsarsa(actions, 48)
    # for j in range(4):
    #     for i in range(12):
    #         print gpsarsa.stateToVector((i, j))
    # print 'states count: %d' % len(gpsarsa.states_vectors)

    for i in range(4):
        print gpsarsa.actionToVector((i+1))

if __name__ == "__main__":
    main()

