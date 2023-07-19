from __future__ import annotations
from . import widgets
import imgui


def mapRange(value, inMin, inMax, outMin, outMax):
    return outMin + (((value - inMin) / (inMax - inMin)) * (outMax - outMin))


class MyCustomHealthBarWindow(widgets.GUIWindow):

    def __init__(self, name: str, io: imgui._IO, width: int, height: int) -> None:
        flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_TITLE_BAR
        flags |= imgui.WINDOW_NO_RESIZE
        flags |= imgui.WINDOW_ALWAYS_AUTO_RESIZE
        flags |= imgui.WINDOW_NO_BACKGROUND
        super().__init__(name, io, False, flags)
        self.health: float = 0.0
        self.min: float = 0.0
        self.max: float = 1.0

        self.width = width
        self.height = height

    def drawWindow(self):
        display_size = self.io.display_size
        imgui.set_next_window_position(
            display_size.x * 0, display_size.y * 1, pivot_x=0, pivot_y=1)
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
