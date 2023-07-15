import dearpygui.dearpygui as dpg
from threading import Thread


class GameGUI:
    def __init__(self) -> None:
        # This line could maybe go in the thread too?
        dpg.create_context()

        self.gui_thread = Thread(target=self.guiThread)
        self.gui_thread.start()

    def guiThread(self):

        dpg.create_viewport(title='Custom Title', width=600,
                            height=200, clear_color=(0.0, 0.0, 0.0, 255.0))

        dpg.set_viewport_always_top(True)
        dpg.setup_dearpygui()

        with dpg.window(tag="Primary Window"):
            dpg.add_text("Hello, world")
            dpg.add_button(label="Save")
            dpg.add_input_text(label="string", default_value="Quick brown fox")
            dpg.add_slider_float(
                label="float", default_value=0.273, max_value=1)

        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)

        dpg.start_dearpygui()
        dpg.destroy_context()

    def run(self):
        pass
        # Update stuff I guess
