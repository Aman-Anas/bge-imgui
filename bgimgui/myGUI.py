from .imguiWrapper import BGEImguiWrapper
from . import widgets
import bge
import imgui
import sys


class MyCustomGUI(BGEImguiWrapper):
    # Example class for how you would override and make your own GUI

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

        self.show_test_window = True
        self.show_custom_window = True

        # Add window objects
        coolWindow = widgets.GUIWindow("Cool Window")

        coolWindow.addWidget(widgets.ImageWidget(
            bge.logic.expandPath("//cursor.png"), rounding=5))

        self.addWindow(coolWindow)

        self.randomForegroundImage = widgets.ForegroundImage(
            bge.logic.expandPath("//cursor.png"), rounding=5)
        self.randomForegroundImage.setImagePosition(100, 50)

        self.randomBackgroundImage = widgets.BackgroundImage(
            bge.logic.expandPath("//cursor.png"))
        self.randomBackgroundImage.setImagePosition(500, 500)
        self.randomBackgroundImage.setScale(0.2, 0.2)

    def drawGUI(self):
        # Draw Menu Bar
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):

                clicked_quit, selected_quit = imgui.menu_item(
                    "Quit", "Cmd+Q", False, True
                )

                if clicked_quit:
                    sys.exit(0)

                imgui.end_menu()
            imgui.end_main_menu_bar()

        # Draws all of the added window objects
        super().drawGUI()

        # Can draw procedurally here too
        imgui.show_test_window()

        if self.show_custom_window:
            is_expand, self.show_custom_window = imgui.begin(
                "Custom window", True)
            if is_expand:
                imgui.text("Bar")
                imgui.text_colored("Eggs", 0.2, 1.0, 0.0)
            imgui.end()

        if self.show_test_window:
            expand, self.show_test_window = imgui.begin("Default Window", True)
            if expand:
                with imgui.font(self.extra_font):
                    imgui.text("Text displayed using custom font")
            imgui.end()

        self.randomForegroundImage.draw()
        self.randomBackgroundImage.draw()
