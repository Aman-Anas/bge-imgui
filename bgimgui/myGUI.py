from .imguiWrapper import BGEImguiWrapper
import bge
import imgui
import sys


class MyCustomGUI(BGEImguiWrapper):
    def initializeGUI(self):
        super().initializeGUI()

        backend = self.imgui_backend

        font_global_scaling_factor = 1  # Set to 2 for high res displays?
        backend.setScalingFactors(font_global_scaling_factor)

        main_font_path = bge.logic.expandPath(
            "//Orbitron-VariableFont_wght.ttf")
        main_font_size_in_pixels = 20
        backend.setMainFont(main_font_path, main_font_size_in_pixels)

        extra_font_path = bge.logic.expandPath("//Blackout 2 AM.ttf")
        extra_font_size = 40
        self.extra_font = backend.addExtraFont(
            extra_font_path, extra_font_size)

        self.show_custom_window = True

    def drawGUI(self):
        super().drawGUI()
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
