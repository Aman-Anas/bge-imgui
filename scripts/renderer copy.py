from imgui.integrations.base import BaseOpenGLRenderer
from bge.types import KX_Scene
#import bgl as gl
import imgui
import ctypes as C
import bge.logic
from .renderShaders import VERTEX_SHADER, FRAGMENT_SHADER
import numpy as np
import mathutils
from bgl import glBindTexture, glViewport, glTexParameteri, glTexImage2D, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER
from bgl import *
from bgl import glDeleteVertexArrays
from bgl import glGenTextures, glDeleteTextures, glGetIntegerv, GL_NEAREST, GL_LINEAR, GL_TEXTURE_BINDING_2D, Buffer, GL_INT

_glGenTextures = glGenTextures


def glGenTextures(n, textures=None):
    id_buf = Buffer(GL_INT, n)
    _glGenTextures(n, id_buf)

    if textures:
        textures.extend(id_buf.to_list())

    return id_buf.to_list()[0] if n == 1 else id_buf.to_list()


_glDeleteTextures = glDeleteTextures


def glDeleteTextures(textures):
    n = len(textures)
    id_buf = Buffer(GL_INT, n, textures)
    _glDeleteTextures(n, id_buf)


_glGetIntegerv = glGetIntegerv


def glGetIntegerv(pname):
    # Only used for GL_VIEWPORT right now, so assume we want a size 4 Buffer
    buf = Buffer(GL_INT, 4)
    _glGetIntegerv(pname, buf)
    return buf.to_list()


class BGEImguiRenderer(BaseOpenGLRenderer):

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
        self.scene = scene

        self.shader = None

        super(BGEImguiRenderer, self).__init__()

        self.io.display_size = bge.render.getWindowWidth(), bge.render.getWindowHeight()

    def refresh_font_texture(self):
        # save texture state
        buf = Buffer(GL_INT, 1)
        glGetIntegerv(GL_TEXTURE_BINDING_2D)
        last_texture = buf[0]

        width, height, pixels = self.io.fonts.get_tex_data_as_rgba32()

        if self._font_texture is not None:
            glDeleteTextures([self._font_texture])

        glGenTextures(1)
        self._font_texture = buf[0]

        glBindTexture(GL_TEXTURE_2D, self._font_texture)
        glTexParameteri(
            GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(
            GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        pixel_buffer = Buffer(GL_BYTE, [4 * width * height])
        pixel_buffer[:] = pixels
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width,
                     height, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixel_buffer)

        self.io.fonts.texture_id = self._font_texture
        glBindTexture(GL_TEXTURE_2D, last_texture)
        self.io.fonts.clear_tex_data()

    def _create_device_objects(self):
        filterManager = self.scene.filterManager
        self.shader = filterManager.addFilter(
            0, bge.logic.RAS_2DFILTER_CUSTOMFILTER, "")

        self.shader.enabled = True

        self.shader.setSource(VERTEX_SHADER, FRAGMENT_SHADER, True)

        # self.shader.validate()  # may not be necessary

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

        glViewport(0, 0, int(fb_width), int(fb_height))

        ortho_projection = mathutils.Matrix((
            (2.0/display_width, 0.0,                   0.0, 0.0),
            (0.0,               2.0/-display_height,   0.0, 0.0),
            (0.0,               0.0,                  -1.0, 0.0),
            (-1.0,               1.0,                   0.0, 1.0))
        )

        # shader.bind()
        # TODO: OOF
        shader.setUniformMatrix4("ProjMtx", ortho_projection)

        #shader.setSampler("Texture", 0)

        for commands in draw_data.commands_lists:
            size = commands.idx_buffer_size * imgui.INDEX_SIZE // 4
            address = commands.idx_buffer_data
            ptr = C.cast(address, C.POINTER(C.c_int))
            idx_buffer_np = np.ctypeslib.as_array(ptr, shape=(size,))

            size = commands.vtx_buffer_size * imgui.VERTEX_SIZE // 4
            address = commands.vtx_buffer_data
            ptr = C.cast(address, C.POINTER(C.c_float))
            vtx_buffer_np = np.ctypeslib.as_array(ptr, shape=(size,))
            vtx_buffer_shaped = vtx_buffer_np.reshape(
                -1, imgui.VERTEX_SIZE // 4)

            idx_buffer_offset = 0
            for command in commands.commands:
                x, y, z, w = command.clip_rect
                glScissor(int(x), int(fb_height - w),
                          int(z - x), int(w - y))

                vertices = vtx_buffer_shaped[:, :2]
                uvs = vtx_buffer_shaped[:, 2:4]
                colors = vtx_buffer_shaped.view(np.uint8)[:, 4*4:]
                colors = colors.astype('f') / 255.0

                indices = idx_buffer_np[idx_buffer_offset:
                                        idx_buffer_offset+command.elem_count]

                glBindTexture(GL_TEXTURE_2D, command.texture_id)

                vertList = vertices.tolist()
                uvList = uvs.tolist()
                colorList = colors.tolist()

                for vert in vertList:
                    shader.setUniform2f("Position", vert[0], vert[1])

                # for uv in uvList:
                #     shader.setUniform2f(
                #         "UV", uv[0], uv[1])

                # for color in colorList:
                #     # print(color)
                #     shader.setUniform2f(
                #         "Color", color[0], color[1])

                # batch = batch_for_shader(shader, 'TRIS', {
                #     "Position": vertices,
                #     "UV": uvs,
                #     "Color": colors,
                # }, indices=indices)
                # batch.draw(shader)

                idx_buffer_offset += command.elem_count

    def _invalidate_device_objects(self):
        if self._vao_handle > -1:
            glDeleteVertexArrays(1, [self._vao_handle])
        if self._vbo_handle > -1:
            glDeleteBuffers(1, [self._vbo_handle])
        if self._elements_handle > -1:
            glDeleteBuffers(1, [self._elements_handle])
        self._vao_handle = self._vbo_handle = self._elements_handle = 0

        glDeleteProgram(self._shader_handle)
        self._shader_handle = 0

        if self._font_texture > -1:
            glDeleteTextures([self._font_texture])
        self.io.fonts.texture_id = 0
        self._font_texture = 0

    def _backup_integers(self, *keys_and_lengths):
        """Helper to back up opengl state"""
        keys = keys_and_lengths[::2]
        lengths = keys_and_lengths[1::2]
        buf = Buffer(GL_INT, max(lengths))
        values = []
        for k, n in zip(keys, lengths):
            glGetIntegerv(k, buf)
            values.append(buf[0] if n == 1 else buf[:n])
        return values
