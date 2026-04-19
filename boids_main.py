from cmu_graphics import *
import math
import random


def onAppStart(app):
    app.background = 'lightBlue'
    app.stepsPerSecond = 30

    app.numBoids = 300
    app.visRange = 100  # boids will match avg velocity & CoM of other boids here
    app.protectRange = 20  # boids move away from other boids here

    # COHESION --  v changes by (distance from center of flock) * CF
    app.coFactor = 0.0005
    # ALIGNMENT -- (difference of avg vel & boid vel) * AF
    app.alignFactor = 0.05
    app.sepFactor = 0.05  # close_dx & close_dy * SF
    # if close enough to edge, v nudged back by 0.5 (flat)
    app.turnFactor = 0.5

    app.minSpeed, app.maxSpeed = 5, 10
    app.margin = 100  # how close to edge before turning

    app.predRad = 50
    app.predFactor = 0.3
    app.mouseX, app.mouseY = -1000, -1000

    app.boids = []
    addBoids(app)


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


def redrawAll(app):
    # drawing the boid
    for boid in app.boids:
        drawCircle(boid['x'], boid['y'], 2)

    # draw 'predator'
    drawCircle(app.mouseX, app.mouseY, 10,
               fill=None, border='tomato', borderWidth=2)


def updateBoids(app):
    # squared to calculate dist w/ sqrt
    visRange2 = app.visRange ** 2
    protectRange2 = app.protectRange ** 2
    margin = app.margin

    for i, boid in enumerate(app.boids):
        # zeroed so each boid's position can be added to it as changes happen
        xPosAvg = yPosAvg = xVelAvg = yVelAvg = 0
        closeDx = closeDy = 0
        neighbors = 0

        # loop through every other boid
        for j, other in enumerate(app.boids):
            if i == j:  # skip "current" outer loop boid
                continue

            # determines distance between boids
            dx = boid['x'] - other['x']
            dy = boid['y'] - other['y']

            # only change pos if within visual range
            if abs(dx) < app.visRange and abs(dy) < app.visRange:
                # actually check the dist now for protected vs visual range
                dist2 = dx ** 2 + dy ** 2

                if dist2 < protectRange2:
                    # sum of distances from every boid in protected range
                    closeDx += dx
                    closeDy += dy
                elif dist2 < visRange2:
                    # COHESION & ALIGNMENT -- sum up pos of neighboids
                    xPosAvg += other['x']
                    yPosAvg += other['y']
                    xVelAvg += other['vx']
                    yVelAvg += other['vy']
                    neighbors += 1  # increment neighbirds used to calculate avgs

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

        # SEPARATION -- velocity changes by total distance away * AF
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

        # call predator fctn
        avoidPredator(app, boid)

        # Force speed to stay mbetween min & max speed
        speed = math.sqrt(boid['vx']**2 + boid['vy']**2)
        if speed < app.minSpeed:
            # extract directions
            xDir, yDir = (boid['vx'] / speed), (boid['vy'] / speed)
            boid['vx'], boid['vy'] = xDir * app.minSpeed, yDir * app.minSpeed

        if speed > app.maxSpeed:
            xDir, yDir = (boid['vx'] / speed), (boid['vy'] / speed)
            boid['vx'], boid['vy'] = xDir * app.maxSpeed, yDir * app.maxSpeed

        boid['x'] += boid['vx']
        boid['y'] += boid['vy']

        # prevent going off screen

        boid['x'] = max(5, min(app.width - 5, boid['x']))
        boid['y'] = max(5, min(app.height - 5, boid['y']))


def onMouseMove(app, mouseX, mouseY):
    # if the boid is within a certain range of mouse, should turn away w/ same turning logic
    app.mouseX, app.mouseY = mouseX, mouseY


def avoidPredator(app, boid):
    xPos, yPos = boid['x'], boid['y']
    dx, dy = (xPos - app.mouseX), (yPos - app.mouseY)

    # if the boid is within range
    if (dx**2 + dy**2) < app.predRad**2:
        # get further away from whatever edge of circle it's on using sep logic
        boid['vx'] += app.predFactor * dx
        boid['vy'] += app.predFactor * dy


def onStep(app):
    updateBoids(app)


def main():
    runApp()


main()
