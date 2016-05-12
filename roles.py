import cellular
import qlearn
import time
import random
import shelve

directions = 4
startPoint = None
stepHistory = []


def pickRandomLocation():
    while 1:
        x = random.randrange(world.width)
        y = random.randrange(world.height)
        cell = world.getCell(x, y)
        if not (cell.wall or len(cell.agents) > 0):
            return cell


def backtoStartLocation():
    if startPoint is not None:
        cell = world.getCell(startPoint.x, startPoint.y)
    else:
        cell = world.getCell(1, 4)
    return cell


def backupStep(lastState, lastAction, reward, state):
    stepHistory.append((lastState, lastAction, reward, state))


def saveEpisode():
    for step in stepHistory:
        print step


class Cell(cellular.Cell):
    wall = False
    cliff = False
    start = False
    goal = False

    def color(self):
        if self.wall:
            return 'black'
        elif self.cliff:
            return 'orange'
        elif self.start:
            return 'green'
        elif self.goal:
            return 'red'
        else:
            return 'white'

    def load(self, data, loc):
        if data == 'X':
            self.wall = True
        elif data == 'C':
            self.cliff = True
        elif data == 'S':
            self.start = True
            startPoint = loc
        elif data == 'G':
            self.goal = True
        else:
            self.wall = False
            self.cliff = False
            self.start = False
            self.goal = False


class Mouse(cellular.Agent):
    color = 'yellow'

    def __init__(self):
        self.ai = None
        self.ai = qlearn.QLearn(actions=range(directions),
                                alpha=0.1, gamma=0.9, epsilon=0.1)

        self.lastState = None
        self.lastAction = None

    def update(self):
        state = self.calcState()
        reward = -1

        # goal reached, episode end.
        if self.cell.goal:
            if self.lastState is not None:
                self.ai.learn(self.lastState, self.lastAction, reward, state)
            self.lastState = None
            self.cell = backtoStartLocation()
            backupStep(self.lastState, self.lastAction, reward, state)
            saveEpisode()
            return

        # fell to the cliff.
        if self.cell.cliff:
            reward = -100
            self.cell = backtoStartLocation()

        if self.lastState is not None:
            self.ai.learn(self.lastState, self.lastAction, reward, state)

        backupStep(self.lastState, self.lastAction, reward, state)

        state = self.calcState()
        action = self.ai.chooseAction(state)
        self.lastState = state
        self.lastAction = action

        self.goInDirection(action)

    def calcState(self):
        return self.cell.x, self.cell.y


mouse = Mouse()
world = cellular.World(Cell, directions=directions, filename='gridworld.txt')
world.age = 0

world.addAgent(mouse, cell=backtoStartLocation())

# epsilonx = (0, 100000)
# epsilony = (0.1, 0)
# epsilonm = (epsilony[1] - epsilony[0]) / (epsilonx[1] - epsilony[0])

# endAge = world.age + 150000
# while world.age < endAge:
#     world.update()
#
#     if world.age % 100 == 0:
#         pass
#
#     if world.age % 10000 == 0:
#         pass

world.display.activate(size=30)
world.display.delay = 1
while 1:
    world.update()

