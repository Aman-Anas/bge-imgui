from imgui_bundle import imgui

from bge.types import KX_Scene
import bge.logic

from .renderer import BGEImguiRenderer


class BGEImguiWrapper:
    def __init__(self, scene: KX_Scene, cursor_path=None) -> None:
        bge.logic.gui = self
        self.context = imgui.create_context()
        self.backend = BGEImguiRenderer(scene, cursor_path=cursor_path)

        self.io = self.backend.io
        self.io.config_flags |= imgui.ConfigFlags_.docking_enable

        self.setup_gui()

    def setup_gui(self) -> None:
        # For child classes to override
        raise NotImplementedError

    def draw(self) -> None:
        # For child classes to override
        raise NotImplementedError

    def update_gui(self):
        backend = self.backend

        # Update inputs like mouse/keyboard
        backend.update_io()

        imgui.new_frame()

        self.draw()

        backend.draw_cursor()

        imgui.end_frame()

        imgui.render()
        backend.render(imgui.get_draw_data())

    def shutdown_gui(self):
        self.backend.shutdown()
