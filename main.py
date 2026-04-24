""" KEY FEATURES
* Boid ('bird-oid object') flocking behavior (separation, cohesion, and alignment behaviors)
* Wind ('w') causes birds and clouds to move in certain directions and blows at different frequencies
* Cloudiness ('c') causes birds to fly slower
* Higher temperature ('t') causes birds to fly further apart, lower temperatures cause increased flocking
* The mouse acts as a toggleable predator ('p') that boids avoid
* There shouldn't be any grading shortcuts needed
"""

from cmu_graphics import *
import math
import random

# Each function, if multiple things are updated within 1 function should be updated in the order
# 1. Background and labels
# 2. Boids (separation --> cohesion --> alignment --> predator behavior)
# 3. Weather (wind --> clouds --> temperature)
# 4. Other


def onAppStart(app):
    resetApp(app)

    # add boids
    app.boids = []
    addBoids(app)

    # init random pos for clouds
    app.clouds = []
    addClouds(app)
    app.cloudShade = CloudShade()

    # init temp shade
    app.tempShade = TempShade()

    app.windParticles = []


def resetApp(app):
    app.stepsPerSecond = 12

    app.numBoids = 375
    app.visRange = 100  # boids will match avg velocity & CoM of other boids here
    app.protectRange = 20  # boids move away from other boids here

    # SEPARATION -- close_dx & close_dy * SF
    app.sepFactor = 0.05

    # COHESION --  v changes by (distance from center of flock) * CF
    app.coFactor = 0.0005

    # ALIGNMENT -- (difference of avg vel & boid vel) * AF
    app.alignFactor = 0.05

    # if close enough to edge, v nudged back by 0.5 (flat)
    app.turnFactor = 0.5

    app.minSpeed, app.maxSpeed = 5, 10
    app.margin = 100  # how close to edge before turning

    # -- Claude helped determine some of these vars below
    app.predMode = True
    app.predRad = 50
    app.predFactor = 0.3
    app.mouseX, app.mouseY = -1000, -1000

    app.weatherMode = None
    app.windFactor = 0
    app.currentGust = 0
    app.windFreq = 0
    app.windTimer = 0
    # -- End citation --

    app.cloudFactor = 0.4
    app.tempFactor = 0

    app.menuOpen = True

# For the next 5 functions from addBoids - updateBoids,
# Claude helped debug, structure code, and adapt code to cmugraphics


def addBoids(app):
    margin = app.margin
    for _ in range(app.numBoids):
        app.boids.append({
            # random.uniform gives decimal number within range for more variety
            'x':  random.uniform(margin, app.width - margin),
            'y':  random.uniform(margin, app.height - margin),
            'vx': random.uniform(-3, 3),
            'vy': random.uniform(-3, 3),
        })


def addClouds(app):
    for i in range(3):
        app.clouds.append(Cloud(i * 500 + random.randint(0, 100),
                                random.randint(10, 250),
                                random.uniform(0.5, 1.5)))


def redrawAll(app):
    # background from bedneyimages on freepik
    drawImage('sky_background.jpg', 0, 0, width=app.width, height=app.height)

    # drawing the boid
    for boid in app.boids:
        drawBoid(boid)

    # draw 'predator'
    if app.predMode:
        drawCircle(app.mouseX, app.mouseY, 10,
                   fill=None, border='tomato', borderWidth=2)

    # drawing weather
    for cloud in app.clouds:
        cloud.draw()
    app.cloudShade.draw(app)

    # temp overlay
    app.tempShade.draw(app)

    # grass
    for p in app.windParticles:
        p.draw()

    # draw menu @ end
    drawMenu(app)


def drawMenu(app):
    menuWidth = 350

    if app.menuOpen:
        drawRect(0, 0, menuWidth, app.height, opacity=70)
        drawLabel('←', 20, 40, fill='white', size=20, align='left')
        drawLabel('Boids Simulation - Starling Murmurations', 20,
                  75, fill='white', size=15, bold=True, align='left')

        # https://cs.stanford.edu/people/eroberts/courses/soco/projects/2008-09/modeling-natural-systems/boids.html

        drawLabel("This algorithm models how individual boid (bird-oid object)",
                  20, 100, fill='white', size=10, align='left')
        drawLabel(
            "movement affects the bulk motion of the flock.", 20, 110, fill='white', size=10, align='left')
        drawLabel("Each boid follows three rules: ", 20,
                  130, fill='white', size=10, align='left', bold=True)
        drawLabel("1. Separation (avoid collision)", 20,
                  145, fill='white', size=10, align='left')
        drawLabel("2. Cohesion (stay close to neighbors)", 20,
                  155, fill='white', size=10, align='left')
        drawLabel("3. Alignment (matching velocities)", 20,
                  165, fill='white', size=10, align='left')

        controls = [
            ('w', 'and the L/R arrow keys to change wind strength',
             app.weatherMode == 'wind'),
            ('c', 'and the L/R arrow keys to change cloud coverage',
             app.weatherMode == 'clouds'),
            ('t', 'and the L/R arrow keys to change temperature',
             app.weatherMode == 'temp'),
            ('p', 'to toggle predator', False),
            ('r', 'to reset weather conditions', False)
        ]

        # INSTRUCTIONS
        drawLabel('CONTROLS', 20, 650, fill='white',
                  size=15, bold=True, align='left')

        for idx, (key, label, state) in enumerate(controls):
            y = 675 + idx * 25
            color = 'tomato' if state else 'white'
            drawLabel(f"Press {key} {label}", 20, y,
                      fill=color, size=12, align='left')

        # CURRENT CONDITIONS
        # labels for when weather conditions are changing
        drawLabel('CURRENT CONDITIONS', 20, 825, fill='white',
                  size=15, bold=True, align='left')

        drawLabel(f"Wind factor:   {pythonRound(app.windFactor, 2)}", 20, 850,
                  fill='white', size=11, align='left')
        drawLabel(f"Cloud factor:  {pythonRound(app.cloudFactor, 2)}", 20, 875,
                  fill='white', size=11, align='left')
        drawLabel(f"Temperature:   {app.tempFactor}", 20, 900,
                  fill='white', size=11, align='left')

    # hide menu
    else:
        drawRect(0, app.height//2 - 30, 25, 60, opacity=70)
        drawLabel('→', 12, app.height//2, fill='white', size=20)

def onMousePress(app, mouseX, mouseY):
    # this is for the menu opening button
    if not app.menuOpen:
        if mouseX < 18:
            app.menuOpen = True
    else:
        if mouseX < 50 and mouseY < 50:
            app.menuOpen = False

# Boids as triangles
def drawBoid(boid):
    angle = math.atan2(boid['vy'], boid['vx'])
    size = 4

    # POINT 1 - tip of triangle
    x1 = boid['x'] + size * math.cos(angle)
    y1 = boid['y'] + size * math.sin(angle)

    # POINT 2 - back corner 1
    x2 = boid['x'] + size * math.cos(angle + 1.5)
    y2 = boid['y'] + size * math.sin(angle + 1.5)

    # POINT 3 - back corner 2
    x3 = boid['x'] + size * math.cos(angle - 1.5)
    y3 = boid['y'] + size * math.sin(angle - 1.5)

    drawPolygon(x1, y1, x2, y2, x3, y3)

# Claude helped outline, and my lovely mentor Meabh helped come up w idea to reduce lag :)

# adding all the boids to respective cells in spatial grid


def buildGrid(app):
    # have size for cell
    cellSize = app.width // 10
    grid = dict()

    for i, boid in enumerate(app.boids):
        boidRow = boid['y'] // cellSize
        boidCol = boid['x'] // cellSize

        if (boidRow, boidCol) not in grid:
            grid[(boidRow, boidCol)] = [i]
        else:
            grid[(boidRow, boidCol)].append(i)

    return grid
    # Psuedocode for updateBoids from "https://vanhunteradams.com/Pico/Animal_Movement/Boids-algorithm.html"


def updateBoids(app):
    # squared to calculate dist w/ sqrt
    visRange2 = app.visRange ** 2
    protectRange2 = app.protectRange ** 2
    margin = app.margin
    cellSize = app.visRange
    grid = buildGrid(app)

    for i, boid in enumerate(app.boids):
        # zeroed so each boid's position can be added to it as changes happen
        xPosAvg = yPosAvg = xVelAvg = yVelAvg = 0
        closeDx = closeDy = 0
        neighbors = 0

        boidRow = boid['y'] // cellSize
        boidCol = boid['x'] // cellSize

        # check boids in neighboring cells
        for drow in [-1, 0, 1]:
            for dcol in [-1, 0, 1]:
                # get the boids in the neighboring cells
                for j in grid.get((boidRow + drow, boidCol + dcol), []):
                    # skip "current" outer loop boid
                    if i == j:
                        continue
        # end citation
                    # actually grab each other boid from neighboring grids
                    other = app.boids[j]

                    # determines distance between boids
                    dx = boid['x'] - other['x']
                    dy = boid['y'] - other['y']
                    dist2 = dx ** 2 + dy ** 2

                    if dist2 < protectRange2:
                        # FOR SEPARATION -- sum of distances from every boid in protected range
                        closeDx += dx
                        closeDy += dy
                    elif dist2 < visRange2:
                        # FOR COHESION & ALIGNMENT -- sum up pos of neighboids
                        xPosAvg += other['x']
                        yPosAvg += other['y']
                        xVelAvg += other['vx']
                        yVelAvg += other['vy']
                        neighbors += 1  # increment neighbirds used to calculate avgs

        # call separation
        separation(app, boid, closeDx, closeDy, margin)

        # call cohesion & alignment
        cohesionAndAlignment(app, neighbors, boid, xPosAvg,
                             yPosAvg, xVelAvg, yVelAvg)

        # call predator fctn
        if app.predMode:
            avoidPredator(app, boid)

        # wind factor
        boid['vx'] += app.currentGust * app.windFactor

        # Force speed to stay mbetween min & max speed
        speed = math.sqrt(boid['vx']**2 + boid['vy']**2)
        if speed < app.minSpeed:
            # extract directions
            xDir, yDir = (boid['vx'] / speed), (boid['vy'] / speed)
            boid['vx'], boid['vy'] = xDir * app.minSpeed, yDir * app.minSpeed

        if speed > app.maxSpeed:
            xDir, yDir = (boid['vx'] / speed), (boid['vy'] / speed)
            boid['vx'], boid['vy'] = xDir * app.maxSpeed, yDir * app.maxSpeed

        # once all changes made, increment positions
        boid['x'] += boid['vx']
        boid['y'] += boid['vy']

        # hard stop to prevent going off screen
        boid['x'] = max(5, min(app.width - 5, boid['x']))
        boid['y'] = max(5, min(app.height - 5, boid['y']))

# Followed "https://vanhunteradams.com/Pico/Animal_Movement/Boids-algorithm.html" for separation & cohesionAndAlignment
# For the next 2 functions, Claude helped debug and keep track of variables


def separation(app, boid, closeDx, closeDy, margin):
    # SEPARATION -- velocity changes by total distance away * SF
    boid['vx'] += closeDx * app.sepFactor
    boid['vy'] += closeDy * app.sepFactor

    # Turn away from edges
    if boid['x'] < margin:
        boid['vx'] += app.turnFactor
    if boid['x'] > app.width - margin:
        boid['vx'] -= app.turnFactor
    if boid['y'] < margin:
        boid['vy'] += app.turnFactor
    if boid['y'] > app.height - margin:
        boid['vy'] -= app.turnFactor


def cohesionAndAlignment(app, neighbors, boid, xPosAvg, yPosAvg, xVelAvg, yVelAvg):
    if neighbors > 0:
        # calculate actual avgs here
        xPosAvg /= neighbors
        yPosAvg /= neighbors
        xVelAvg /= neighbors
        yVelAvg /= neighbors

        # COHESION -- boid steers towards neighbors CoM
        # update velocity with distance between CoM * CF
        boid['vx'] += (xPosAvg - boid['x']) * app.coFactor
        boid['vy'] += (yPosAvg - boid['y']) * app.coFactor

        # ALIGNMENT -- boid matches velocity of neighbors
        # difference between average v's and current boid v
        boid['vx'] += (xVelAvg - boid['vx']) * app.alignFactor
        boid['vy'] += (yVelAvg - boid['vy']) * app.alignFactor

# Predator behavior adapted from "http://www.kfish.org/boids/pseudocode.html"


def avoidPredator(app, boid):
    xPos, yPos = boid['x'], boid['y']
    dx, dy = (xPos - app.mouseX), (yPos - app.mouseY)

    # if the boid is within range
    if (dx**2 + dy**2) < app.predRad**2:
        # get further away from whatever edge of circle it's on using sep logic
        boid['vx'] += app.predFactor * dx
        boid['vy'] += app.predFactor * dy


def onMouseMove(app, mouseX, mouseY):
    # if the boid is within a certain range of mouse, should turn away w/ same turning logic
    app.mouseX, app.mouseY = mouseX, mouseY


def onKeyPress(app, key):
    if key == 'r':
        resetApp(app)

    if key == 'p':
        app.predMode = not app.predMode

    # weather
    if key == 'w':
        app.weatherMode = 'wind' if app.weatherMode != 'wind' else None
    elif key == 'c':
        app.weatherMode = 'clouds' if app.weatherMode != 'clouds' else None
    elif key == 't':
        app.weatherMode = 'temp' if app.weatherMode != 'temp' else None


def onKeyHold(app, keys):
    if app.weatherMode == 'wind':
        if 'left' in keys and app.windFreq >= -50 and app.windFactor >= -1:
            app.windFreq -= 5
            app.windFactor -= 0.1
        if 'right' in keys and app.windFreq <= 50 and app.windFactor <= 1:
            app.windFreq += 5
            app.windFactor += 0.1

    elif app.weatherMode == 'temp':
        if 'left' in keys and app.sepFactor >= 0.01 and app.protectRange >= 5:
            # reduce protected range and sep factor
            app.sepFactor -= 0.01
            app.protectRange -= 2
            app.tempFactor -= 1

        if 'right' in keys and app.sepFactor <= 0.1 and app.protectRange <= 30:
            app.sepFactor += 0.01
            app.protectRange += 2
            app.tempFactor += 1

    elif app.weatherMode == 'clouds':
        if 'left' in keys and app.minSpeed <= 9 and app.maxSpeed <= 14:
            app.minSpeed += 0.2
            app.maxSpeed += 0.2
            app.cloudFactor = max(0, app.cloudFactor - 0.1)
        if 'right' in keys and app.minSpeed >= 1 and app.maxSpeed >= 6:
            app.minSpeed -= 0.2
            app.maxSpeed -= 0.2
            app.cloudFactor = min(1, app.cloudFactor + 0.1)


def onStep(app):
    updateBoids(app)

    # wind stuff
    app.windTimer += 1
    if app.windTimer > random.randint(app.windFreq, app.windFreq + 60):
        app.currentGust = 1 + random.uniform(0, 1)
        app.windTimer = 0
    else:
        app.currentGust *= 0.9  # decrease wind each time, so it's not constantly huge wind

    # clouds
    # Claude wrote this
    targetNumClouds = int(3 + app.cloudFactor * 10)

    if len(app.clouds) < targetNumClouds:
        app.clouds.append(Cloud(random.randint(0, app.width),  # random x
                                random.randint(10, 250),
                                random.uniform(0.5, 1.5)))
    elif len(app.clouds) > targetNumClouds:
        # --exempt--
        app.clouds[-1].fadingOut = True

    app.clouds = [c for c in app.clouds if not (
        c.fadingOut and c.opacity == 0)]
    # --end of exempt--
    # -- End citation --

    for cloud in app.clouds:
        cloud.updatePos(app)

    # -- exempt code (clauded) --
    if abs(app.windFactor) > 0.1:
        for _ in range(int(abs(app.windFactor) * 8)):  # increased from 3 to 8
            app.windParticles.append(WindParticle(app))

    app.windParticles = [p for p in app.windParticles if p.opacity > 0]

    for p in app.windParticles:
        p.update(app)
    # -- exempt code --


class Cloud:
    def __init__(self, x, y, scale):
        self.x = x
        self.y = y
        self.scale = scale

        self.opacity = 0
        self.fadingOut = False

    def updatePos(self, app):
        self.x += 0.3 + app.windFactor * 2
        # --exempt--
        # Claude wrote partially
        if self.fadingOut:
            self.opacity = max(0, self.opacity - 5)
        else:
            self.opacity = min(80, self.opacity + 2)
        # --end of exempt--

        if self.x > app.width + 200:
            self.x = -200
        elif self.x < - 200:
            self.x = app.width + 200

    # cloud png from Adi Putra on vecteezy.com
    def draw(self):
        drawImage('cloud_transparent.png', self.x, self.y, width=int(
            300*self.scale), height=int(200*self.scale), opacity=int(self.opacity))

    # -- End of citation --

# for this function, Claude gave me outline/approach


class Overlay:
    def __init__(self):
        self.opacity = 2


class CloudShade(Overlay):
    def draw(self, app):
        # the cloudier, the greater the opacity
        opacity = int(app.cloudFactor * 40)
        drawRect(0, 0, app.width, app.height, fill='dimGray', opacity=opacity)


class TempShade(Overlay):
    def draw(self, app):
        if app.tempFactor < 0:  # cold
            r, g, b, = 0, 0, 255
        else:
            r, g, b = 255, 0, 0

        opacity = int(abs(app.tempFactor) * self.opacity)
        drawRect(0, 0, app.width, app.height,
                 fill=rgb(r, g, b), opacity=opacity)


# -- exempt code (clauded) --
class WindParticle:
    def __init__(self, app):
        self.x = random.randint(0, app.width)
        self.y = random.randint(0, app.height)
        self.size = random.uniform(2, 5)
        self.opacity = random.randint(50, 100)
        self.speed = random.uniform(1, 3)

    def update(self, app):
        self.x += app.windFactor * 6 * self.speed  # faster drift
        self.y += random.uniform(-0.5, 0.5)         # slight vertical wobble
        self.opacity -= 1             # fade out over time

    def draw(self):
        drawCircle(self.x, self.y, self.size,
                   fill='white', opacity=int(self.opacity))
# -- end exempt --


def main():
    runApp()


main()
