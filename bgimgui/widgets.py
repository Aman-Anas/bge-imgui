from .image import ImageHelper
import os
import imgui


class GUIWidget:
    def __init__(self) -> None:
        pass

    def draw(self):
        pass


def draw_bounding_rect():
    draw_list = imgui.get_window_draw_list()
    draw_list.add_rect(*imgui.get_item_rect_min(), *imgui.get_item_rect_max(),
                       imgui.get_color_u32_rgba(1, 1, 1, 1), thickness=2)


class ImageWidget(GUIWidget):
    def __init__(self, file: str, scale=(1, 1), rounding=None, flags=None, drawBoundRect=False) -> None:
        super().__init__()
        if not os.path.isfile(file):
            raise FileNotFoundError(
                "Could not find file specified at {file} path. Try using bge.logic.expandPath() to get the correct path")

        self.image = ImageHelper(file)
        self.drawBoundRect = drawBoundRect

        self.scale = scale
        self.rounding = rounding
        self.flags = flags

        # Not doing crops or weird ratios because in that case you might as well make an ImageHelper object
        # As it requires extra parameters

    def enableBoundingBox(self):
        self.drawBoundRect = True

    def disableBoundingBox(self):
        self.drawBoundRect = False

    def setScale(self, scaleX, scaleY):
        self.scale = (scaleX, scaleY)

    def setFlags(self, flags):
        self.flags = flags

    def setRounding(self, rounding):
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
        if self.drawBoundRect:
            draw_bounding_rect()


class GUIWindow:
    def __init__(self, name: str, closable: bool = True, flags=None) -> None:
        super().__init__()
        self.name = name
        self.closable = closable
        self.widgets: list[GUIWidget] = []
        if flags is None:
            self.flags = 0
        else:
            self.flags = flags

        self.show = True

    def show(self):
        self.show = True

    def hide(self):
        self.show = False

    def draw(self):
        is_expand, self.show = imgui.begin(
            self.name, closable=self.closable, flags=self.flags)
        if is_expand:
            self.drawWidgets()
        imgui.end()

    def drawWidgets(self):
        for widget in self.widgets:
            widget.draw()

    def addWidget(self, widget: GUIWidget):
        self.widgets.append(widget)
