from __future__ import annotations
from .image import ImageHelper, ForegroundImageHelper, BackgroundImageHelper
import os
from imgui_bundle import imgui
import bge.logic


def draw_bounding_rect():
    draw_list = imgui.get_window_draw_list()
    draw_list.add_rect(*imgui.get_item_rect_min(), *imgui.get_item_rect_max(),
                       imgui.get_color_u32(imgui.ImVec4(1, 1, 1, 1)), thickness=2)


class ImageWidget:
    def __init__(self, file: str, scale=(1, 1), rounding=None, flags=None, draw_bound_rect=False, ImageClass=ImageHelper) -> None:
        super().__init__()
        if not os.path.isfile(file):
            raise FileNotFoundError(
                "Could not find file specified at {file} path. Try using bge.logic.expandPath() to get the correct path")

        self.image = ImageClass(file)
        self.draw_bound_rect = draw_bound_rect

        self.scale = scale
        self.rounding = rounding
        self.flags = flags

        # Not doing crops or weird ratios because in that case you might as well make an ImageHelper object
        # As it requires extra parameters

    def enable_bounding_box(self):
        self.draw_bound_rect = True

    def disable_bounding_box(self):
        self.draw_bound_rect = False

    def set_scale(self, scaleX, scaleY):
        self.scale = (scaleX, scaleY)

    def set_flags(self, flags):
        self.flags = flags

    def set_rounding(self, rounding):
        self.rounding = rounding

    def draw(self):
        scaled_width = self.image.width * self.scale[0]
        scaled_height = self.image.height * self.scale[1]
        kwargs = {}
        args = ()

        if self.rounding is not None:
            kwargs["rounding"] = self.rounding
        if self.flags is not None:
            kwargs["flags"] = self.flags

        self.image.render(scaled_width, scaled_height, *args, **kwargs)
        if self.draw_bound_rect:
            draw_bounding_rect()


class ForegroundImage(ImageWidget):
    def __init__(self, file: str, scale=(1, 1), rounding=None, flags=None, drawBoundRect=False) -> None:
        super().__init__(file, scale, rounding, flags,
                         drawBoundRect, ImageClass=ForegroundImageHelper)
        self.window = None

    def set_image_position(self, x, y):
        self.image.setImagePosition(x, y)

    def attach_to_window(self, window: GUIWindow):
        self.window = window

    def detach_window(self):
        self.window = None

    def draw(self):
        if self.window is not None:
            pos = imgui.get_cursor_screen_pos()
            self.image.image_position = (pos.x, pos.y)
        super().draw()


class BackgroundImage(ImageWidget):
    def __init__(self, file: str, scale=(1, 1), rounding=None, flags=None, drawBoundRect=False) -> None:
        super().__init__(file, scale, rounding, flags,
                         drawBoundRect, ImageClass=BackgroundImageHelper)
        self.window = None

    def set_image_position(self, x, y):
        self.image.setImagePosition(x, y)

    def attach_to_window(self, window: GUIWindow):
        self.window = window

    def detach_window(self):
        self.window = None

    def draw(self):
        if self.window is not None:
            pos = imgui.get_cursor_screen_pos()
            self.image.image_position = (pos.x, pos.y)
        super().draw()


class GUIWindow:
    def __init__(self, name: str, io: imgui.IO, closable: bool = True, flags=None) -> None:
        super().__init__()
        self.name = name
        self.closable = closable
        self.io = io

        if flags is None:
            self.flags = 0
        else:
            self.flags = flags

        self.show = True

    def show(self):
        self.show = True

    def hide(self):
        self.show = False

    def draw_window(self):
        if self.show:
            if self.closable:
                is_expand, self.show = imgui.begin(
                    self.name, True, flags=self.flags)
            else:
                is_expand, _ = imgui.begin(
                    self.name, None, flags=self.flags)

            if is_expand:
                self.draw_contents()
            imgui.end()

    def draw_contents(self):
        pass
