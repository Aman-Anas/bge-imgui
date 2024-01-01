from . import bgimgui
from .simple_gui import SimpleCustomGUI
from bge.types import SCA_PythonController
import bge


def startGUI(cont: SCA_PythonController):
    if cont.sensors["tap"].positive:
        own = cont.owner
        # Initialize the gui
        own["gui"] = SimpleCustomGUI(
            own.scene, main=False, panel=own, resolution=(400, 400))

        # This is how you would change the global panel interaction distance
        # bgimgui.BGEImguiRenderer.INTERACTION_DIST = 3


def runGUI(cont: SCA_PythonController):
    if cont.sensors["loop"].positive:
        own = cont.owner
        gui: SimpleCustomGUI = own["gui"]
        gui.update_gui()


def stopGUI(cont: SCA_PythonController):
    if cont.sensors["stop"].positive:
        own = cont.owner
        gui: SimpleCustomGUI = own["gui"]
        gui.shutdown_gui()
        bge.logic.endGame()
