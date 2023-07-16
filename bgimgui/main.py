from . import imguiWrapper
import bgl
from bge.types import SCA_PythonController
import bge
# from .shader import *
#from .renderShaders import FRAGMENT_SHADER
from threading import Thread
from .gl_utils import *


def startGUI(cont: SCA_PythonController):
    if cont.sensors["tap"].positive:
        own = cont.owner
        gui = imguiWrapper.BGEImguiWrapper(own.scene)
        # shader = own.scene.filterManager.addFilter(
        #     0, bge.logic.RAS_2DFILTER_CUSTOMFILTER, FRAGMENT_SHADER)
        # shader.enabled = True
        #e = dir(bgl)

        # bge.logic.colors = [
        #     (0, 0, 0, 1),
        #     (0, 1, 0, 1),
        #     (0, 0, 1, 1),
        #     (0, 1, 1, 1)
        # ]
        # x = 0
        # y = 0
        # width = 0.5
        # height = 0.5
        # bge.logic.gl_position = [
        #     [x, y],
        #     [x + width, y],
        #     [x + width, y + height],
        #     [x, y + height]
        # ]
        
        # own.scene.post_draw.append(potato)

        #print('glShaderSource' in e)


def run(cont):
    if cont.sensors["loop"].positive:
        own = cont.owner
        potato(own["colors"], own["gl_position"])


def potato():
    colors = bge.logic.colors
    gl_position = bge.logic.gl_position
    # Enable alpha blending
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Enable polygon offset
    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(1.0, 1.0)

    glBegin(GL_QUADS)
    for i in range(4):
        glColor4f(self.colors[i][0], self.colors[i][1], self.colors[i][2], self.colors[i][3])
        glVertex2f(self.gl_position[i][0], self.gl_position[i][1])
    glEnd()

    glDisable(GL_POLYGON_OFFSET_FILL)
