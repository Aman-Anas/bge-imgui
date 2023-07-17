from imgui.integrations.base import BaseOpenGLRenderer
from bge.types import KX_Scene
import imgui
import ctypes
import bge.logic
import imgui
import ctypes
from OpenGL import GL as gl
import bgl
import time
import sys


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
        self.scene.post_draw.append(self.renderCall)

    def refresh_font_texture(self):
        # save texture state
        last_texture = gl.glGetIntegerv(gl.GL_TEXTURE_BINDING_2D)

        width, height, pixels = self.io.fonts.get_tex_data_as_rgba32()

        if self._font_texture is not None:
            gl.glDeleteTextures([self._font_texture])

        self._font_texture = gl.glGenTextures(1)

        gl.glBindTexture(gl.GL_TEXTURE_2D, self._font_texture)
        gl.glTexParameteri(
            gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(
            gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width,
                        height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, pixels)

        self.io.fonts.texture_id = self._font_texture
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

        self.data = draw_data
        # if self.renderCall not in self.scene.post_draw:

        # time.sleep(sys.float_info.epsilon)

    def renderCall(self):
        if self.data is None:
            return
        draw_data = self.data

        # perf: local for faster access
        io = self.io

        display_width, display_height = io.display_size
        fb_width = int(display_width * io.display_fb_scale[0])
        fb_height = int(display_height * io.display_fb_scale[1])

        if fb_width == 0 or fb_height == 0:
            return

        draw_data.scale_clip_rects(*io.display_fb_scale)

        # backup GL state
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
            2.0/display_width, 0.0,                   0.0, 0.0,
            0.0,               2.0/-display_height,   0.0, 0.0,
            0.0,               0.0,                  -1.0, 0.0,
            -1.0,               1.0,                   0.0, 1.0
        )

        gl.glUseProgram(self._shader_handle)
        gl.glUniform1i(self._attrib_location_tex, 0)
        gl.glUniformMatrix4fv(self._attrib_proj_mtx, 1,
                              gl.GL_FALSE, ortho_projection)
        gl.glBindVertexArray(self._vao_handle)

        for commands in draw_data.commands_lists:
            idx_buffer_offset = 0

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo_handle)
            # todo: check this (sizes)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, commands.vtx_buffer_size * imgui.VERTEX_SIZE,
                            ctypes.c_void_p(commands.vtx_buffer_data), gl.GL_STREAM_DRAW)

            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self._elements_handle)
            # todo: check this (sizes)
            gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, commands.idx_buffer_size *
                            imgui.INDEX_SIZE, ctypes.c_void_p(commands.idx_buffer_data), gl.GL_STREAM_DRAW)

            # todo: allow to iterate over _CmdList
            for command in commands.commands:
                gl.glBindTexture(gl.GL_TEXTURE_2D, command.texture_id)

                # todo: use named tuple
                x, y, z, w = command.clip_rect
                gl.glScissor(int(x), int(fb_height - w),
                             int(z - x), int(w - y))

                if imgui.INDEX_SIZE == 2:
                    gltype = gl.GL_UNSIGNED_SHORT
                else:
                    gltype = gl.GL_UNSIGNED_INT

                gl.glDrawElements(gl.GL_TRIANGLES, command.elem_count,
                                  gltype, ctypes.c_void_p(idx_buffer_offset))

                idx_buffer_offset += command.elem_count * imgui.INDEX_SIZE

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
    bge.events.TABKEY: imgui.KEY_TAB,
    bge.events.LEFTARROWKEY: imgui.KEY_LEFT_ARROW,
    bge.events.RIGHTARROWKEY: imgui.KEY_RIGHT_ARROW,
    bge.events.UPARROWKEY: imgui.KEY_UP_ARROW,
    bge.events.DOWNARROWKEY: imgui.KEY_DOWN_ARROW,
    bge.events.PAGEUPKEY: imgui.KEY_PAGE_UP,
    bge.events.PAGEDOWNKEY: imgui.KEY_PAGE_DOWN,
    bge.events.HOMEKEY: imgui.KEY_HOME,
    bge.events.ENDKEY: imgui.KEY_END,
    bge.events.INSERTKEY: imgui.KEY_INSERT,
    bge.events.DELKEY: imgui.KEY_DELETE,
    bge.events.BACKSPACEKEY: imgui.KEY_BACKSPACE,
    bge.events.SPACEKEY: imgui.KEY_SPACE,
    bge.events.ENTERKEY: imgui.KEY_ENTER,
    bge.events.ESCKEY: imgui.KEY_ESCAPE,
    bge.events.AKEY: imgui.KEY_A,
    bge.events.CKEY: imgui.KEY_C,
    bge.events.VKEY: imgui.KEY_V,
    bge.events.XKEY: imgui.KEY_X,
    bge.events.YKEY: imgui.KEY_Y,
    bge.events.ZKEY: imgui.KEY_Z,
}


class BGEImguiRenderer(BGEPipelineRenderer):
    def __init__(self, scene):
        self.scene = scene
        super().__init__(scene)

        self.savedDisplaySize = bge.render.getWindowWidth(), bge.render.getWindowHeight()
        self.io.display_size = self.savedDisplaySize[0], self.savedDisplaySize[1]

        self.mouse = bge.logic.mouse
        self.keyboard = bge.logic.keyboard
        self.cursorRenderer = CursorRenderer(scene)
        self.cursorRenderer.addCursor()

        self._map_keys()

    def _map_keys(self):
        key_map = self.io.key_map
        for bgeKey, imguiKey in BGE_KEY_EVENT_MAP.items():
            key_map[imguiKey] = bgeKey

    def updateScreenSize(self, io):
        width = bge.render.getWindowWidth()
        height = bge.render.getWindowHeight()
        refreshSize = True

        if self.savedDisplaySize[0] != width:
            refreshSize = True
        elif self.savedDisplaySize[1] != height:
            refreshSize = True

        if refreshSize:
            self.savedDisplaySize = width, height
            self.io.display_size = self.savedDisplaySize[0], self.savedDisplaySize[1]

    def updateIO(self):
        io = imgui.get_io()
        self.updateScreenSize(io)

        mouse = self.mouse

        pos = ((mouse.position[0] * self.io.display_size[0]),
               (mouse.position[1] * self.io.display_size[1]))

        io.mouse_pos = pos
        self.cursorRenderer.updateCursorInfo(self.savedDisplaySize[1], pos)

        activeMouseButtons = mouse.activeInputs

        if bge.events.LEFTMOUSE in activeMouseButtons:
            io.mouse_down[0] = 1
        else:
            io.mouse_down[0] = 0

        if bge.events.RIGHTMOUSE in activeMouseButtons:
            io.mouse_down[1] = 1
        else:
            io.mouse_down[1] = 0

        if bge.events.MIDDLEMOUSE in activeMouseButtons:
            io.mouse_down[2] = 1
        else:
            io.mouse_down[2] = 0

        if bge.events.WHEELUPMOUSE in activeMouseButtons:
            io.mouse_wheel = .5
        elif bge.events.WHEELDOWNMOUSE in activeMouseButtons:
            io.mouse_wheel = -.5
        else:
            io.mouse_wheel = 0

        keyboard = self.keyboard
        keyMap = BGE_KEY_EVENT_MAP

        for key, event in keyboard.inputs.items():
            if key in keyMap:
                if event.active:
                    io.keys_down[key] = True
                else:
                    io.keys_down[key] = False

        activeKeys = keyboard.activeInputs

        io.key_ctrl = (bge.events.LEFTCTRLKEY in activeKeys) or (
            bge.events.RIGHTCTRLKEY in activeKeys)
        io.key_alt = (bge.events.LEFTALTKEY in activeKeys) or (
            bge.events.RIGHTALTKEY in activeKeys)
        io.key_shift = (bge.events.LEFTSHIFTKEY in activeKeys) or (
            bge.events.RIGHTSHIFTKEY in activeKeys)

        text = keyboard.text
        for character in text:
            io.add_input_character(ord(character))

        # Probably not needed, also deltaTime is only available in RanGE engine
        io.delta_time = bge.logic.deltaTime()

    def setFont(self, path: str, font_scaling_factor: int, font_size_in_pixels: int, screen_scaling_factor: int):
        io = imgui.get_io()

        io.fonts.clear()
        self.new_font = io.fonts.add_font_from_file_ttf(
            path, font_scaling_factor * font_size_in_pixels)

        screen_scaling_factor = bge.render.getWindowWidth() / screen_scaling_factor
        scale = 1
        scale /= font_scaling_factor
        scale *= screen_scaling_factor
        io.font_global_scale = scale
        self.refresh_font_texture()


class CursorRenderer:
    def __init__(self, scene: KX_Scene) -> None:
        self.scene = scene
        self.mousePos = (0, 0)
        self.height = 0
        self.cursorWidth = 25
        self.cursorHeight = 25

    def setCursorSize(self, width: int, height: int):
        self.cursorWidth = width
        self.cursorHeight = height

    def updateCursorInfo(self, height, mousePos):
        self.height = height
        self.mousePos = mousePos

    def addCursor(self, filePath=None):
        if not filePath:
            filePath = bge.logic.expandPath("//cursor.png")

        img = bge.texture.ImageFFmpeg(filePath)
        dummy = img.image  # For some reason I have to assign it to get it to work?? Idk
        img.refresh()
        self.cursor_size = img.size

        id_buf = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGenTextures(1, id_buf)
        self.cursor_tex_id = id_buf.to_list()[0]

        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.cursor_tex_id)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D,
                            bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)

        bgl.glTexParameteri(bgl.GL_TEXTURE_2D,
                            bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA, img.size[0], img.size[1], 0,
                         gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img.image)
        self.cursorTexCo = [(0, 0), (1, 0), (1, 1), (0, 1)]
        self.cursorBackColor = [1, 1, 1, 1]
        self.scene.post_draw.append(self.drawCursor)

    def drawCursor(self):
        width = self.cursorWidth
        height = self.cursorHeight

        x = self.mousePos[0]
        y = - self.mousePos[1] + self.height - height
        gl_position = [
            [x, y],
            [x + width, y],
            [x + width, y + height],
            [x, y + height]
        ]
        # Get some viewport info
        buf = bgl.Buffer(bgl.GL_INT, 4)
        bgl.glGetIntegerv(bgl.GL_VIEWPORT, buf)
        view = buf.to_list()
        # Save the state
        bgl.glPushAttrib(bgl.GL_ALL_ATTRIB_BITS)

        # Disable depth test so we always draw over things
        bgl.glDisable(bgl.GL_DEPTH_TEST)

        # Disable lighting so everything is shadless
        bgl.glDisable(bgl.GL_LIGHTING)

        # Unbinding the texture prevents BGUI frames from somehow picking up on
        # color of the last used texture
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, 0)

        # Make sure we're using smooth shading instead of flat
        bgl.glShadeModel(bgl.GL_SMOOTH)

        # Setup the matrices
        bgl.glMatrixMode(bgl.GL_TEXTURE)
        bgl.glPushMatrix()
        bgl.glLoadIdentity()
        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glPushMatrix()
        bgl.glLoadIdentity()
        bgl.gluOrtho2D(0, view[2], 0, view[3])
        bgl.glMatrixMode(bgl.GL_MODELVIEW)
        bgl.glPushMatrix()
        bgl.glLoadIdentity()
        # Enable textures
        bgl.glEnable(bgl.GL_TEXTURE_2D)

        # Enable alpha blending
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.cursor_tex_id)

        # Draw the textured quad
        bgl.glColor4f(*self.cursorBackColor)

        bgl.glBegin(gl.GL_QUADS)
        for i in range(4):
            bgl.glTexCoord2f(self.cursorTexCo[i][0], self.cursorTexCo[i][1])
            bgl.glVertex2f(gl_position[i][0], gl_position[i][1])
            # print(gl_position[i])
        bgl.glEnd()

        bgl.glBindTexture(bgl.GL_TEXTURE_2D, 0)
        # Reset the state
        bgl.glPopMatrix()
        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glPopMatrix()
        bgl.glMatrixMode(bgl.GL_TEXTURE)
        bgl.glPopMatrix()
        bgl.glPopAttrib()


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
