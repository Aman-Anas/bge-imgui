from imgui_bundle.python_backends.base_backend import BaseOpenGLRenderer
from imgui_bundle import imgui

from bge.types import KX_Scene
import bge.logic

import ctypes
import glob
import os
import pathlib

from OpenGL import GL as gl
from PIL import Image
import numpy as np


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

    def __init__(self, scene: KX_Scene):
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

        super(BGEPipelineRenderer, self).__init__()
        self.scene.post_draw.append(self.render_call)

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

        # restore state
        gl.glBindTexture(gl.GL_TEXTURE_2D, last_texture)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, last_array_buffer)
        gl.glBindVertexArray(last_vertex_array)
        pass

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
        self.io.fonts.texture_id = 0
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
    def __init__(self, scene, cursor_path=None):
        self.scene = scene
        super().__init__(scene)

        width, height = bge.render.getWindowWidth(), bge.render.getWindowHeight()

        self.saved_disp_size = width, height
        self.io.display_size = width, height

        self.mouse = bge.logic.mouse
        self.keyboard = bge.logic.keyboard

        self.cursor_renderer = CursorRenderer(scene)

        if not cursor_path:
            self.show_cursor = False
        else:
            self.cursor_renderer.add_cursors(cursor_path)
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

        # Only accept user input if this flag true
        if self.accept_input:
            self.update_mouse_pos(io)
            self.update_mouse_btns(io)
            self.update_keyboard(io)

    def update_mouse_pos(self, io: imgui.IO):
        mouse = self.mouse
        x, y = ((mouse.position[0] * self.io.display_size[0]),
                (mouse.position[1] * self.io.display_size[1]))

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
            pass
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

    def set_main_font(self, path: str, font_size_in_pixels: int):
        io = self.io

        io.fonts.clear()
        self.main_font = io.fonts.add_font_from_file_ttf(
            path, self.font_scaling_factor * font_size_in_pixels)

        self.refresh_font_texture()

    def add_extra_font(self, path: str, font_size_in_pixels: int):
        io = self.io
        newFont = io.fonts.add_font_from_file_ttf(
            path, self.font_scaling_factor * font_size_in_pixels)
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
