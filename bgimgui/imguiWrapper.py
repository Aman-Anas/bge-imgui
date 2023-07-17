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

        self.show_custom_window = True

        self.guiThread = Thread(target=self.runGUIThread)
        self.guiThread.start()
        bge.logic.mouse.visible = True

    def runGUIThread(self):
        while True:
            self.run()
            time.sleep(sys.float_info.epsilon)

    def run(self):
        backend = self.imgui_backend

        backend.updateIO()

        imgui.new_frame()

        if False:
            is_expand, self.show_custom_window = imgui.begin(
                "Custom window", True)
            if is_expand:
                imgui.text("Bar")
                imgui.text_ansi("B\033[31marA\033[mnsi ")
                imgui.text_ansi_colored(
                    "Eg\033[31mgAn\033[msi ", 0.2, 1.0, 0.0)
                imgui.extra.text_ansi_colored("Eggs", 0.2, 1.0, 0.0)

            imgui.end()
        if False:
            # open new window context
            imgui.begin("Your first window!", True)

            # draw text label inside of current window
            imgui.text("Hello world!")

            imgui.end()

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

        imgui.render()
        backend.render(imgui.get_draw_data())
