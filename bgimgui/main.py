from .imguiWrapper import BGEImguiWrapper
from bge.types import SCA_PythonController
import bge


def startGUI(cont: SCA_PythonController):
    if cont.sensors["tap"].positive:
        own = cont.owner
        gui = BGEImguiWrapper(own.scene)


def runGUI(cont: SCA_PythonController):
    if cont.sensors["loop"].positive:
        own = cont.owner
        gui: BGEImguiWrapper = bge.logic.gui
        gui.updateOnGameFrame()


def stopGUI(cont: SCA_PythonController):
    if cont.sensors["stop"].positive:
        own = cont.owner
        gui: BGEImguiWrapper = bge.logic.gui
        gui.shutdownGUI()
        bge.logic.endGame()
