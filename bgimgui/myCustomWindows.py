from __future__ import annotations
from . import widgets
from imgui_bundle import imgui


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

    def drawWindow(self):
        display_size = self.io.display_size
        imgui.set_next_window_pos(
            (display_size.x * 0, display_size.y * 1), pivot=(0, 1))
        super().drawWindow()

    def drawContents(self):
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

    def drawWindow(self):
        pass  # Nothing specific
        super().drawWindow()

    def drawContents(self):
        imgui.text_colored(imgui.ImColor(1, 0.7, 0.7).value,
                           "Wow! This is a text box. Colored orange.")
