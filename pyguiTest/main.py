from . import pyguiWrapper


def startGUI(cont):
    if cont.sensors["tap"].positive:
        own = cont.owner
        gui = pyguiWrapper.GameGUI()
        own["gui"] = gui
