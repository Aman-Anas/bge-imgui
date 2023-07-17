from .gl_utils import *
import bgl
from imgui.integrations.base import BaseOpenGLRenderer
from bge.types import KX_Scene
import imgui
import ctypes
import bge.logic
import numpy as np
import imgui
import ctypes
from OpenGL import GL as pyOpenGL


# DOES NOT WORK AT THE MOMENT,
# I switched to the pyopengl renderer since it has extensive documentation
# Ideally bgl has better performance though

class BGEPipelineRenderer(BaseOpenGLRenderer):
    """Basic OpenGL integration base class."""

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
        self.scene.post_draw.append(self.saveLoadGLState)

    def refresh_font_texture(self):
        # save texture state
        buf = Buffer(bgl.GL_INT, 1)
        #bgl.glGetIntegerv(GL_TEXTURE_BINDING_2D, buf)
        #last_texture = buf[0]

        width, height, pixels = self.io.fonts.get_tex_data_as_rgba32()

        if self._font_texture is not None:
            glDeleteTextures([self._font_texture])

        bgl.glGenTextures(1, buf)
        self._font_texture = buf[0]
        last_texture = buf[0]

        glBindTexture(GL_TEXTURE_2D, self._font_texture)
        glTexParameteri(
            GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(
            GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        pixel_buffer = Buffer(GL_BYTE, [4 * width * height])
        pixel_buffer[:] = pixels
        glTexImage2D(GL_TEXTURE_2D, 0, GL_ALPHA, width,
                     height, 0, GL_ALPHA, GL_UNSIGNED_BYTE, pixel_buffer)
        # print(pixels)

        self.io.fonts.texture_id = self._font_texture
        #glBindTexture(GL_TEXTURE_2D, last_texture)
        self.io.fonts.clear_tex_data()
        # print(last_texture)
        # print(self.io.fonts.texture_id)

    def _create_device_objects(self):
        # # save state

        last_texture = glGetIntegerv(GL_TEXTURE_BINDING_2D)
        last_array_buffer = glGetIntegerv(GL_ARRAY_BUFFER_BINDING)

        last_vertex_array = glGetIntegerv(GL_VERTEX_ARRAY_BINDING)

        #self._shader_handle = pyOpenGL.glCreateProgram()
        # note: no need to store shader parts handles after linking
        #vertex_shader = pyOpenGL.glCreateShader(GL_VERTEX_SHADER)
        #fragment_shader = pyOpenGL.glCreateShader(GL_FRAGMENT_SHADER)

        # glShaderSource(vertex_shader, self.VERTEX_SHADER_SRC)
        # gl.glShaderSource(fragment_shader, self.FRAGMENT_SHADER_SRC)
        # gl.glCompileShader(vertex_shader)
        # gl.glCompileShader(fragment_shader)

        # gl.glAttachShader(self._shader_handle, vertex_shader)
        # gl.glAttachShader(self._shader_handle, fragment_shader)

        # gl.glLinkProgram(self._shader_handle)

        # # note: after linking shaders can be removed
        # gl.glDeleteShader(vertex_shader)
        # gl.glDeleteShader(fragment_shader)

        # self._attrib_location_tex = gl.glGetUniformLocation(
        #     self._shader_handle, "Texture")
        # self._attrib_proj_mtx = gl.glGetUniformLocation(
        #     self._shader_handle, "ProjMtx")
        # self._attrib_location_position = gl.glGetAttribLocation(
        #     self._shader_handle, "Position")
        # self._attrib_location_uv = gl.glGetAttribLocation(
        #     self._shader_handle, "UV")
        # self._attrib_location_color = gl.glGetAttribLocation(
        #     self._shader_handle, "Color")

        # self._vbo_handle = gl.glGenBuffers(1)
        # self._elements_handle = gl.glGenBuffers(1)

        # self._vao_handle = gl.glGenVertexArrays(1)
        # glBindVertexArray(self._vao_handle)
        #glBindBuffer(GL_ARRAY_BUFFER, self._vbo_handle)

        # glEnableVertexAttribArray(self._attrib_location_position)
        # gl.glEnableVertexAttribArray(self._attrib_location_uv)
        # gl.glEnableVertexAttribArray(self._attrib_location_color)

        # gl.glVertexAttribPointer(self._attrib_location_position, 2, gl.GL_FLOAT, gl.GL_FALSE,
        #                          imgui.VERTEX_SIZE, ctypes.c_void_p(imgui.VERTEX_BUFFER_POS_OFFSET))
        # gl.glVertexAttribPointer(self._attrib_location_uv, 2, gl.GL_FLOAT, gl.GL_FALSE,
        #                          imgui.VERTEX_SIZE, ctypes.c_void_p(imgui.VERTEX_BUFFER_UV_OFFSET))
        # gl.glVertexAttribPointer(self._attrib_location_color, 4, gl.GL_UNSIGNED_BYTE,
        #                          gl.GL_TRUE, imgui.VERTEX_SIZE, ctypes.c_void_p(imgui.VERTEX_BUFFER_COL_OFFSET))

        # # restore state
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, last_texture[0])
        #bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, last_array_buffer)
        # bgl.glBindVertexArray(last_vertex_array)
        pass

    def saveLoadGLState(self):
        view = glGetIntegerv(GL_VIEWPORT)
        # Save the state
        glPushAttrib(GL_ALL_ATTRIB_BITS)

        # Disable depth test so we always draw over things
        glDisable(GL_DEPTH_TEST)

        # Disable lighting so everything is shadless
        glDisable(GL_LIGHTING)

        # Unbinding the texture prevents BGUI frames from somehow picking up on
        # color of the last used texture
        glBindTexture(GL_TEXTURE_2D, 0)

        # Make sure we're using smooth shading instead of flat
        glShadeModel(GL_SMOOTH)

        # Setup the matrices
        glMatrixMode(GL_TEXTURE)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, view[2], 0, view[3])
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Do things
        self.renderCall()

        # Reset the state
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_TEXTURE)
        glPopMatrix()
        glPopAttrib()

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

        # gl.glEnable(gl.GL_BLEND)
        # # gl.glBlendEquation(gl.GL_FUNC_ADD)
        # gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        # gl.glDisable(gl.GL_CULL_FACE)
        # gl.glDisable(gl.GL_DEPTH_TEST)
        # gl.glEnable(gl.GL_SCISSOR_TEST)
        # # gl.glActiveTexture(gl.GL_TEXTURE0)

        # gl.glViewport(0, 0, int(fb_width), int(fb_height))

        # ortho_projection = (
        #     2.0/display_width, 0.0,                   0.0, 0.0,
        #     0.0,               2.0/-display_height,   0.0, 0.0,
        #     0.0,               0.0,                  -1.0, 0.0,
        #     -1.0,               1.0,                   0.0, 1.0
        # )

        # # Enable polygon offset
        # gl.glEnable(gl.GL_POLYGON_OFFSET_FILL)
        # gl.glPolygonOffset(1.0, 1.0)
        last_texture = glGetIntegerv(GL_TEXTURE_BINDING_2D)

        # Enable alpha blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_CULL_FACE)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_SCISSOR_TEST)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glEnable(GL_TEXTURE_2D)
        glViewport(0, 0, int(fb_width), int(fb_height))

        for commands in draw_data.commands_lists:
            idx_buffer = commands.idx_buffer_data

            # size = commands.vtx_buffer_size * imgui.VERTEX_SIZE // 4
            # address = commands.vtx_buffer_data
            # ptr = ctypes.cast(address, ctypes.POINTER(ctypes.c_float))
            # vtx_buffer_np = np.ctypeslib.as_array(ptr, shape=(size,))
            # vtxbuf = bgl.Buffer(bgl.GL_FLOAT, len(
            #     vtx_buffer_np), vtx_buffer_np)  # [0]
            # # vtx_buffer_shaped = vtx_buffer_np.reshape(
            # #     -1, imgui.VERTEX_SIZE // 4)
            # print(vtxbuf)
            # # print(len(vtx_buffer_shaped))
            # glVertexPointer(2, GL_FLOAT, imgui.VERTEX_SIZE, vtxbuf)

            # size = commands.idx_buffer_size * imgui.INDEX_SIZE // 4
            # address = commands.idx_buffer_data
            # idx_buf_ptr = ctypes.cast(address, ctypes.POINTER(ctypes.c_int))
            # idx_buffer_np = np.ctypeslib.as_array(idx_buf_ptr, shape=(size,))
            # idxbuf = bgl.Buffer(bgl.GL_INT, len(
            #     idx_buffer_np), idx_buffer_np)  # [0]

            # print(idxbuf)
            pyOpenGL.glVertexPointer(2, pyOpenGL.GL_FLOAT, imgui.VERTEX_SIZE, ctypes.c_void_p(
                commands.vtx_buffer_data + imgui.VERTEX_BUFFER_POS_OFFSET))
            pyOpenGL.glTexCoordPointer(2, pyOpenGL.GL_FLOAT, imgui.VERTEX_SIZE, ctypes.c_void_p(
                commands.vtx_buffer_data + imgui.VERTEX_BUFFER_UV_OFFSET))
            pyOpenGL.glColorPointer(4, pyOpenGL.GL_UNSIGNED_BYTE, imgui.VERTEX_SIZE, ctypes.c_void_p(
                commands.vtx_buffer_data + imgui.VERTEX_BUFFER_COL_OFFSET))

            #
            #
            #
            #
            # vtx_buffer_shaped = vtx_buffer_np.reshape(
            #     -1, imgui.VERTEX_SIZE // 4)
            idx_buffer_offset = 0

            for command in commands.commands:
                pyOpenGL.glBindTexture(GL_TEXTURE_2D, command.texture_id)

                # todo: use named tuple
                x, y, z, w = command.clip_rect
                # glScissor(int(x), int(fb_height - w),
                #           int(z - x), int(w - y))
                pyOpenGL.glScissor(int(x), int(fb_height - w),
                                   int(z - x), int(w - y))

                # vertices = vtx_buffer_shaped[:, :2]
                # uvs = vtx_buffer_shaped[:, 2:4]
                # colors = vtx_buffer_shaped.view(np.uint8)[:, 4*4:]
                # colors = colors.astype('f') / 255.0

                # indices = idx_buffer_np[idx_buffer_offset:
                #                         idx_buffer_offset+command.elem_count]

                #buf = bgl.Buffer(bgl.GL_BYTE, 1, [idx_buf_ptr])
                # print(buf.to_list())

                # print("texes:")
                # print(command.texture_id)
                if imgui.INDEX_SIZE == 2:
                    gltype = pyOpenGL.GL_UNSIGNED_SHORT
                else:
                    gltype = pyOpenGL.GL_UNSIGNED_INT

                # Enable polygon offset
                # glEnable(GL_POLYGON_OFFSET_FILL)
                #glPolygonOffset(1.0, 1.0)
                #glColor4f(1, 1, 1, 1)
                # print("wao")
                pyOpenGL.glDrawElements(pyOpenGL.GL_TRIANGLES, command.elem_count,
                                        gltype, ctypes.c_void_p(idx_buffer))

                # print("hm")
                # glBegin(GL_QUADS)
                # for index, vert in enumerate(vertices):

                #     color = colors[index]
                #     uv = uvs[index]
                #     glTexCoord2f(uv[0], uv[1])
                #     glColor4f(color[0], color[1], color[2], color[3])
                #     glVertex2f(vert[0], vert[1])
                # glEnd()

                glDisable(GL_POLYGON_OFFSET_FILL)

                idx_buffer_offset += command.elem_count
                idx_buffer += (command.elem_count * imgui.INDEX_SIZE)
                #idx_buffer_offset += command.elem_count * imgui.INDEX_SIZE

        # restore modified GL state
        # gl.glUseProgram(last_program)
        # gl.glActiveTexture(last_active_texture)
        #glBindTexture(bgl.GL_TEXTURE_2D, last_texture[0])
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)

        # gl.glBindVertexArray(last_vertex_array)
        #gl.glBindBuffer(gl.GL_ARRAY_BUFFER, last_array_buffer)
        #gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, last_element_array_buffer)
        # gl.glBlendEquationSeparate(
        #    last_blend_equation_rgb, last_blend_equation_alpha)
        #bgl.glBlendFunc(last_blend_src, last_blend_dst)

        # if last_enable_blend:
        #     gl.glEnable(gl.GL_BLEND)
        # else:
        #     gl.glDisable(gl.GL_BLEND)

        # if last_enable_cull_face:
        #     gl.glEnable(gl.GL_CULL_FACE)
        # else:
        #     gl.glDisable(gl.GL_CULL_FACE)

        # if last_enable_depth_test:
        #     gl.glEnable(gl.GL_DEPTH_TEST)
        # else:
        #     gl.glDisable(gl.GL_DEPTH_TEST)

        # if last_enable_scissor_test:
        #     gl.glEnable(gl.GL_SCISSOR_TEST)
        # else:
        #     gl.glDisable(gl.GL_SCISSOR_TEST)

        # gl.glViewport(last_viewport[0], last_viewport[1],
        #               last_viewport[2], last_viewport[3])
        # gl.glScissor(last_scissor_box[0], last_scissor_box[1],
        #              last_scissor_box[2], last_scissor_box[3])

    def _invalidate_device_objects(self):
        # if self._vao_handle > -1:
        #     gl.glDeleteVertexArrays(1, [self._vao_handle])
        # if self._vbo_handle > -1:
        #     gl.glDeleteBuffers(1, [self._vbo_handle])
        # if self._elements_handle > -1:
        #     gl.glDeleteBuffers(1, [self._elements_handle])

        # gl.glDeleteProgram(self._shader_handle)

        if self._font_texture > -1:
            glDeleteTextures([self._font_texture])
        self.io.fonts.texture_id = 0
        self._font_texture = 0

    def _backup_integers(self, *keys_and_lengths):
        """Helper to back up opengl state"""
        keys = keys_and_lengths[::2]
        lengths = keys_and_lengths[1::2]
        buf = bgl.Buffer(bgl.GL_INT, max(lengths))
        values = []
        for k, n in zip(keys, lengths):
            bgl.glGetIntegerv(k, buf)
            values.append(buf[0] if n == 1 else buf[:n])
        return values


class BGEImguiRenderer(BGEPipelineRenderer):
    def __init__(self, scene):
        self.scene = scene
        super().__init__(scene)
        self.io.display_size = bge.render.getWindowWidth(), bge.render.getWindowHeight()

        self.mouse = bge.logic.mouse

    def updateIO(self):
        mouse = self.mouse
        io = imgui.get_io()
        pos = (int(mouse.position[0] * self.io.display_size[0]),
               int(mouse.position[1] * self.io.display_size[1]))
        # print(pos)

        io.mouse_pos = pos

        if bge.events.LEFTMOUSE in mouse.activeInputs:
            io.mouse_down[0] = 1
        else:
            io.mouse_down[0] = 0

        if bge.events.RIGHTMOUSE in mouse.activeInputs:
            io.mouse_down[1] = 1
        else:
            io.mouse_down[1] = 0

        if bge.events.MIDDLEMOUSE in mouse.activeInputs:
            io.mouse_down[2] = 1
        else:
            io.mouse_down[2] = 0
