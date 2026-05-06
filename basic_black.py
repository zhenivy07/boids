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


def resetApp(app):
    app.stepsPerSecond = 12

    app.numBoids = 500
    app.visRange = 100  # boids will match avg velocity & CoM of other boids here
    app.protectRange = 20  # boids move away from other boids here

    # SEPARATION -- close_dx & close_dy * SF
    app.sepFactor = 0.05
    app.depSepFactor = 0.05

    # COHESION --  v changes by (distance from center of flock) * CF
    app.coFactor = 0.005

    # ALIGNMENT -- (difference of avg vel & boid vel) * AF
    app.alignFactor = 0.01

    # if close enough to edge, v nudged back by 0.5 (flat)
    app.turnFactor = 0.5

    app.minSpeed, app.maxSpeed = 5, 12
    app.margin = 100  # how close to edge before turning

    app.depth = 200


def addBoids(app):
    margin = app.margin

    for _ in range(app.numBoids):
        app.boids.append({
            # random.uniform gives decimal number within range for more variety
            'x':  random.uniform(margin, app.width - margin),
            'y':  random.uniform(margin, app.height - margin),
            'z': random.uniform(0.1, app.depth),
            'vx': random.uniform(-3, 3),
            'vy': random.uniform(-3, 3),
            'vz': random.uniform(-3, 3),
        })


def redrawAll(app):
    # background from bedneyimages on freepik
    drawRect(0, 0, app.width, app.height)

    # drawing the boid
    sortedBoids = sorted(app.boids, key=lambda boid: boid['z'], reverse=True)
    for boid in app.boids:
        drawBoid(boid)


def drawBoid(boid):
    # calculate perspective scale for z-axis, inverted so smaller z = bigger bird
    scale = 1 - (boid['z'] / 600)
    size = 5 * scale
    opacity = 40 + int(50 * scale)

    angle = math.atan2(boid['vy'], boid['vx'])

    # POINT 1 - tip of triangle
    x1 = boid['x'] + size * math.cos(angle)
    y1 = boid['y'] + size * math.sin(angle)

    # POINT 2 - back corner 1
    x2 = boid['x'] + size * math.cos(angle + 1.5)
    y2 = boid['y'] + size * math.sin(angle + 1.5)

    # POINT 3 - back corner 2
    x3 = boid['x'] + size * math.cos(angle - 1.5)
    y3 = boid['y'] + size * math.sin(angle - 1.5)

    drawPolygon(x1, y1, x2, y2, x3, y3, opacity=opacity, fill='white')

# Claude helped write this, and my lovely mentor Meabh helped come up w idea to reduce lag :)

# adding all the boids to respective cells in hypothetical grid


def buildGrid(app):
    # have size for cell
    cellSize = app.visRange
    grid = dict()

    for i, boid in enumerate(app.boids):
        boidRow = boid['y'] // cellSize
        boidCol = boid['x'] // cellSize
        boidDep = boid['z'] // cellSize

        key = (boidRow, boidCol, boidDep)

        if key not in grid:
            grid[key] = [i]
        else:
            grid[key].append(i)

    return grid
    # Psuedocode for updateBoids from "https://vanhunteradams.com/Pico/Animal_Movement/Boids-algorithm.html"


def updateBoids(app):
    cellSize = app.visRange
    grid = buildGrid(app)

    for i, boid in enumerate(app.boids):
        # for storing neighbor idx and dist from curr boid
        potentialNeighbors = []

        boidRow = int(boid['y'] // cellSize)
        boidCol = int(boid['x'] // cellSize)
        boidDep = int(boid['z'] // cellSize)

        # get boids from 3D grid
        for drow in [-1, 0, 1]:
            for dcol in [-1, 0, 1]:
                for ddep in [-1, 0, 1]:
                    key = (boidRow + drow, boidCol +
                           dcol, boidDep + ddep)
                    # get the boids in the neighboring cells
                    for j in grid.get(key, []):
                        # skip "current" outer loop boid
                        if i == j:
                            continue

                        # actually grab each other boid from neighboring grids
                        other = app.boids[j]

                        # determines distance between boids
                        dx = boid['x'] - other['x']
                        dy = boid['y'] - other['y']
                        dz = boid['z'] - other['z']
                        dist2 = dx ** 2 + dy ** 2 + dz ** 2

                        potentialNeighbors.append((j, dist2))

        # taking closest 7 neighbors
        potentialNeighbors.sort(key=lambda x: x[1])
        closestSeven = potentialNeighbors[:7]

        xPosAvg = yPosAvg = zPosAvg = xVelAvg = yVelAvg = zVelAvg = 0
        closeDx = closeDy = closeDz = 0

        for j, dist2 in closestSeven:
            other = app.boids[j]

            if dist2 < app.protectRange ** 2:
                # initiate vars in preperation for calling sep fctn
                closeDx += (boid['x'] - other['x'])
                closeDy += (boid['y'] - other['y'])
                closeDz += (boid['z'] - other['z'])

            # update for co & align
            xPosAvg += other['x']
            yPosAvg += other['y']
            zPosAvg += other['z']
            xVelAvg += other['vx']
            yVelAvg += other['vy']
            zVelAvg += other['vz']

        # use count of neighbors found
        numFound = len(closestSeven)
        separation(app, boid, closeDx, closeDy, closeDz, app.margin)

        # call cohesion & alignment
        cohesionAndAlignment(app, numFound, boid, xPosAvg,
                             yPosAvg, zPosAvg, xVelAvg, yVelAvg, zVelAvg)

        # Force speed to stay mbetween min & max speed
        speed = math.sqrt(boid['vx']**2 + boid['vy']**2 + boid['vz']**2)
        if speed < app.minSpeed:
            # extract directions
            xDir, yDir = (boid['vx'] / speed), (boid['vy'] / speed)
            boid['vx'], boid['vy'] = xDir * app.minSpeed, yDir * app.minSpeed

        if speed > app.maxSpeed:
            ratio = app.maxSpeed / speed
            boid['vx'] *= ratio
            boid['vy'] *= ratio
            boid['vz'] *= ratio

        # once all changes made, increment positions
        boid['x'] += boid['vx']
        boid['y'] += boid['vy']
        boid['z'] += boid['vz']

        # hard stop to prevent going off screen
        boid['x'] = max(5, min(app.width - 5, boid['x']))
        boid['y'] = max(5, min(app.height - 5, boid['y']))

        # 3D bound check
        if boid['z'] < 0 or boid['z'] > app.depth:
            boid['vz'] *= -1

# Followed "https://vanhunteradams.com/Pico/Animal_Movement/Boids-algorithm.html" for separation & cohesionAndAlignment
# For the next 2 functions, Claude helped debug and keep track of variables


def separation(app, boid, closeDx, closeDy, closeDz, margin):
    # SEPARATION -- velocity changes by total distance away * SF
    boid['vx'] += closeDx * app.sepFactor
    boid['vy'] += closeDy * app.sepFactor
    boid['vz'] += closeDz * app.depSepFactor

    # Turn away from edges
    if boid['x'] < margin:
        boid['vx'] += app.turnFactor
    if boid['x'] > app.width - margin:
        boid['vx'] -= app.turnFactor
    if boid['y'] < margin:
        boid['vy'] += app.turnFactor
    if boid['y'] > app.height - margin:
        boid['vy'] -= app.turnFactor


def cohesionAndAlignment(app, neighbors, boid, xP, yP, zP, xV, yV, zV):
    if neighbors > 0:

        # COHESION -- boid steers towards neighbors CoM
        # update velocity with distance between CoM * CF
        boid['vx'] += (xP/neighbors - boid['x']) * app.coFactor
        boid['vy'] += (yP/neighbors - boid['y']) * app.coFactor
        boid['vz'] += (zP/neighbors - boid['z']) * app.coFactor

        # ALIGNMENT -- boid matches velocity of neighbors
        # difference between average v's and current boid v
        boid['vx'] += (xV/neighbors - boid['vx']) * app.alignFactor
        boid['vy'] += (yV/neighbors - boid['vy']) * app.alignFactor
        boid['vz'] += (zV/neighbors - boid['vz']) * app.alignFactor

# Predator behavior adapted from "http://www.kfish.org/boids/pseudocode.html"


def onStep(app):
    updateBoids(app)


def main():
    runApp()


main()
