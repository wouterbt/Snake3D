import pygame
from OpenGL.GL import *
from OpenGL.GLUT import glutSolidCube, glutSolidSphere
from random import random
from sys import exit

TURNSPEED = 0.2 # degrees per millisecond
SIZE = 5 # cube size
MOVETIME = 1000 # milliseconds
WIDTH = 640
HEIGHT = 480

class Cube:
    gameOver = False
    score = 0

    def __init__(self, size, font):
        self.size = size
        self.font = font
        self.width, self.height = pygame.display.get_window_size()
        maxX = size / 2
        minX = -maxX
        myRange = [x + minX for x in range(size + 1)]
        self.edges = [[(minX, y, z), (maxX, y, z)] for y in myRange for z in myRange]
        self.edges.extend([[(x, minX, z), (x, maxX, z)] for x in myRange for z in myRange])
        self.edges.extend([[(x, y, minX), (x, y, maxX)] for x in myRange for y in myRange])
        self.edges = [item for sublist in self.edges for item in sublist] # flatten list

        self.wallsX = [[(x, minX, minX), (x, maxX, minX), (x, maxX, maxX), (x, minX, maxX)] for x in myRange]
        self.wallsX = [item for sublist in self.wallsX for item in sublist] # flatten list
        self.wallsY = [[(minX, y, minX), (minX, y, maxX), (maxX, y, maxX), (maxX, y, minX)] for y in myRange]
        self.wallsY = [item for sublist in self.wallsY for item in sublist] # flatten list
        self.wallsZ = [[(minX, minX, z), (minX, maxX, z), (maxX, maxX, z), (maxX, minX, z)] for z in myRange]
        self.wallsZ = [item for sublist in self.wallsZ for item in sublist] # flatten list

        self.rotationAxis = "x"
        self.rotationVector = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
        self.rotating = False
        self.currentRotation = 0.0
        self.targetRotation = 0
        self.snake = Snake((0, 0, SIZE // 2))
        self.spawnApple()
        self.clock = pygame.time.Clock()
        self.lastMoveTime = pygame.time.get_ticks()

    def spawnApple(self):
        tryAgain = True
        while tryAgain:
            position = tuple([int(random() * self.size) - self.size // 2] * 3)
            if not self.snake.testPosition(position):
                self.apple = Apple(position)
                tryAgain = False

    def drawText(self, text, x, y):
        img = self.font.render(text, True, (255, 255, 255, 255))
        data = pygame.image.tostring(img, "RGBA", True)
        glWindowPos2i(x - img.get_width() // 2, y - img.get_height() // 2)     
        glDrawPixels(img.get_width(), img.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

    def display(self):
        currentTime = pygame.time.get_ticks()
        delta = TURNSPEED * self.clock.tick(30)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glLineWidth(1)

        glPushMatrix()
        glTranslate(0, 0, -10)

        if self.rotating:
            if self.currentRotation < self.targetRotation:
                self.currentRotation += delta
            else:
                self.currentRotation -= delta
            if abs(self.currentRotation - self.targetRotation) < delta:
                self.snake.update(self.rotationAxis, self.targetRotation)
                self.apple.update(self.rotationAxis, self.targetRotation)
                self.currentRotation = 0.0
                self.targetRotation = 0
                self.rotating = False
        glRotate(self.currentRotation, *self.rotationVector[self.rotationAxis])

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        if currentTime > self.lastMoveTime + MOVETIME and not self.gameOver:
            self.snake.forward(self)
            self.lastMoveTime = currentTime
        self.apple.display()
        self.snake.display()

        glMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0, 0, 1, 1]) # blue opaque
        glBegin(GL_LINES)
        for item in self.edges:
            glVertex(*item)
        glEnd()
        
        glMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [1, 0, 1, 0.2]) # purple transparant

        glPolygonMode(GL_FRONT, GL_FILL)
        glPolygonMode(GL_BACK, GL_POINT)

        glBegin(GL_QUADS)
        glNormal(1, 0, 0)
        for item in self.wallsX:
            glVertex(*item)
        glEnd()

        glBegin(GL_QUADS)
        glNormal(-1, 0, 0)
        for item in self.wallsX[::-1]:
            glVertex(*item)
        glEnd()

        glBegin(GL_QUADS)
        glNormal(0, 1, 0)
        for item in self.wallsY:
            glVertex(*item)
        glEnd()

        glBegin(GL_QUADS)
        glNormal(0, -1, 0)
        for item in self.wallsY[::-1]:
            glVertex(*item)
        glEnd()

        glPolygonMode(GL_FRONT, GL_POINT)
        glPolygonMode(GL_BACK, GL_FILL)

        glBegin(GL_QUADS)
        glNormal(0, 0, 1)
        for item in self.wallsZ:
            glVertex(*item)
        glEnd()

        glBegin(GL_QUADS)
        glNormal(0, 0, -1)
        for item in self.wallsZ[::-1]:
            glVertex(*item)
        glEnd()

        glPopMatrix()

        self.drawText(str(self.score), 50, self.height - 50)
        
        if self.gameOver:
            self.drawText("Game Over", self.width // 2, self.height // 2)

        pygame.display.flip()

class Element:
    def __init__(self, position):
        self.position = position
        self.color = [1, 1, 1, 1]
    
    def drawShape(self):
        glutSolidCube(0.95)

    def display(self):
        glPushMatrix()
        glTranslate(*self.position)
        glMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, self.color)
        self.drawShape()
        glPopMatrix()

    def update(self, rotationAxis, rotationAngle):
        i = 1 if rotationAngle > 0 else -1
        x, y, z = self.position
        if rotationAxis == "x":
            self.position = x, -i * z, i * y
        if rotationAxis == "y":
            self.position = i * z, y, -i * x

class BodyElement (Element):
    def __init__(self, position):
        super().__init__(position)
        self.color = [0, 1, 0, 0.5] # green transparant

    def makeBody(self):
        self.color = [1, 1, 0, 0.5] # yellow transparant

class Apple (Element):
    def __init__(self, position):
        super().__init__(position)
        self.color = [1, 0, 0, 1] # red opaque

    def drawShape(self):
        glutSolidSphere(0.5, 100, 100)

class Snake:
    def __init__(self, position):
        self.body = [BodyElement(position)]
    
    def display(self):
        for b in self.body[::-1]:
            b.display()
    
    def update(self, rotationAxis, rotationAngle):
        for b in self.body:
            b.update(rotationAxis, rotationAngle)

    def forward(self, cube):
        x, y, z = self.body[-1].position
        newPosition = x, y, z - 1
        if  z == -(cube.size // 2) or self.testPosition(newPosition):
            cube.gameOver = True
            return
        self.body[-1].makeBody()
        self.body.append(BodyElement(newPosition))
        if newPosition == cube.apple.position:
            cube.score += 1
            cube.spawnApple()
        else:
            del(self.body[0])

    def testPosition(self, position):
        for b in self.body:
            if b.position == position:
                return True
        return False

class Game:
    def keyboard(self, key):
        if key == pygame.K_UP or key == pygame.K_DOWN:
            delta = 90 if key == pygame.K_DOWN else -90
            self.myCube.targetRotation += delta
            self.myCube.rotationAxis = "x"
            self.myCube.rotating = True
        if key == pygame.K_LEFT or key == pygame.K_RIGHT:
            delta = 90 if key == pygame.K_RIGHT else -90
            self.myCube.targetRotation += delta
            self.myCube.rotationAxis = "y"
            self.myCube.rotating = True
        if key == pygame.K_ESCAPE:
            pygame.quit()
            exit()
        if key == pygame.K_SPACE and self.myCube.gameOver:
                self.startGame()

    def startGame(self):
        self.myCube = Cube(SIZE, self.font)

    def __init__(self):
        pygame.init()
        self.font = pygame.font.SysFont("helvetica", 72)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)
        pygame.display.set_caption("Snake 3D")
 
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-WIDTH / HEIGHT, WIDTH / HEIGHT, -1, 1, 2, 20)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glEnable(GL_LIGHTING)
        glEnable(GL_RESCALE_NORMAL)
        glEnable(GL_LIGHT0)
        glLight(GL_LIGHT0, GL_POSITION, [2, 1, -5, 1]) # w = 1: positional light source
        glLight(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8])
        glLight(GL_LIGHT0, GL_AMBIENT, [0.4, 0.4, 0.4])
        glLight(GL_LIGHT0, GL_SPECULAR, [1, 1, 1])
        glMaterial(GL_FRONT_AND_BACK, GL_SPECULAR, [1, 1, 1])
        glMaterial(GL_FRONT_AND_BACK, GL_SHININESS, 50)

        self.startGame()

        running = True

        while running:
            self.myCube.display()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    self.keyboard(event.key)
                if event.type == pygame.VIDEORESIZE:
                    self.myCube.width, self.myCube.height = event.size
        pygame.quit()

Game()
