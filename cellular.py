import random
import sys

neighbourSynonyms = ('neighbours', 'neighbors', 'neighbour', 'neighbor')


class Cell:
    def __getattr__(self, key):
        if key in neighbourSynonyms:
            pts = [self.world.getPointInDirection(
                self.x, self.y, dir) for dir in range(self.world.directions)]
            ns = tuple([self.world.grid[y][x] for (x, y) in pts])
            for n in neighbourSynonyms:
                self.__dict__[n] = ns
            return ns
        raise AttributeError(key)


class Agent:
    def __setattr__(self, key, val):
        if key == 'cell':
            old = self.__dict__.get(key, None)
            if old is not None:
                old.agents.remove(self)
            if val is not None:
                val.agents.append(self)
        self.__dict__[key] = val

    def __getattr__(self, key):
        if key == 'leftCell':
            return self.getCellOnLeft()
        elif key == 'rightCell':
            return self.getCellOnRight()
        elif key == 'aheadCell':
            return self.getCellAhead()
        raise AttributeError(key)

    def turn(self, amount):
        self.dir = (self.dir + amount) % self.world.directions

    def turnLeft(self):
        self.turn(-1)

    def turnRight(self):
        self.turn(1)

    def turnAround(self):
        self.turn(self.world.directions / 2)

    # return True if successfully moved in that direction
    def goInDirection(self, dir):
        target = self.cell.neighbour[dir]
        if getattr(target, 'wall', False):
            #print "hit a wall"
            return False
        self.cell = target
        return True

    def goForward(self):
        self.goInDirection(self.dir)

    def goBackward(self):
        self.turnAround()
        self.goForward()
        self.turnAround()

    def getCellAhead(self):
        return self.cell.neighbour[self.dir]

    def getCellOnLeft(self):
        return self.cell.neighbour[(self.dir - 1) % self.world.directions]

    def getCellOnRight(self):
        return self.cell.neighbour[(self.dir + 1) % self.world.directions]

    def goTowards(self, target):
        if self.cell == target:
            return
        best = None
        for n in self.cell.neighbours:
            if n == target:
                best = target
                break
            dist = (n.x - target.x) ** 2 + (n.y - target.y) ** 2
            if best is None or bestDist > dist:
                best = n
                bestDist = dist
        if best is not None:
            if getattr(best, 'wall', False):
                return
            self.cell = best


class World:
    def __init__(self, cell=None, width=None, height=None, directions=8, filename=None):
        if cell is None:
            cell = Cell
        self.Cell = cell
        self.display = makeDisplay(self)
        self.directions = directions
        if filename is not None:
            data = file(filename).readlines()
            if height is None:
                height = len(data)
            if width is None:
                width = max([len(x.rstrip()) for x in data])
        if width is None:
            width = 20
        if height is None:
            height = 20
        self.width = width
        self.height = height
        self.image = None
        self.reset()
        if filename is not None:
            self.load(filename)

    def getCell(self, x, y):
        return self.grid[y][x]

    def getWrappedCell(self, x, y):
        return self.grid[y % self.height][x % self.width]

    def reset(self):
        self.grid = [[self.makeCell(i, j)
                      for i in range(self.width)]
                     for j in range(self.height)]
        self.dictBackup = [[{} for i in range(self.width)]
                           for j in range(self.height)]
        self.agents = []
        self.age = 0

    def makeCell(self, x, y):
        c = self.Cell()
        c.x = x
        c.y = y
        c.world = self
        c.agents = []
        return c

    def randomize(self):
        if not hasattr(self.Cell, 'randomize'):
            return
        for row in self.grid:
            for cell in row:
                cell.randomize()

    def save(self, f=None):
        if not hasattr(self.Cell, 'save'):
            return
        if isinstance(f, type('')):
            f = file(f, 'w')

        total = ''
        for j in range(self.height):
            line = ''
            for i in range(self.width):
                line += self.grid[j][i].save()
            total += '%s\n' % line
        if f is not None:
            f.write(total)
            f.close()
        else:
            return total

    def load(self, f):
        if not hasattr(self.Cell, 'load'):
            return
        if isinstance(f, type('')):
            f = file(f)
        lines = f.readlines()
        lines = [x.rstrip() for x in lines]
        fh = len(lines)
        fw = max([len(x) for x in lines])
        if fh > self.height:
            fh = self.height
            starty = 0
        else:
            starty = (self.height - fh) / 2
        if fw > self.width:
            fw = self.width
        else:
            startx = (self.width - fw) / 2

        self.reset()
        for j in range(fh):
            line = lines[j]
            for i in range(min(fw, len(line))):
                self.grid[starty + j][startx + i].load(line[i], (i, j))

    def update(self):
        if hasattr(self.Cell, 'update'):
            for j, row in enumerate(self.grid):
                for i, c in enumerate(row):
                    self.dictBackup[j][i].update(c.__dict__)
                    c.update()
                    c.__dict__, self.dictBackup[j][i] = self.dictBackup[j][i], c.__dict__
            for j, row in enumerate(self.grid):
                for i, c in enumerate(row):
                    c.__dict__, self.dictBackup[j][i] = self.dictBackup[j][i], c.__dict__
            for a in self.agents:
                a.update()
            self.display.redraw()
        else:
            for a in self.agents:
                oldCell = a.cell
                a.update()
                if oldCell != a.cell:
                    self.display.redrawCell(oldCell.x, oldCell.y)
                self.display.redrawCell(a.cell.x, a.cell.y)
        self.display.update()
        self.age += 1

    def getPointInDirection(self, x, y, dir):
        if self.directions == 8:
            # top, top-right, right, ...
            dx, dy = [(0, -1), (1, -1), (1, 0), (1, 1),
                      (0, 1), (-1, 1), (-1, 0), (-1, -1)][dir]
        elif self.directions == 4:
            dx, dy = [(0, -1), (1, 0), (0, 1), (-1, 0)][dir]

        x2 = x + dx
        y2 = y + dy

        if x2 < 0:
            x2 += self.width
        if y2 < 0:
            y2 += self.height
        if x2 >= self.width:
            x2 -= self.width
        if y2 >= self.height:
            y2 -= self.height

        return (x2, y2)

    def addAgent(self, agent, x=None, y=None, cell=None, dir=None):
        self.agents.append(agent)
        if cell is not None:
            x = cell.x
            y = cell.y
        if x is None:
            x = random.randrange(self.width)
        if y is None:
            y = random.randrange(self.height)
        if dir is None:
            dir = random.randrange(self.directions)
        agent.cell = self.grid[y][x]
        agent.dir = dir
        agent.world = self


import time

def makeDisplay(world):
    d = Display()
    d.world = world
    return d


class DummyDisplay:
    def activate(self, size=4):
        pass

    def redraw(self):
        pass

    def redrawCell(self):
        pass

    def update(self):
        pass

    def setTitle(self, title):
        pass


class TkinterDisplay:
    def __init__(self):
        pass


class PygameDisplay:
    activated = False
    paused = False
    title = ''
    updateEvery = 1
    delay = 0
    screen = None

    def activate(self, size=4):
        self.size = size
        pygame.init()
        w = self.world.width * size
        h = self.world.height * size
        if PygameDisplay.screen is None or PygameDisplay.screen.get_width() != w or PygameDisplay.screen.get_height() != h:
            PygameDisplay.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE, 32)
        self.activated = True
        self.defaultColor = self.getColor(self.world.grid[0][0].__class__())
        self.redraw()

    def redraw(self):
        if not self.activated:
            return
        self.screen.fill(pygame.color.Color('gray'))
        self.offsetx = (self.screen.get_width() - self.world.width * self.size) / 2
        self.offsety = (self.screen.get_height() - self.world.height * self.size) / 2
        sy = self.offsety
        odd = False
        for row in self.world.grid:
            sx = self.offsetx
            for cell in row:
                if len(cell.agents) > 0:
                    c = self.getColor(cell.agents[0])
                else:
                    c = self.getColor(cell)
                try:
                    self.screen.fill(c, (sx, sy, self.size-1, self.size-1))
                except TypeError:
                    print 'Error: invalid color:', c
                sx += self.size
            odd = not odd
            sy += self.size

    def redrawCell(self, x, y):
        if not self.activated:
            return
        sx = x * self.size + self.offsetx
        sy = y * self.size + self.offsety

        cell = self.world.grid[y][x]
        if len(cell.agents) > 0:
            c = self.getColor(cell.agents[0])
        else:
            c = self.getColor(cell)

        self.screen.fill(c, (sx, sy, self.size-1, self.size-1))

    def update(self):
        if not self.activated:
            return
        if self.world.age % self.updateEvery != 0 and not self.paused:
            return
        self.setTitle(self.title)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                sys.exit()
            elif event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                self.onResize(event)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEUP:
                if self.delay > 0:
                    self.delay -= 1
                else:
                    self.updateEvery *= 2
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEDOWN:
                if self.updateEvery > 1:
                    self.updateEvery /= 2
                else:
                    self.delay += 1
                if self.delay > 10:
                    self.delay = 10
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.pause()

        pygame.display.flip()
        if self.delay > 0:
            time.sleep(self.delay * 0.05)

    def setTitle(self, title):
        if not self.activated:
            return
        self.title = title
        title += ' %s ' % makeTitle(self.world)
        if pygame.display.get_caption()[0] != title:
            pygame.display.set_caption(title)

    def pause(self, event=None):
        self.paused = not self.paused
        while self.paused:
            self.update()

    def onResize(self, event):
        if not self.activated:
            return
        pygame.display.set_mode(event.size, pygame.RESIZABLE, 32)
        oldSize = self.size
        scalew = event.size[0] / self.world.width
        scaleh = event.size[1] / self.world.height
        self.size = min(scalew, scaleh)
        if self.size < 1:
            self.size = 1
        self.redraw()

    def getColor(self, obj):
        if obj == 'gridline':
            c = 'gray'
        else:
            c = getattr(obj, 'color', None)
        if c is None:
            c = getattr(obj, 'color', 'white')
        if callable(c):
            c = c()
        if isinstance(c, type(())):
            if isinstance(c[0], type(0.0)):
                c = (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))
            return c
        return pygame.color.Color(c)

    def saveImage(self, filename=None):
        if filename is None:
            filename = '%05d.bmp' % self.world.age
        pygame.image.save(self.screen, filename)


def makeTitle(world):
    text = 'age: %d' % world.age
    extra = []
    if world.display.paused:
        extra.append('paused')
    if world.display.updateEvery != 1:
        extra.append('skip=%d' % world.display.updateEvery)
    if world.display.delay > 0:
        extra.append('delay=%d' % world.display.delay)

    if len(extra) > 0:
        text += ' [%s]' % ', '.join(extra)
    return text

try:
    import pygame
    Display = PygameDisplay
except:
    try:
        import Tkinter
        import cStringIO
        Display = TkinterDisplay
    except:
        Display = DummyDisplay



































