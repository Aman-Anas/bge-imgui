from . import imguiWrapper
# import bge.logic
# from .renderShaders import VERTEX_SHADER, FRAGMENT_SHADER


def testInit(cont):
    if cont.sensors["tap"].positive:
        own = cont.owner
        gui = imguiWrapper.BGEImguiWrapper(own.scene)
        own["gui"] = gui
        # print("bro wut")


# def runGUI(cont):
#     if cont.sensors["loop"].positive:
#         own = cont.owner
#         if own["gui"] is not False:
#             gui: imguiWrapper.BGEImguiWrapper = own["gui"]
#             gui.run()
