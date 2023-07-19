import imgui
from .renderer import BGEImguiRenderer
from .widgets import GUIWindow
from bge.types import KX_Scene
import bge.logic


class BGEImguiWrapper:
    def __init__(self, scene: KX_Scene) -> None:
        bge.logic.gui = self
        self.imgui_context = imgui.create_context()
        self.imgui_backend = BGEImguiRenderer(scene)
        self.windows: list[GUIWindow] = []

        self.initializeGUI()

    def initializeGUI(self):
        pass
        # For child classes to override

    def addWindow(self, window: GUIWindow):
        self.windows.append(window)

    def removeWindow(self, window: GUIWindow):
        self.windows.remove(window)

    def updateOnGameFrame(self):
        self.run()

    def drawGUI(self):
        for window in self.windows:
            window.drawWindow()

    def run(self):
        backend = self.imgui_backend

        # Update inputs like mouse/keyboard
        backend.updateIO()

        imgui.new_frame()

        self.drawGUI()

        backend.drawCursor()

        imgui.end_frame()

        imgui.render()
        backend.render(imgui.get_draw_data())

    def shutdownGUI(self):
        self.imgui_backend.shutdown()
