from __future__ import annotations
from .bgimgui import widgets
from imgui_bundle import imgui
import bge


def mapRange(value, inMin, inMax, outMin, outMax):
    return outMin + (((value - inMin) / (inMax - inMin)) * (outMax - outMin))


class MyCustomHealthBarWindow(widgets.GUIWindow):

    def __init__(self, name: str, io: imgui.IO, width: int, height: int) -> None:
        flags = imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_title_bar
        flags |= imgui.WindowFlags_.no_resize
        flags |= imgui.WindowFlags_.always_auto_resize
        flags |= imgui.WindowFlags_.no_background
        super().__init__(name, io, False, flags)
        self.health: float = 0.0
        self.min: float = 0.0
        self.max: float = 1.0

        self.width = width
        self.height = height

    def draw_window(self):
        display_size = self.io.display_size
        imgui.set_next_window_pos(
            (display_size.x * 0, display_size.y * 1), pivot=(0, 1))
        super().draw_window()

    def draw_contents(self):
        corrected_hp = mapRange(self.health, self.min, self.max, 0, 1)
        imgui.progress_bar(corrected_hp, (self.width, self.height), self.name)
        imgui.progress_bar(
            corrected_hp/2, (self.width, self.height), f"{self.name}2")
        imgui.progress_bar(
            corrected_hp/4, (self.width, self.height), f"{self.name}3")

    def setHealth(self, health: float):
        self.health = health

    def setLimits(self, min_health, max_health):
        self.min = min_health
        self.max = max_health


class MyTextWindow(widgets.GUIWindow):
    def __init__(self, name: str, io: imgui.IO, closable: bool = True, flags=None) -> None:
        super().__init__(name, io, closable, flags)

    def draw_window(self):
        pass  # Nothing specific
        super().draw_window()

    def draw_contents(self):
        imgui.text_colored(imgui.ImColor(1, 0.7, 0.7).value,
                           "Wow! This is a text box. Colored orange.")
        modal = imgui.button("open")
        if modal:
            imgui.open_popup("wao")

        is_expand, _, = imgui.begin_popup_modal("wao", True)
        if is_expand:
            imgui.text("hi")
            imgui.end_popup()


class SettingsWindow(widgets.GUIWindow):

    START_DEBUG = True

    def __init__(self, io: imgui._IO, closable: bool = True, flags=None) -> None:
        super().__init__("Settings", io, closable, flags)

        self.show_debug = SettingsWindow.START_DEBUG

        self.update_values()

    def update_values(self):
        self.resolution = [bge.render.getWindowWidth(),
                           bge.render.getWindowHeight()]
        self.fullscreen = bge.render.getFullScreen()

        self.max_logic_frame = bge.logic.getMaxLogicFrame()
        self.logic_tick_rate = bge.logic.getLogicTicRate()

        self.vsync_options = ["VSYNC OFF", "VSYNC ADAPTIVE", "VSYNC ON"]
        self.vsync_enums = [bge.render.VSYNC_OFF,
                            bge.render.VSYNC_ADAPTIVE, bge.render.VSYNC_ON]

        self.vsync = bge.render.getVsync()
        self.vsync_opt_index = self.vsync_enums.index(self.vsync)

    def draw_contents(self):
        if imgui.begin_tab_bar("SettingsTabs"):
            general, _ = imgui.begin_tab_item("General")
            if general:
                self.general_settings()
                imgui.end_tab_item()

            other, _ = imgui.begin_tab_item("Other")
            if other:
                imgui.text("hi")
                imgui.end_tab_item()

            imgui.end_tab_bar()

    def general_settings(self):
        refresh = imgui.button("Refresh settings after window resize")

        imgui.separator()

        max_resolution = bge.render.getDisplayDimensions()
        imgui.text("Resolution")
        imgui.text(
            f"Detected max display resolution: {max_resolution}")
        _, self.resolution = imgui.input_int2(
            "##resolution", self.resolution)

        imgui.text("Fullscreen: ")
        imgui.same_line()
        _, self.fullscreen = imgui.checkbox("##fullscreen", self.fullscreen)

        imgui.separator()

        imgui.text("Logic Tick Rate (FPS)")
        _, self.logic_tick_rate = imgui.input_float(
            "##logicTickRate", self.logic_tick_rate)

        imgui.text("V-Sync setting")
        _, self.vsync_opt_index = imgui.combo(
            "##Vsyncsetting", self.vsync_opt_index, self.vsync_options)

        imgui.text("Maximum Logic Frames per second")
        _, self.max_logic_frame = imgui.input_int(
            "##maxLogicFrames", self.max_logic_frame)

        imgui.separator()

        imgui.text("Show debug info: ")
        imgui.same_line()
        _, self.show_debug = imgui.checkbox("##debugInfo", self.show_debug)

        apply = imgui.button("Apply settings!", (-1, 0))

        if apply:
            bge.logic.setMaxLogicFrame(self.max_logic_frame)
            bge.logic.setLogicTicRate(self.logic_tick_rate)
            bge.render.setFullScreen(self.fullscreen)
            bge.render.setWindowSize(*self.resolution)

            bge.render.showFramerate(self.show_debug)
            bge.render.showProfile(self.show_debug)
            bge.render.showProperties(self.show_debug)

            bge.render.setVsync(self.vsync_enums[self.vsync_opt_index])

        if refresh:
            self.update_values()
