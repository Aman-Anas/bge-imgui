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
