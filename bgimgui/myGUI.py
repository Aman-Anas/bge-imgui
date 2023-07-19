from .imguiWrapper import BGEImguiWrapper
from . import widgets
from .myCustomWindows import MyCustomHealthBarWindow
import bge
import imgui
import sys


class MyCustomGUI(BGEImguiWrapper):
    # Example class for how you would override and make your own GUI

    def styleGUI(self):
        pass
        # Example for how to style GUI
        # style = imgui.get_style() # override active style
        # imgui.style_colors_dark(style) # optional: set base colors from "Dark" (or any other) style
        # # set red, green, blue and alpha color components for style colors you wanna change
        # style.colors[imgui.COLOR_BORDER] = (r, g, b, a)
        # style.colors[imgui.COLOR_TITLE_BACKGROUND] = (r, g, b, a)
        # style.colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = (r, g, b, a)

    def initializeGUI(self):
        super().initializeGUI()
        io = imgui.get_io()

        # allow user to navigate UI with a keyboard
        io.config_flags |= imgui.CONFIG_NAV_ENABLE_KEYBOARD

        self.styleGUI()

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
        coolWindow = MyCustomHealthBarWindow("Cool Health Bar", io, 1000, 20)

        self.addWindow(coolWindow)

        self.randomForegroundImage = widgets.ForegroundImage(
            bge.logic.expandPath("//cursor.png"), rounding=5)
        self.randomForegroundImage.setImagePosition(100, 50)

        self.randomBackgroundImage = widgets.BackgroundImage(
            bge.logic.expandPath("//cursor.png"))
        self.randomBackgroundImage.setImagePosition(500, 500)
        self.randomBackgroundImage.setScale(0.2, 0.2)

    def drawGUI(self):
        backend = self.imgui_backend

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

        screenWidth, screenHeight = backend.getScreenSize()

        # Can draw procedurally here too
        imgui.show_test_window()

        if self.show_custom_window:

            # Force set a window position
            # Pivot allows to modify the "center" position on the window
            # Where x=0 is the left and x=1 is the right
            imgui.set_next_window_position(
                screenWidth, screenHeight * 0.5, pivot_x=1, pivot_y=0.5)

            is_expand, self.show_custom_window = imgui.begin(
                "Custom window", True, flags=imgui.WINDOW_NO_MOVE | imgui.WINDOW_ALWAYS_AUTO_RESIZE | imgui.WINDOW_NO_TITLE_BAR)
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
