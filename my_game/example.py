from bge.types import SCA_PythonController
import bge

from .bgimgui.renderer import BGEImguiRenderer

from imgui_bundle import imgui


# Simple example script for running imgui without any wrappers (just the BGEImguiRenderer)
def startGUI(cont: SCA_PythonController):
    if cont.sensors["tap"].positive:
        own = cont.owner
        context = imgui.create_context()
        imgui_backend = BGEImguiRenderer(
            own.scene, bge.logic.expandPath("//cursors"))
        own["context"] = context
        own["backend"] = imgui_backend


def runGUI(cont: SCA_PythonController):
    if cont.sensors["loop"].positive:
        own = cont.owner
        backend: BGEImguiRenderer = own["backend"]

        # Update inputs like mouse/keyboard
        backend.update_io()

        imgui.new_frame()

        # Draw windows and elements here
        imgui.show_demo_window()

        backend.draw_cursor()

        imgui.end_frame()

        imgui.render()
        backend.render(imgui.get_draw_data())


def stopGUI(cont: SCA_PythonController):
    if cont.sensors["stop"].positive:
        own = cont.owner
        backend: BGEImguiRenderer = own["backend"]
        backend.shutdown()
        bge.logic.endGame()
