import imgui
from .renderer import BGEImguiRenderer
from bge.types import KX_Scene
from threading import Thread
import time
import sys
import bge.logic


class BGEImguiWrapper:
    def __init__(self, scene: KX_Scene) -> None:
        bge.logic.gui = self
        self.imgui_context = imgui.create_context()
        self.imgui_backend = BGEImguiRenderer(scene)

        self.initializeGUI()

        self.keepGUIRunning = True
        self.guiThread = Thread(target=self.runGUIThread)
        self.guiThread.start()

    def initializeGUI(self):
        pass
        # For child classes to override

    def runGUIThread(self):
        while self.keepGUIRunning:
            self.run()

            # May not be needed, but this yields the thread to other ones
            # Avoids holding up game frame rendering
            time.sleep(sys.float_info.epsilon)

    def updateOnGameFrame(self):
        backend = self.imgui_backend
        backend.updateOnFrame()

    def run(self):
        backend = self.imgui_backend

        # Update inputs like mouse/keyboard
        backend.updateOnLoop()

        imgui.new_frame()

        self.drawGUI()

        imgui.render()
        backend.render(imgui.get_draw_data())

    def drawGUI(self):
        pass
        # For child classes to override

    def shutdownGUI(self):
        self.keepGUIRunning = False
        self.imgui_backend.shutdown()
        self.guiThread.join()
