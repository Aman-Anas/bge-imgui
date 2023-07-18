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
        io = imgui.get_io()
        backend = self.imgui_backend

        path = bge.logic.expandPath("//Orbitron-VariableFont_wght.ttf")

        # Just an approximation, can be tweaked with these scaling factors
        font_scaling_factor = 1  # Set to 2 for high res displays?
        font_size_in_pixels = 20
        # screen_scaling_factor = 1000
        backend.setScalingFactors(font_scaling_factor)
        backend.setMainFont(path, font_size_in_pixels)

        extraFontPath = bge.logic.expandPath("//Blackout 2 AM.ttf")
        self.extra_font = backend.addExtraFont(
            extraFontPath, font_size_in_pixels)

        self.show_custom_window = True

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

        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):

                clicked_quit, selected_quit = imgui.menu_item(
                    "Quit", "Cmd+Q", False, True
                )

                if clicked_quit:
                    sys.exit(0)

                imgui.end_menu()
            imgui.end_main_menu_bar()

        imgui.show_test_window()

        if self.show_custom_window:
            is_expand, self.show_custom_window = imgui.begin(
                "Custom window", True)
            if is_expand:
                imgui.text("Bar")
                imgui.text_colored("Eggs", 0.2, 1.0, 0.0)
            imgui.end()

        imgui.begin("Default Window")
        with imgui.font(self.extra_font):
            imgui.text("Text displayed using custom font")
        imgui.end()

        imgui.render()
        backend.render(imgui.get_draw_data())

    def shutdownGUI(self):
        self.keepGUIRunning = False
        self.imgui_backend.shutdown()
        self.guiThread.join()
