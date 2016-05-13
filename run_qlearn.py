import cellular
import qlearn
import random


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


def startCell():
    if startPoint is not None:
        cell = world.getCell(startPoint[0], startPoint[1])
    else:
        cell = world.getCell(1, 4)
    return cell


def backupStep(lastState, lastAction, reward, state):
    stepHistory.append((lastState, lastAction, reward, state))


def saveEpisode():
    global stepHistory
    for step in stepHistory:
        if step is not None:
            f.write(str(step)+'\n')
    f.write('\n')
    stepHistory = []
    pass


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
        global startPoint
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
        self.ai = qlearn.QLearn(actions=range(directions), alpha=0.1, gamma=0.9, epsilon=0.1)
        self.lastAction = None
        self.lastState = None
        self.score = 0

    def update(self):
        state = self.calcState()
        reward = self.calcReward()
        action = self.ai.chooseAction(state)
        if self.lastAction is not None:
            self.ai.learn(self.lastState, self.lastAction, reward, state)
        self.lastState = state
        self.lastAction = action
        backupStep(self.lastState, self.lastAction, reward, state)

        # goal reached, episode end.
        if self.cell.goal:
            self.cell = startCell()
            self.lastAction = None
            saveEpisode()
            return

        # fell to the cliff.
        if self.cell.cliff:
            self.lastAction = None
            self.cell = startCell()
        else:
            self.goInDirection(action)

    def calcState(self):
        return self.cell.x, self.cell.y

    def calcReward(self):
        if self.cell.cliff:
            return cliffReward
        elif self.cell.goal:
            self.score += 1
            return goalReward
        else:
            return normalReward

normalReward = -1
cliffReward = -100
goalReward = 0

mouse = Mouse()
world = cellular.World(Cell, directions=directions, filename='gridworld.txt')
world.age = 0

world.addAgent(mouse, cell=startCell())

f = open('episodes_qlearn.txt', 'w')

while mouse.score < 500:
    world.update()
    print 'age: %d score: %d' % (world.age, mouse.score)

oldscore = None
mouse.ai.epsilon = 0.005
world.display.activate(size=30)
world.display.delay = 1
while 1:
    world.update()
    if oldscore != mouse.score:
        print mouse.score
        oldscore = mouse.score

f.flush()
f.close()
