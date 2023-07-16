import sys
from .gl_utils import *
import bge
from PyQt5 import QtGui
from PyQt5.QtOpenGL import *
from PyQt5 import QtCore, QtWidgets, QtOpenGL
import math


class Ui_MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        print("bruh")
        super(Ui_MainWindow, self).__init__()
        self.widget = glWidget()
        self.button = QtWidgets.QPushButton('Test', self)
        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.addWidget(self.widget)
        mainLayout.addWidget(self.button)
        self.setLayout(mainLayout)


class glWidget(QGLWidget):
    def __init__(self, parent=None):
        QGLWidget.__init__(self, parent)
        self.setMinimumSize(640, 480)


def paintGL():
    # print("E")
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(-2.5, 0.5, -6.0)
    glColor3f(1.0, 1.5, 0.0)
    glPolygonMode(GL_FRONT, GL_FILL)
    glBegin(GL_TRIANGLES)
    glVertex3f(2.0, -1.2, 0.0)
    glVertex3f(2.6, 0.0, 0.0)
    glVertex3f(2.9, -1.2, 0.0)
    glEnd()
    glFlush()


def initializeGL():
    # print("Q")
    glClearDepth(1.0)
    glDepthFunc(GL_LESS)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, 1.33, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    paintGL()


def potato():

    x = 0
    y = 0
    width = 500
    height = 600
    gl_position = [
        [x, y],
        [x + width, y],
        [x + width, y + height],
        [x, y + height]
    ]
    # Enable alpha blending
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Enable polygon offset
    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(1.0, 1.0)

    glBegin(GL_QUADS)
    for i in range(4):
        #glColor4f(colors[i][0], colors[i][1], colors[i][2], colors[i][3])
        glColor4f(1, 1, 1, 1)
        glVertex2f(gl_position[i][0], gl_position[i][1])
    glEnd()

    glDisable(GL_POLYGON_OFFSET_FILL)


def saveLoadGLState(glFunction):
    view = glGetIntegerv(GL_VIEWPORT)
    # Save the state
    glPushAttrib(GL_ALL_ATTRIB_BITS)

    # Disable depth test so we always draw over things
    glDisable(GL_DEPTH_TEST)

    # Disable lighting so everything is shadless
    glDisable(GL_LIGHTING)

    # Unbinding the texture prevents BGUI frames from somehow picking up on
    # color of the last used texture
    glBindTexture(GL_TEXTURE_2D, 0)

    # Make sure we're using smooth shading instead of flat
    glShadeModel(GL_SMOOTH)

    # Setup the matrices
    glMatrixMode(GL_TEXTURE)
    glPushMatrix()
    glLoadIdentity()
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, view[2], 0, view[3])
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Do things
    glFunction()

    # Reset the state
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_TEXTURE)
    glPopMatrix()
    glPopAttrib()


# if __name__ == '__main__':
#     app = QtWidgets.QApplication(sys.argv)
#     Form = QtWidgets.QMainWindow()
#     ui = Ui_MainWindow(Form)
#     ui.show()
#     sys.exit(app.exec_())

def skyColour():
    # sky colours for day, night and the difference between them
    night = [0.05, 0.035, 0.063]
    day = [0.103, 0.499, 1]
    diff = [n-d for n, d in zip(night, day)]

    # create a sine wave that repeats after 24 hours of game time
    # the final value, y, should be between 0 and 1
    a = -0.5
    h = 0.5
    c = 1
    b = (2*math.pi)
    x = math.sin((b * (bge.logic.getClockTime()/60)/24) + c)
    y = a*x+h

    r = night[0] - diff[0]*y
    g = night[1] - diff[1]*y
    b = night[2] - diff[2]*y
    glClearColor(r, g, b, 1)
    glClear(GL_COLOR_BUFFER_BIT)
    return


def main(cont: bge.types.SCA_PythonController):
    if cont.sensors["tap"].positive:
        own = cont.owner
        #app = QtWidgets.QApplication([])
        #Form = QtWidgets.QMainWindow()
        # print("O")
        #ui = Ui_MainWindow(Form)
        # print("P")

        bge.logic.colors = [
            (1, 1, 1, 1),
            (1, 1, 1, 1),
            (1, 1, 1, 1),
            (1, 1, 1, 1)
        ]

        own.scene.post_draw.append(saveLoadGLState)
        # ui.show()
        # own.scene.pre_draw.append(skyColour)
