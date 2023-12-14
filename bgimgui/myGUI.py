from .imguiWrapper import BGEImguiWrapper
from . import widgets
from .myCustomWindows import MyCustomHealthBarWindow, MyTextWindow
import bge
from imgui_bundle import imgui
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

        # You can also read in a file containing a saved style dict

    def initializeGUI(self):
        super().initializeGUI()
        io = imgui.get_io()

        # allow user to navigate UI with a keyboard
        io.config_flags |= imgui.ConfigFlags_.nav_enable_keyboard

        self.styleGUI()

        backend = self.imgui_backend

        # Set font global scaling factor to 2 for high res displays? (like retina)
        font_global_scaling_factor = 1
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

        # Add window objects via addWindowToRender() like a retained mode GUI
        coolWindow = MyCustomHealthBarWindow("Cool Health Bar", io, 1000, 20)
        self.addWindowToRender(coolWindow)

        # Alternately, store them in the GUI and just render as necessary (Recommended method)
        self.myTextWindow = MyTextWindow("potato", io)

        self.randomForegroundImage = widgets.ForegroundImage(
            bge.logic.expandPath("//cursors/arrow.png"), rounding=5)
        self.randomForegroundImage.setImagePosition(100, 50)

        self.randomBackgroundImage = widgets.BackgroundImage(
            bge.logic.expandPath("//cursors/resize.png"))
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

        # Draws all of the added window objects (somewhat like a retained mode)
        super().drawGUI()

        # Draw a stored window
        # You can also put this function call in a match-case statement to have one GUI
        # with multiple modes (like LoginScreen, ConnectScreen, MainGame, etc)
        # Or even use objects in a finite state machine
        self.myTextWindow.drawWindow()

        screenWidth, screenHeight = backend.getScreenSize()

        # Can draw windows procedurally here too (without any wrapper objects for windows)
        imgui.show_demo_window()

        if self.show_custom_window:

            # Force set a window position
            # Pivot allows to modify the "center" position on the window
            # Where x=0 is the left and x=1 is the right
            imgui.set_next_window_pos(
                imgui.ImVec2(screenWidth, screenHeight * 0.5), pivot=imgui.ImVec2(1, 0.5))

            is_expand, self.show_custom_window = imgui.begin(
                "Custom window", True, flags=imgui.WindowFlags_.no_move | imgui.WindowFlags_.always_auto_resize | imgui.WindowFlags_.no_title_bar)
            if is_expand:
                imgui.text("Bar")
                imgui.text_colored(imgui.ImColor(0.2, 1.0, 0.0).value, "Eggs")
            imgui.end()

        if self.show_test_window:
            expand, self.show_test_window = imgui.begin("Default Window", True)
            if expand:
                imgui.push_font(self.extra_font)
                imgui.text("Text displayed using custom font")
                imgui.pop_font()
            imgui.end()

        self.randomForegroundImage.draw()
        self.randomBackgroundImage.draw()
