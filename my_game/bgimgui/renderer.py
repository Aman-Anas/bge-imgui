from __future__ import annotations
from bge.types import KX_Scene
import bge.logic

import ctypes
import glob
import os
import pathlib

import OpenGL
# ENABLE ERROR CHECKING IF YOU NEED TO DEBUG SHADER ISSUES
OpenGL.ERROR_CHECKING = False

if True:
    from OpenGL import GL as gl
    from PIL import Image
    import numpy as np

    from imgui_bundle.python_backends.base_backend import BaseOpenGLRenderer
    from imgui_bundle import imgui


class BGEPipelineRenderer(BaseOpenGLRenderer):
    """Basic OpenGL integration base class."""
    VERTEX_SHADER_SRC = """
    #version 330

    uniform mat4 ProjMtx;
    in vec2 Position;
    in vec2 UV;
    in vec4 Color;
    out vec2 Frag_UV;
    out vec4 Frag_Color;

    void main() {
        Frag_UV = UV;
        Frag_Color = Color;

        gl_Position = ProjMtx * vec4(Position.xy, 0, 1);
    }
    """

    FRAGMENT_SHADER_SRC = """
    #version 330

    uniform sampler2D Texture;
    in vec2 Frag_UV;
    in vec4 Frag_Color;
    out vec4 Out_Color;

    void main() {
        Out_Color = Frag_Color * texture(Texture, Frag_UV.st);
    }
    """

    def __init__(self, scene: KX_Scene, main=True,
                 panel: bge.types.KX_GameObject | None = None,
                 resolution: tuple[int, int] | None = None):
        self._shader_handle = None
        self._vert_handle = None
        self._fragment_handle = None
        self.scene = scene

        self._attrib_location_tex = None
        self._attrib_proj_mtx = None
        self._attrib_location_position = None
        self._attrib_location_uv = None
        self._attrib_location_color = None

        self._vbo_handle = None
        self._elements_handle = None
        self._vao_handle = None
        self.data = None

        self.main = main
        if not main:
            if panel is None:
                bge.logic.endGame()
                raise ValueError(
                    "Pass a panel game object for non-main UI viewport")

            if resolution is None:
                bge.logic.endGame()
                raise ValueError(
                    "Pass a resolution tuple for non-main UI viewport")
            self.panel = panel
            texture = bge.texture.Texture(panel, 0, 0)

            # Initialize the texture
            data = bge.texture.ImageViewport()
            data.capsize = [resolution[0], resolution[1]]
            texture.source = data

            # Save the bind ID and resolution for the FBO later
            self.bind_id = texture.bindId
            self.tex_resolution = resolution
            self.fbo_texture = texture

            # Refresh texture once to apply changes
            self.fbo_texture.refresh(False)

        super(BGEPipelineRenderer, self).__init__()
        self.scene.post_draw.append(self.render_call)

        if self.main:
            width, height = bge.render.getWindowWidth(), bge.render.getWindowHeight()
        else:
            width, height = self.tex_resolution

        self.saved_disp_size = width, height
        self.io.display_size = width, height

    def refresh_font_texture(self):
        # save texture state
        last_texture = gl.glGetIntegerv(gl.GL_TEXTURE_BINDING_2D)

        # width, height, pixels = self.io.fonts.get_tex_data_as_rgba32()
        font_matrix: np.ndarray = self.io.fonts.get_tex_data_as_rgba32()
        width = font_matrix.shape[1]
        height = font_matrix.shape[0]
        pixels = font_matrix.data

        if self._font_texture is not None:
            gl.glDeleteTextures([self._font_texture])

        self._font_texture = gl.glGenTextures(1)

        gl.glBindTexture(gl.GL_TEXTURE_2D, self._font_texture)
        gl.glTexParameteri(
            gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(
            gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            width,
            height,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            pixels,
        )

        self.io.fonts.tex_id = self._font_texture
        gl.glBindTexture(gl.GL_TEXTURE_2D, last_texture)
        self.io.fonts.clear_tex_data()

    def _create_device_objects(self):
        # save state
        last_texture = gl.glGetIntegerv(gl.GL_TEXTURE_BINDING_2D)
        last_array_buffer = gl.glGetIntegerv(gl.GL_ARRAY_BUFFER_BINDING)

        last_fbo = gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING)

        last_vertex_array = gl.glGetIntegerv(gl.GL_VERTEX_ARRAY_BINDING)

        self._shader_handle = gl.glCreateProgram()
        # note: no need to store shader parts handles after linking
        vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)

        gl.glShaderSource(vertex_shader, self.VERTEX_SHADER_SRC)
        gl.glShaderSource(fragment_shader, self.FRAGMENT_SHADER_SRC)
        gl.glCompileShader(vertex_shader)
        gl.glCompileShader(fragment_shader)

        gl.glAttachShader(self._shader_handle, vertex_shader)
        gl.glAttachShader(self._shader_handle, fragment_shader)

        gl.glLinkProgram(self._shader_handle)

        # note: after linking shaders can be removed
        gl.glDeleteShader(vertex_shader)
        gl.glDeleteShader(fragment_shader)

        self._attrib_location_tex = gl.glGetUniformLocation(
            self._shader_handle, "Texture")
        self._attrib_proj_mtx = gl.glGetUniformLocation(
            self._shader_handle, "ProjMtx")
        self._attrib_location_position = gl.glGetAttribLocation(
            self._shader_handle, "Position")
        self._attrib_location_uv = gl.glGetAttribLocation(
            self._shader_handle, "UV")
        self._attrib_location_color = gl.glGetAttribLocation(
            self._shader_handle, "Color")

        self._vbo_handle = gl.glGenBuffers(1)
        self._elements_handle = gl.glGenBuffers(1)

        self._vao_handle = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self._vao_handle)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo_handle)

        gl.glEnableVertexAttribArray(self._attrib_location_position)
        gl.glEnableVertexAttribArray(self._attrib_location_uv)
        gl.glEnableVertexAttribArray(self._attrib_location_color)

        gl.glVertexAttribPointer(self._attrib_location_position, 2, gl.GL_FLOAT, gl.GL_FALSE,
                                 imgui.VERTEX_SIZE, ctypes.c_void_p(imgui.VERTEX_BUFFER_POS_OFFSET))
        gl.glVertexAttribPointer(self._attrib_location_uv, 2, gl.GL_FLOAT, gl.GL_FALSE,
                                 imgui.VERTEX_SIZE, ctypes.c_void_p(imgui.VERTEX_BUFFER_UV_OFFSET))
        gl.glVertexAttribPointer(self._attrib_location_color, 4, gl.GL_UNSIGNED_BYTE,
                                 gl.GL_TRUE, imgui.VERTEX_SIZE, ctypes.c_void_p(imgui.VERTEX_BUFFER_COL_OFFSET))

        # If not main render, use the FBO
        if not self.main:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.bind_id)

            width, height = self.tex_resolution

            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width,
                            height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
            gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
            gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)

            self.frame_buffer = gl.glGenFramebuffers(1)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.frame_buffer)

            gl.glFramebufferTexture2D(
                gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.bind_id, 0)
            gl.glDrawBuffer(gl.GL_COLOR_ATTACHMENT0)

        # restore state
        gl.glBindTexture(gl.GL_TEXTURE_2D, last_texture)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, last_array_buffer)
        gl.glBindVertexArray(last_vertex_array)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, last_fbo)

    def render(self, draw_data):
        # Since we are rendering in the post_draw callback, simply update the draw data
        self.data = draw_data

    def render_call(self):
        if self.data is None:
            return

        draw_data = self.data

        # perf: local for faster access
        io = self.io

        display_width, display_height = io.display_size
        fb_width = int(display_width * io.display_framebuffer_scale[0])
        fb_height = int(display_height * io.display_framebuffer_scale[1])

        if fb_width == 0 or fb_height == 0:
            return

        draw_data.scale_clip_rects(io.display_framebuffer_scale)

        # backup GL state
        # todo: provide cleaner version of this backup-restore code
        common_gl_state_tuple = get_common_gl_state()
        last_program = gl.glGetIntegerv(gl.GL_CURRENT_PROGRAM)
        last_active_texture = gl.glGetIntegerv(gl.GL_ACTIVE_TEXTURE)
        last_array_buffer = gl.glGetIntegerv(gl.GL_ARRAY_BUFFER_BINDING)
        last_element_array_buffer = gl.glGetIntegerv(
            gl.GL_ELEMENT_ARRAY_BUFFER_BINDING)
        last_vertex_array = gl.glGetIntegerv(gl.GL_VERTEX_ARRAY_BINDING)

        last_fbo = gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING)

        if not self.main:
            gl.glDisable(gl.GL_SCISSOR_TEST)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.frame_buffer)

            # Clears any color information in the FBO, makes transparent background
            gl.glClearColor(0.0, 0.0, 0.0, 0.0)

            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendEquation(gl.GL_FUNC_ADD)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        gl.glViewport(0, 0, int(fb_width), int(fb_height))

        ortho_projection = (ctypes.c_float * 16)(
            2.0 / display_width, 0.0,                    0.0, 0.0,
            0.0,                2.0 / -display_height,  0.0, 0.0,
            0.0,                0.0,                   -1.0, 0.0,
            -1.0,                1.0,                    0.0, 1.0,
        )

        gl.glUseProgram(self._shader_handle)
        gl.glUniform1i(self._attrib_location_tex, 0)
        gl.glUniformMatrix4fv(self._attrib_proj_mtx, 1,
                              gl.GL_FALSE, ortho_projection)

        gl.glBindVertexArray(self._vao_handle)

        for commands in draw_data.cmd_lists:

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo_handle)
            # todo: check this (sizes)
            gl.glBufferData(
                gl.GL_ARRAY_BUFFER,
                commands.vtx_buffer.size() * imgui.VERTEX_SIZE,
                ctypes.c_void_p(commands.vtx_buffer.data_address()),
                gl.GL_STREAM_DRAW,
            )

            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self._elements_handle)
            # todo: check this (sizes)
            gl.glBufferData(
                gl.GL_ELEMENT_ARRAY_BUFFER,
                commands.idx_buffer.size() * imgui.INDEX_SIZE,
                ctypes.c_void_p(commands.idx_buffer.data_address()),
                gl.GL_STREAM_DRAW,
            )

            # todo: allow to iterate over _CmdList
            for command in commands.cmd_buffer:
                gl.glBindTexture(gl.GL_TEXTURE_2D, command.texture_id)

                # todo: use named tuple
                x, y, z, w = command.clip_rect
                gl.glScissor(int(x), int(fb_height - w),
                             int(z - x), int(w - y))

                if imgui.INDEX_SIZE == 2:
                    gltype = gl.GL_UNSIGNED_SHORT
                else:
                    gltype = gl.GL_UNSIGNED_INT

                gl.glDrawElements(
                    gl.GL_TRIANGLES,
                    command.elem_count,
                    gltype,
                    ctypes.c_void_p(command.idx_offset * imgui.INDEX_SIZE)
                )

        if not self.main:
            # Fix for UPBGE depsgraph
            self.panel.worldPosition.x += 0.01
            self.panel.worldPosition.x -= 0.01

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, last_fbo)

        # restore modified GL state
        restore_common_gl_state(common_gl_state_tuple)
        gl.glUseProgram(last_program)
        gl.glActiveTexture(last_active_texture)
        gl.glBindVertexArray(last_vertex_array)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, last_array_buffer)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, last_element_array_buffer)

    def _invalidate_device_objects(self):
        if self._vao_handle > -1:
            gl.glDeleteVertexArrays(1, [self._vao_handle])
        if self._vbo_handle > -1:
            gl.glDeleteBuffers(1, [self._vbo_handle])
        if self._elements_handle > -1:
            gl.glDeleteBuffers(1, [self._elements_handle])
        self._vao_handle = self._vbo_handle = self._elements_handle = 0

        gl.glDeleteProgram(self._shader_handle)
        self._shader_handle = 0

        if self._font_texture > -1:
            gl.glDeleteTextures([self._font_texture])
        self.io.fonts.tex_id = 0
        self._font_texture = 0


BGE_KEY_EVENT_MAP = {
    bge.events.TABKEY: imgui.Key.tab,
    bge.events.LEFTARROWKEY: imgui.Key.left_arrow,
    bge.events.RIGHTARROWKEY: imgui.Key.right_arrow,
    bge.events.UPARROWKEY: imgui.Key.up_arrow,
    bge.events.DOWNARROWKEY: imgui.Key.down_arrow,
    bge.events.PAGEUPKEY: imgui.Key.page_up,
    bge.events.PAGEDOWNKEY: imgui.Key.page_down,
    bge.events.HOMEKEY: imgui.Key.home,
    bge.events.ENDKEY: imgui.Key.end,
    bge.events.INSERTKEY: imgui.Key.insert,
    bge.events.DELKEY: imgui.Key.delete,
    bge.events.BACKSPACEKEY: imgui.Key.backspace,
    bge.events.SPACEKEY: imgui.Key.space,
    bge.events.ENTERKEY: imgui.Key.enter,
    bge.events.ESCKEY: imgui.Key.escape,
    bge.events.AKEY: imgui.Key.a,
    bge.events.CKEY: imgui.Key.c,
    bge.events.VKEY: imgui.Key.v,
    bge.events.XKEY: imgui.Key.x,
    bge.events.YKEY: imgui.Key.y,
    bge.events.ZKEY: imgui.Key.z,

    # Modifiers
    bge.events.LEFTCTRLKEY: imgui.Key.left_ctrl,
    bge.events.RIGHTCTRLKEY: imgui.Key.right_ctrl,
    bge.events.LEFTALTKEY: imgui.Key.left_alt,
    bge.events.RIGHTALTKEY: imgui.Key.right_alt,
    bge.events.LEFTSHIFTKEY: imgui.Key.left_shift,
    bge.events.RIGHTSHIFTKEY: imgui.Key.right_shift,
}

BGE_MODIFIER_EVENT_MAP = {
    bge.events.LEFTCTRLKEY: imgui.Key.im_gui_mod_ctrl,
    bge.events.RIGHTCTRLKEY: imgui.Key.im_gui_mod_ctrl,
    bge.events.LEFTALTKEY: imgui.Key.im_gui_mod_alt,
    bge.events.RIGHTALTKEY: imgui.Key.im_gui_mod_alt,
    bge.events.LEFTSHIFTKEY: imgui.Key.im_gui_mod_shift,
    bge.events.RIGHTSHIFTKEY: imgui.Key.im_gui_mod_shift,
}


class BGEImguiRenderer(BGEPipelineRenderer):

    INTERACTION_DIST = 100
    JUST_RAYCASTED = False
    CAST_DATA = (None, None, None)

    def __init__(self, scene, cursor_path=None, main=True,
                 panel: bge.types.KX_GameObject | None = None,
                 resolution: tuple[int, int] | None = None):
        self.scene = scene
        super().__init__(scene, main, panel, resolution)

        if panel:
            self.context_id = int(panel["imgui_panel"])

        self.io.backend_flags |= imgui.BackendFlags_.has_set_mouse_pos

        self.mouse = bge.logic.mouse
        self.keyboard = bge.logic.keyboard

        self.cursor_renderer = CursorRenderer(scene)

        if not cursor_path:
            self.show_cursor = False
        else:
            self.cursor_renderer.add_cursors(cursor_path)
            self.io.backend_flags |= imgui.BackendFlags_.has_mouse_cursors
            self.show_cursor = True

        self.accept_input = True
        self.font_scaling_factor = 1

        # Check for RanGE so deltaTime can be updated
        if hasattr(bge.logic, "deltaTime"):
            self.useDeltaTime = True
        else:
            self.useDeltaTime = False

        self._map_keys()

    def get_screen_size(self):
        return self.saved_disp_size

    def set_cursor_visible(self, show: bool):
        self.show_cursor = show

    def _map_keys(self):
        self.key_map = BGE_KEY_EVENT_MAP.copy()
        self.modifier_map = BGE_MODIFIER_EVENT_MAP.copy()
        self.active_modifiers = set()

    def update_screen_size(self):
        if not self.main:
            return

        width = bge.render.getWindowWidth()
        height = bge.render.getWindowHeight()
        refreshSize = False

        if self.saved_disp_size[0] != width:
            refreshSize = True
        elif self.saved_disp_size[1] != height:
            refreshSize = True

        if refreshSize:
            self.saved_disp_size = width, height
            self.io.display_size = width, height

    def update_io(self):
        io = self.io

        self.update_screen_size()

        # # Only accept user input if this flag true
        if self.accept_input:
            self.update_mouse_pos(io)
            self.update_mouse_btns(io)
            self.update_keyboard(io)

    def camera_raycast(self, camera, mouse):
        # Weird fix for raycasting from camera
        parent = None
        if camera.parent is not None:
            parent = camera.parent
            camera.removeParent()

        direction_vec = camera.worldPosition - \
            camera.getScreenVect(*mouse.position)

        data = camera.rayCast(
            direction_vec,
            prop="imgui_panel",
            dist=BGEImguiRenderer.INTERACTION_DIST
        )

        if parent:
            camera.setParent(parent)

        BGEImguiRenderer.JUST_RAYCASTED = True
        BGEImguiRenderer.CAST_DATA = data
        return data

    def render_call(self):
        # Override render call for camera raycast
        super().render_call()
        BGEImguiRenderer.JUST_RAYCASTED = False

    def update_mouse_pos(self, io: imgui.IO):
        mouse = self.mouse

        if io.want_set_mouse_pos:
            mouse.position = (io.mouse_pos.x / self.io.display_size.x,
                              io.mouse_pos.y / self.io.display_size.y)
            return

        if self.main:
            x, y = ((mouse.position[0] * self.io.display_size[0]),
                    (mouse.position[1] * self.io.display_size[1]))
        else:

            # This is to ensure with multiple panels, you only raycast once
            # per frame. Might not be worth the performance increase though,
            # need to test more.
            if BGEImguiRenderer.JUST_RAYCASTED:
                hit_obj, point, _ = BGEImguiRenderer.CAST_DATA

            else:
                hit_obj, point, _ = self.camera_raycast(
                    self.scene.active_camera, mouse)

            if hit_obj and (hit_obj["imgui_panel"] == self.context_id):
                hit_obj: bge.types.KX_GameObject

                scale = hit_obj.localScale

                dist, _, mouse_vec = hit_obj.getVectTo(point)
                mouse_vec.magnitude *= dist
                # Adjust scaling
                mouse_vec.x /= scale.x
                mouse_vec.y /= scale.y
                # Reverse Y direction
                mouse_vec.y *= -1
                # Correct Translation
                mouse_vec.x += 1
                mouse_vec.y += 1
                mouse_vec.x /= 2
                mouse_vec.y /= 2

                x, y = ((mouse_vec.x * self.io.display_size[0]),
                        (mouse_vec.y * self.io.display_size[1]))

            else:
                x, y = -imgui.FLT_MAX, -imgui.FLT_MAX

        io.add_mouse_pos_event(x, y)
        self.cursor_renderer.update_position(x, y)

    def update_mouse_btns(self, io: imgui.IO):
        mouse = self.mouse

        active_btns = mouse.activeInputs

        io.add_mouse_button_event(0, bge.events.LEFTMOUSE in active_btns)
        io.add_mouse_button_event(1, bge.events.RIGHTMOUSE in active_btns)

        io.add_mouse_button_event(2, bge.events.MIDDLEMOUSE in active_btns)

        if bge.events.WHEELUPMOUSE in active_btns:
            io.add_mouse_wheel_event(0, 0.5)
        elif bge.events.WHEELDOWNMOUSE in active_btns:
            io.add_mouse_wheel_event(0, -0.5)
        else:
            io.add_mouse_wheel_event(0, 0)

        if self.useDeltaTime:
            # Update deltatime in range, may not be necessary
            io.delta_time = bge.logic.deltaTime()

    def update_keyboard(self, io: imgui.IO):
        keyboard = self.keyboard
        active_keys = keyboard.activeInputs

        for key, event in self.key_map.items():
            io.add_key_event(event, key in active_keys)

        self.active_modifiers.clear()
        for key, event in self.modifier_map.items():
            if event not in self.active_modifiers:
                io.add_key_event(event, key in active_keys)
                self.active_modifiers.add(event)

        text = keyboard.text
        for character in text:
            io.add_input_character(ord(character))

    def set_scaling_factors(self, font_scaling_factor: int, screen_scaling_factor: int = 1):
        io = self.io

        # Use to make a font bigger than the 1:1 ratio, supposedly fixes issues with
        # high-res displays
        self.font_scaling_factor = font_scaling_factor

        scale = 1
        scale /= font_scaling_factor
        scale *= screen_scaling_factor
        io.font_global_scale = scale

    def set_main_font(self, path: str, font_size_in_pixels: int, *args, **kwargs):
        io = self.io

        io.fonts.clear()
        self.main_font = io.fonts.add_font_from_file_ttf(
            path, self.font_scaling_factor * font_size_in_pixels, *args, **kwargs)

        self.refresh_font_texture()

    def add_extra_font(self, path: str, font_size_in_pixels: int, *args, **kwargs):
        io = self.io
        newFont = io.fonts.add_font_from_file_ttf(
            path, self.font_scaling_factor * font_size_in_pixels, *args, **kwargs)
        self.refresh_font_texture()
        return newFont

    def draw_cursor(self):
        if self.show_cursor:
            self.cursor_renderer.draw_cursor()


def get_rgba_pixels(image: Image.Image):
    if image.mode == "RGB":
        return image.tobytes("raw", "RGBX")
    else:
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        return image.tobytes("raw", "RGBA")


class CursorRenderer:
    def __init__(self, scene: KX_Scene) -> None:
        self.scene = scene
        self.x = 0
        self.y = 0

        self.cursor_width = 25
        self.cursor_height = 25
        self.cursorDict = {}

    def set_size(self, width: int, height: int):
        self.cursor_width = width
        self.cursor_height = height

    def update_position(self, x: float, y: float):
        self.x = x
        self.y = y

    def add_cursors(self, file_path=None):
        if not file_path:
            file_path = bge.logic.expandPath("//cursors")

        cursor_list = glob.glob(file_path + '/**/*.png', recursive=True)

        self.cursorDict = {}

        for cursor_file in cursor_list:
            path = pathlib.Path(cursor_file)
            image = Image.open(path)
            width, height = image.size
            cursorPixels = get_rgba_pixels(image)

            fileName = os.path.basename(path)
            fileWithoutExtension = os.path.splitext(fileName)[0]

            texID = gl.glGenTextures(1)

            gl.glBindTexture(gl.GL_TEXTURE_2D, texID)
            gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_BORDER)
            gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_BORDER)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width,
                            height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, cursorPixels)
            image.close()
            self.cursorDict[fileWithoutExtension] = texID

    def draw_cursor(self):
        width = self.cursor_width
        height = self.cursor_height

        x = self.x
        y = self.y

        draw_list = imgui.get_foreground_draw_list()

        pos = x, y
        pos2 = (x + width, y + height)

        match imgui.get_mouse_cursor():
            case imgui.MouseCursor_.arrow:
                textureID = self.cursorDict["arrow"]
            case imgui.MouseCursor_.resize_nwse:
                textureID = self.cursorDict["resize"]
            case _:
                textureID = self.cursorDict["arrow"]

        draw_list.add_image(textureID, pos, pos2)


def get_common_gl_state():
    """
    Backups the current OpenGL state
    Returns a tuple of results for glGet / glIsEnabled calls
    NOTE: when adding more backuped state in the future,
    make sure to update function `restore_common_gl_state`
    """
    last_texture = gl.glGetIntegerv(gl.GL_TEXTURE_BINDING_2D)
    last_viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
    last_enable_blend = gl.glIsEnabled(gl.GL_BLEND)
    last_enable_cull_face = gl.glIsEnabled(gl.GL_CULL_FACE)
    last_enable_depth_test = gl.glIsEnabled(gl.GL_DEPTH_TEST)
    last_enable_scissor_test = gl.glIsEnabled(gl.GL_SCISSOR_TEST)
    last_scissor_box = gl.glGetIntegerv(gl.GL_SCISSOR_BOX)
    last_blend_src = gl.glGetIntegerv(gl.GL_BLEND_SRC)
    last_blend_dst = gl.glGetIntegerv(gl.GL_BLEND_DST)
    last_blend_equation_rgb = gl. glGetIntegerv(gl.GL_BLEND_EQUATION_RGB)
    last_blend_equation_alpha = gl.glGetIntegerv(gl.GL_BLEND_EQUATION_ALPHA)
    last_front_and_back_polygon_mode, _ = gl.glGetIntegerv(gl.GL_POLYGON_MODE)
    return (
        last_texture,
        last_viewport,
        last_enable_blend,
        last_enable_cull_face,
        last_enable_depth_test,
        last_enable_scissor_test,
        last_scissor_box,
        last_blend_src,
        last_blend_dst,
        last_blend_equation_rgb,
        last_blend_equation_alpha,
        last_front_and_back_polygon_mode,
    )


def restore_common_gl_state(common_gl_state_tuple):
    """
    Takes a tuple after calling function `get_common_gl_state`,
    to set the given OpenGL state back as it was before rendering the UI
    """
    (
        last_texture,
        last_viewport,
        last_enable_blend,
        last_enable_cull_face,
        last_enable_depth_test,
        last_enable_scissor_test,
        last_scissor_box,
        last_blend_src,
        last_blend_dst,
        last_blend_equation_rgb,
        last_blend_equation_alpha,
        last_front_and_back_polygon_mode,
    ) = common_gl_state_tuple

    gl.glBindTexture(gl.GL_TEXTURE_2D, last_texture)
    gl.glBlendEquationSeparate(
        last_blend_equation_rgb, last_blend_equation_alpha)
    gl.glBlendFunc(last_blend_src, last_blend_dst)

    gl.glPolygonMode(gl.GL_FRONT_AND_BACK, last_front_and_back_polygon_mode)

    if last_enable_blend:
        gl.glEnable(gl.GL_BLEND)
    else:
        gl.glDisable(gl.GL_BLEND)

    if last_enable_cull_face:
        gl.glEnable(gl.GL_CULL_FACE)
    else:
        gl.glDisable(gl.GL_CULL_FACE)

    if last_enable_depth_test:
        gl.glEnable(gl.GL_DEPTH_TEST)
    else:
        gl.glDisable(gl.GL_DEPTH_TEST)

    if last_enable_scissor_test:
        gl.glEnable(gl.GL_SCISSOR_TEST)
    else:
        gl.glDisable(gl.GL_SCISSOR_TEST)

    gl.glScissor(last_scissor_box[0], last_scissor_box[1],
                 last_scissor_box[2], last_scissor_box[3])
    gl.glViewport(last_viewport[0], last_viewport[1],
                  last_viewport[2], last_viewport[3])
