from . import bgimgui
from imgui_bundle import imgui

from .my_windows import MyCustomHealthBarWindow, MyTextWindow, SettingsWindow


class SimpleCustomGUI(bgimgui.BGEImguiWrapper):
    # Simpler example class for how you would override and make your own GUI

    def setup_gui(self):
        io = imgui.get_io()

        # Allow user to navigate UI with a keyboard
        io.config_flags |= imgui.ConfigFlags_.nav_enable_keyboard

        # > This is how you would load a GUI style
        # bgimgui.style_gui_from_file(bge.logic.expandPath("//ui_style.toml"))

        # > This is how you would set a main font file
        # main_font_path = bge.logic.expandPath(
        #     "//Orbitron-VariableFont_wght.ttf")
        # main_font_size_in_pixels = 20
        # backend.set_main_font(main_font_path, main_font_size_in_pixels)

        # Make windows like this
        self.my_text_window = MyTextWindow("potato", io)
        self.hp_bar = MyCustomHealthBarWindow("Cool bar", io, 500, 20)
        self.settings_window = SettingsWindow(io)

    def draw(self):
        # Draw a stored window
        # You can also put this function call in a match-case statement to have one GUI
        # with multiple modes (like LoginScreen, ConnectScreen, MainGame, etc)
        # Or even use objects in a finite state machine
        self.my_text_window.draw_window()
        self.hp_bar.draw_window()
        self.settings_window.draw_window()

        # Can draw windows procedurally here too (without any wrapper objects for windows)
        imgui.show_demo_window()
