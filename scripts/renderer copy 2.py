from imgui.integrations.base import BaseOpenGLRenderer
from bge.types import KX_Scene
import bgl as gl
import imgui
import ctypes
import bge.logic
from .renderShaders import VERTEX_SHADER, FRAGMENT_SHADER
import numpy as np
import mathutils
from OpenGL import GL as pyOpenGL
from bgl import glGenTextures, glDeleteTextures, glGetIntegerv, Buffer

_glGenTextures = glGenTextures


def glGenTextures(n, textures=None):
    id_buf = Buffer(gl.GL_INT, n)
    _glGenTextures(n, id_buf)

    if textures:
        textures.extend(id_buf.to_list())

    return id_buf.to_list()[0] if n == 1 else id_buf.to_list()


_glDeleteTextures = glDeleteTextures


def glDeleteTextures(textures):
    n = len(textures)
    id_buf = Buffer(gl.GL_INT, n, textures)
    _glDeleteTextures(n, id_buf)


_glGetIntegerv = glGetIntegerv


def glGetIntegerv(pname):
    # Only used for GL_VIEWPORT right now, so assume we want a size 4 Buffer
    buf = Buffer(gl.GL_INT, 4)
    _glGetIntegerv(pname, buf)
    return buf.to_list()


class BGEImguiRenderer(BaseOpenGLRenderer):
    VERTEX_SHADER_SRC = """
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
    uniform sampler2D Texture;
    in vec2 Frag_UV;
    in vec4 Frag_Color;
    out vec4 Out_Color;

    vec4 linear_to_srgb(vec4 linear) {
        return mix(
            1.055 * pow(linear, vec4(1.0 / 2.4)) - 0.055,
            12.92 * linear,
            step(linear, vec4(0.00031308))
        );
    }

    vec4 srgb_to_linear(vec4 srgb) {
        return mix(
            pow((srgb + 0.055) / 1.055, vec4(2.4)),
            srgb / 12.92,
            step(srgb, vec4(0.04045))
        );
    }

    void main() {
        Out_Color = Frag_Color * texture(Texture, Frag_UV.st);
        Out_Color.rgba = srgb_to_linear(Out_Color.rgba);
    }
    """

    def __init__(self, scene: KX_Scene):
        self._shader_handle = None
        self._vert_handle = None
        self._fragment_handle = None

        self._attrib_location_tex = None
        self._attrib_proj_mtx = None
        self._attrib_location_position = None
        self._attrib_location_uv = None
        self._attrib_location_color = None

        self._vbo_handle = None
        self._elements_handle = None
        self._vao_handle = None

        self.shader = None
        self.scene = scene

        super(BGEImguiRenderer, self).__init__()

        self.io.display_size = bge.render.getWindowWidth(), bge.render.getWindowHeight()

    def refresh_font_texture(self):
        # save texture state
        buf = gl.Buffer(gl.GL_INT, 1)
        gl.glGetIntegerv(gl.GL_TEXTURE_BINDING_2D, buf)
        last_texture = buf[0]

        width, height, pixels = self.io.fonts.get_tex_data_as_rgba32()

        if self._font_texture is not None:
            gl.glDeleteTextures([self._font_texture])

        gl.glGenTextures(1, buf)
        self._font_texture = buf[0]

        gl.glBindTexture(gl.GL_TEXTURE_2D, self._font_texture)
        gl.glTexParameteri(
            gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(
            gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        pixel_buffer = gl.Buffer(gl.GL_BYTE, [4 * width * height])
        pixel_buffer[:] = pixels
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width,
                        height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, pixel_buffer)

        self.io.fonts.texture_id = self._font_texture
        gl.glBindTexture(gl.GL_TEXTURE_2D, last_texture)
        self.io.fonts.clear_tex_data()

    def _create_device_objects(self):
        pass
        filterManager = self.scene.filterManager
        self.shader = filterManager.addFilter(
            0, bge.logic.RAS_2DFILTER_CUSTOMFILTER, FRAGMENT_SHADER)

        self.shader.enabled = True

        last_texture = glGetIntegerv(gl.GL_TEXTURE_BINDING_2D)
        last_array_buffer = glGetIntegerv(gl.GL_ARRAY_BUFFER_BINDING)

        last_vertex_array = glGetIntegerv(gl.GL_VERTEX_ARRAY_BINDING)

        self._shader_handle = pyOpenGL.glCreateProgram()

        vertex_shader = pyOpenGL.glCreateShader(pyOpenGL.GL_VERTEX_SHADER)
        fragment_shader = pyOpenGL.glCreateShader(gl.GL_FRAGMENT_SHADER)

        pyOpenGL.glShaderSource(vertex_shader, self.VERTEX_SHADER_SRC)
        pyOpenGL.glShaderSource(fragment_shader, self.FRAGMENT_SHADER_SRC)
        pyOpenGL.glCompileShader(vertex_shader)
        pyOpenGL.glCompileShader(fragment_shader)

        pyOpenGL.glAttachShader(self._shader_handle, vertex_shader)
        pyOpenGL.glAttachShader(self._shader_handle, fragment_shader)

        pyOpenGL.glLinkProgram(self._shader_handle)

        # note: after linking shaders can be removed
        pyOpenGL.glDeleteShader(vertex_shader)
        pyOpenGL.glDeleteShader(fragment_shader)

        self._attrib_location_tex = pyOpenGL.glGetUniformLocation(
            self._shader_handle, "Texture")
        self._attrib_proj_mtx = pyOpenGL.glGetUniformLocation(
            self._shader_handle, "ProjMtx")
        self._attrib_location_position = pyOpenGL.glGetAttribLocation(
            self._shader_handle, "Position")
        self._attrib_location_uv = pyOpenGL.glGetAttribLocation(
            self._shader_handle, "UV")
        self._attrib_location_color = pyOpenGL.glGetAttribLocation(
            self._shader_handle, "Color")

        self._vbo_handle = Buffer(gl.GL_INT, 1)
        gl.glGenBuffers(1, self._vbo_handle)

        self._elements_handle = Buffer(gl.GL_INT, 1)
        gl.glGenBuffers(1, self._elements_handle)

        self._vao_handle = Buffer(gl.GL_INT, 1)
        gl.glGenVertexArrays(1, self._vao_handle)

        gl.glBindVertexArray(self._vao_handle.to_list()[0])
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo_handle.to_list()[0])

        gl.glEnableVertexAttribArray(self._attrib_location_position)
        gl.glEnableVertexAttribArray(self._attrib_location_uv)
        gl.glEnableVertexAttribArray(self._attrib_location_color)

        arrayType = ctypes.c_int16 * 2000
        cVertexBuffer = ctypes.c_void_p(imgui.VERTEX_BUFFER_POS_OFFSET)
        npVertexData = np.frombuffer(ctypes.cast(
            cVertexBuffer, ctypes.POINTER(arrayType)))

        vertexBuffer = np_array_as_bgl_Buffer(npVertexData)

        gl.glVertexAttribPointer(self._attrib_location_position, 2, gl.GL_FLOAT, gl.GL_FALSE,
                                 imgui.VERTEX_SIZE, vertexBuffer)
        gl.glVertexAttribPointer(self._attrib_location_uv, 2, gl.GL_FLOAT, gl.GL_FALSE,
                                 imgui.VERTEX_SIZE, ctypes.c_void_p(imgui.VERTEX_BUFFER_UV_OFFSET))
        gl.glVertexAttribPointer(self._attrib_location_color, 4, gl.GL_UNSIGNED_BYTE,
                                 gl.GL_TRUE, imgui.VERTEX_SIZE, ctypes.c_void_p(imgui.VERTEX_BUFFER_COL_OFFSET))

        # restore state
        gl.glBindTexture(gl.GL_TEXTURE_2D, last_texture)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, last_array_buffer)
        gl.glBindVertexArray(last_vertex_array)

    def render(self, draw_data: imgui.core._DrawData):
        io = self.io
        shader = self.shader

        display_width, display_height = io.display_size
        fb_width = int(display_width * io.display_fb_scale[0])
        fb_height = int(display_height * io.display_fb_scale[1])

        if fb_width == 0 or fb_height == 0:
            print("ooof?")
            return

        draw_data.scale_clip_rects(*io.display_fb_scale)

        # common_gl_state_tuple = self.get_common_gl_state()

        # gl.glPushAttrib(gl.GL_ENABLE_BIT |
        #                 gl.GL_COLOR_BUFFER_BIT | gl.GL_TRANSFORM_BIT)
        # gl.glEnable(gl.GL_BLEND)
        # gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        # gl.glDisable(gl.GL_CULL_FACE)
        # gl.glDisable(gl.GL_DEPTH_TEST)
        # gl.glEnable(gl.GL_SCISSOR_TEST)
        # gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        # gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        # gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        # gl.glEnableClientState(gl.GL_COLOR_ARRAY)
        # gl.glEnable(gl.GL_TEXTURE_2D)

        # gl.glViewport(0, 0, int(fb_width), int(fb_height))
        # gl.glMatrixMode(gl.GL_PROJECTION)
        # gl.glPushMatrix()
        # gl.glLoadIdentity()
        # gl.glOrtho(0, io.display_size.x, io.display_size.y, 0.0, -1., 1.)
        # gl.glMatrixMode(gl.GL_MODELVIEW)
        # gl.glPushMatrix()
        # gl.glLoadIdentity()

        # for commands in draw_data.commands_lists:
        #     idx_buffer = commands.idx_buffer_data

        #     ArrayType = ctypes.c_int16 * 2000
        #     cVertexBuffer = ctypes.c_void_p(
        #         commands.vtx_buffer_data + imgui.VERTEX_BUFFER_POS_OFFSET)
        #     npVertexData = np.frombuffer(ctypes.cast(
        #         cVertexBuffer, ctypes.POINTER(ArrayType)))

        #     vertexBuffer = np_array_as_bgl_Buffer(npVertexData)

        #     gl.glVertexPointer(2, pyOpenGL.GL_FLOAT,
        #                        imgui.VERTEX_SIZE, vertexBuffer)
        #     gl.glTexCoordPointer(2, gl.GL_FLOAT, imgui.VERTEX_SIZE, ctypes.c_void_p(
        #         commands.vtx_buffer_data + imgui.VERTEX_BUFFER_UV_OFFSET))
        #     gl.glColorPointer(4, gl.GL_UNSIGNED_BYTE, imgui.VERTEX_SIZE, ctypes.c_void_p(
        #         commands.vtx_buffer_data + imgui.VERTEX_BUFFER_COL_OFFSET))

        #     for command in commands.commands:
        #         gl.glBindTexture(gl.GL_TEXTURE_2D, command.texture_id)

        #         x, y, z, w = command.clip_rect
        #         gl.glScissor(int(x), int(fb_height - w),
        #                      int(z - x), int(w - y))

        #         if imgui.INDEX_SIZE == 2:
        #             gltype = gl.GL_UNSIGNED_SHORT
        #         else:
        #             gltype = gl.GL_UNSIGNED_INT

        #         gl.glDrawElements(gl.GL_TRIANGLES, command.elem_count,
        #                           gltype, ctypes.c_void_p(idx_buffer))

        #         idx_buffer += (command.elem_count * imgui.INDEX_SIZE)

        # self.restore_common_gl_state(common_gl_state_tuple)

        # gl.glDisableClientState(gl.GL_COLOR_ARRAY)
        # gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        # gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        # gl.glMatrixMode(gl.GL_MODELVIEW)
        # gl.glPopMatrix()
        # gl.glMatrixMode(gl.GL_PROJECTION)
        # gl.glPopMatrix()
        # gl.glPopAttrib()

        # gl.glViewport(0, 0, int(fb_width), int(fb_height))

        # ortho_projection = mathutils.Matrix((
        #     (2.0/display_width, 0.0,                   0.0, 0.0),
        #     (0.0,               2.0/-display_height,   0.0, 0.0),
        #     (0.0,               0.0,                  -1.0, 0.0),
        #     (-1.0,               1.0,                   0.0, 1.0))
        # )

        # # shader.bind()
        # # TODO: OOF
        # #shader.setUniformMatrix4("ProjMtx", ortho_projection)
        # shader.setTexture(0, 0, "inTex")
        # #shader.setSampler("inTex", 0)

        # for commands in draw_data.commands_lists:
        #     size = commands.idx_buffer_size * imgui.INDEX_SIZE // 4
        #     address = commands.idx_buffer_data
        #     ptr = C.cast(address, C.POINTER(C.c_int))
        #     idx_buffer_np = np.ctypeslib.as_array(ptr, shape=(size,))

        #     size = commands.vtx_buffer_size * imgui.VERTEX_SIZE // 4
        #     address = commands.vtx_buffer_data
        #     ptr = C.cast(address, C.POINTER(C.c_float))
        #     vtx_buffer_np = np.ctypeslib.as_array(ptr, shape=(size,))
        #     vtx_buffer_shaped = vtx_buffer_np.reshape(
        #         -1, imgui.VERTEX_SIZE // 4)

        #     idx_buffer_offset = 0
        #     for command in commands.commands:
        #         x, y, z, w = command.clip_rect
        #         gl.glScissor(int(x), int(fb_height - w),
        #                      int(z - x), int(w - y))

        #         vertices = vtx_buffer_shaped[:, :2]
        #         uvs = vtx_buffer_shaped[:, 2:4]
        #         colors = vtx_buffer_shaped.view(np.uint8)[:, 4*4:]
        #         colors = colors.astype('f') / 255.0

        #         indices = idx_buffer_np[idx_buffer_offset:
        #                                 idx_buffer_offset+command.elem_count]

        #         gl.glBindTexture(gl.GL_TEXTURE_2D, command.texture_id)

        #         vertList = vertices.tolist()
        #         uvList = uvs.tolist()
        #         colorList = colors.tolist()
        #         # gl.glBegin()
        #         # for vert in vertList:
        #         #     shader.setUniform2f("Position", vert[0], vert[1])

        #         # for uv in uvList:
        #         #     shader.setUniform2f(
        #         #         "UV", uv[0], uv[1])

        #         # for color in colorList:
        #         #     # print(color)
        #         #     shader.setUniform2f(
        #         #         "Color", color[0], color[1])

        #         # batch = batch_for_shader(shader, 'TRIS', {
        #         #     "Position": vertices,
        #         #     "UV": uvs,
        #         #     "Color": colors,
        #         # }, indices=indices)
        #         # batch.draw(shader)

        #         idx_buffer_offset += command.elem_count

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

    def _backup_integers(self, *keys_and_lengths):
        """Helper to back up opengl state"""
        keys = keys_and_lengths[::2]
        lengths = keys_and_lengths[1::2]
        buf = gl.Buffer(gl.GL_INT, max(lengths))
        values = []
        for k, n in zip(keys, lengths):
            gl.glGetIntegerv(k, buf)
            values.append(buf[0] if n == 1 else buf[:n])
        return values

    def get_common_gl_state(self):
        """
        Backups the current OpenGL state
        Returns a tuple of results for glGet / glIsEnabled calls
        NOTE: when adding more backuped state in the future,
        make sure to update function `restore_common_gl_state`
        """
        last_texture = glGetIntegerv(gl.GL_TEXTURE_BINDING_2D)
        last_viewport = glGetIntegerv(gl.GL_VIEWPORT)
        last_enable_blend = gl.glIsEnabled(gl.GL_BLEND)
        last_enable_cull_face = gl.glIsEnabled(gl.GL_CULL_FACE)
        last_enable_depth_test = gl.glIsEnabled(gl.GL_DEPTH_TEST)
        last_enable_scissor_test = gl.glIsEnabled(gl.GL_SCISSOR_TEST)
        last_scissor_box = glGetIntegerv(gl.GL_SCISSOR_BOX)
        last_blend_src = glGetIntegerv(gl.GL_BLEND_SRC)
        last_blend_dst = glGetIntegerv(gl.GL_BLEND_DST)
        last_blend_equation_rgb = glGetIntegerv(gl.GL_BLEND_EQUATION_RGB)
        last_blend_equation_alpha = glGetIntegerv(
            gl.GL_BLEND_EQUATION_ALPHA)
        last_front_and_back_polygon_mode, _, _2, _3 = glGetIntegerv(
            gl.GL_POLYGON_MODE)
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

    def restore_common_gl_state(self, common_gl_state_tuple):
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

        gl.glBindTexture(gl.GL_TEXTURE_2D, last_texture[0])
        # pyOpenGL.glBlendEquationSeparate(
        #     last_blend_equation_rgb, last_blend_equation_alpha)
        gl.glBlendFunc(last_blend_src[0], last_blend_dst[0])

        gl.glPolygonMode(gl.GL_FRONT_AND_BACK,
                         last_front_and_back_polygon_mode)

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


_Py_ssize_t = ctypes.c_int64


class _PyObject(ctypes.Structure):
    pass


_PyObject._fields_ = [                      # cannot define inside _PyObject,
    ('ob_refcnt', _Py_ssize_t),             # because _PyObject is referenced
    ('ob_type', ctypes.POINTER(_PyObject)),  # <-- here
]


class _PyObject(ctypes.Structure):
    _fields_ = [
        ('_ob_next', ctypes.POINTER(_PyObject)),
        ('_ob_prev', ctypes.POINTER(_PyObject)),
        ('ob_refcnt', _Py_ssize_t),
        ('ob_type', ctypes.POINTER(_PyObject)),
    ]


class _PyVarObject(_PyObject):
    _fields_ = [
        ('ob_size', _Py_ssize_t),
    ]


class C_Buffer(_PyVarObject):
    _fields_ = [
        ("parent", ctypes.py_object),
        ("type", ctypes.c_int),
        ("ndimensions", ctypes.c_int),
        ("dimensions", ctypes.POINTER(ctypes.c_int)),
        ("buf", ctypes.c_void_p),
    ]


def np_array_as_bgl_Buffer(array):
    type = array.dtype
    if type == np.int8:
        type = gl.GL_BYTE
    elif type == np.int16:
        type = gl.GL_SHORT
    elif type == np.int32:
        type = gl.GL_INT
    elif type == np.float32:
        type = gl.GL_FLOAT
    elif type == np.float64:
        type = gl.GL_DOUBLE
    else:
        raise

    _decref = ctypes.pythonapi.Py_DecRef
    _incref = ctypes.pythonapi.Py_IncRef

    _decref.argtypes = _incref.argtypes = [ctypes.py_object]
    _decref.restype = _incref.restype = None

    buf = gl.Buffer(gl.GL_BYTE, (1, *array.shape))[0]
    c_buf = C_Buffer.from_address(id(buf))

    _decref(c_buf.parent)
    _incref(array)

    c_buf.parent = array  # Prevents MEM_freeN
    c_buf.type = type
    c_buf.buf = array.ctypes.data
    return buf
