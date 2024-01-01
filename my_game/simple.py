from .simple_gui import SimpleCustomGUI
from bge.types import SCA_PythonController
import bge


def startGUI(cont: SCA_PythonController):
    if cont.sensors["tap"].positive:
        own = cont.owner
        # Initialize the gui
        bge.logic.gui = SimpleCustomGUI(own.scene)


def runGUI(cont: SCA_PythonController):
    if cont.sensors["loop"].positive:
        own = cont.owner
        gui: SimpleCustomGUI = bge.logic.gui
        gui.update_gui()


def stopGUI(cont: SCA_PythonController):
    if cont.sensors["stop"].positive:
        own = cont.owner
        gui: SimpleCustomGUI = bge.logic.gui
        gui.shutdown_gui()
        bge.logic.endGame()
