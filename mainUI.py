import imgui
from imgui.integrations.base import BaseOpenGLRenderer
import bgl as gl
import gpu
import ctypes as C
import numpy as np
import bge
import mathutils


class BlenderImguiRenderer(BaseOpenGLRenderer):
    """Integration of ImGui into Blender."""

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

    def __init__(self, scene: bge.types.KX_Scene):
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

        super().__init__()

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
        filterManager = self.scene.filterManager
        
        shader = filterManager.addFilter(
            2, bge.logic.RAS_2DFILTER_CUSTOMFILTER, "")
        
        shader.setSource(self.VERTEX_SHADER_SRC,
                         self.FRAGMENT_SHADER_SRC, True)
        
        self._bl_shader = shader
        # gpu.types.GPUShader(
        #     self.VERTEX_SHADER_SRC, self.FRAGMENT_SHADER_SRC)

    def render(self, draw_data):
        io = self.io
        shader = self._bl_shader

        display_width, display_height = io.display_size
        fb_width = int(display_width * io.display_fb_scale[0])
        fb_height = int(display_height * io.display_fb_scale[1])

        if fb_width == 0 or fb_height == 0:
            return

        draw_data.scale_clip_rects(*io.display_fb_scale)

        # backup GL state
        (
            last_program,
            last_texture,
            last_active_texture,
            last_array_buffer,
            last_element_array_buffer,
            last_vertex_array,
            last_blend_src,
            last_blend_dst,
            last_blend_equation_rgb,
            last_blend_equation_alpha,
            last_viewport,
            last_scissor_box,
        ) = self._backup_integers(
            gl.GL_CURRENT_PROGRAM, 1,
            gl.GL_TEXTURE_BINDING_2D, 1,
            gl.GL_ACTIVE_TEXTURE, 1,
            gl.GL_ARRAY_BUFFER_BINDING, 1,
            gl.GL_ELEMENT_ARRAY_BUFFER_BINDING, 1,
            gl.GL_VERTEX_ARRAY_BINDING, 1,
            gl.GL_BLEND_SRC, 1,
            gl.GL_BLEND_DST, 1,
            gl.GL_BLEND_EQUATION_RGB, 1,
            gl.GL_BLEND_EQUATION_ALPHA, 1,
            gl.GL_VIEWPORT, 4,
            gl.GL_SCISSOR_BOX, 4,
        )

        last_enable_blend = gl.glIsEnabled(gl.GL_BLEND)
        last_enable_cull_face = gl.glIsEnabled(gl.GL_CULL_FACE)
        last_enable_depth_test = gl.glIsEnabled(gl.GL_DEPTH_TEST)
        last_enable_scissor_test = gl.glIsEnabled(gl.GL_SCISSOR_TEST)

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendEquation(gl.GL_FUNC_ADD)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glActiveTexture(gl.GL_TEXTURE0)

        gl.glViewport(0, 0, int(fb_width), int(fb_height))

        ortho_projection = mathutils.Matrix(
            (2.0/display_width, 0.0,                   0.0, 0.0),
            (0.0,               2.0/-display_height,   0.0, 0.0),
            (0.0,               0.0,                  -1.0, 0.0),
            (-1.0,               1.0,                   0.0, 1.0)
        )
        # shader.bind()
        shader.setUniformMatrix4("ProjMtx", ortho_projection)
        shader.setUniform1i("Texture", 0)

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
                gl.glScissor(int(x), int(fb_height - w),
                             int(z - x), int(w - y))

                vertices = vtx_buffer_shaped[:, :2]
                uvs = vtx_buffer_shaped[:, 2:4]
                colors = vtx_buffer_shaped.view(np.uint8)[:, 4*4:]
                colors = colors.astype('f') / 255.0

                indices = idx_buffer_np[idx_buffer_offset:
                                        idx_buffer_offset+command.elem_count]

                gl.glBindTexture(gl.GL_TEXTURE_2D, command.texture_id)

                # gl.glBegin(gl.GL_TRIANGLES)
                # for vertex in vertices:
                #     shader
                # shader.

                # batch = batch_for_shader(shader, 'TRIS', {
                #     "Position": vertices,
                #     "UV": uvs,
                #     "Color": colors,
                # }, indices=indices)
                # batch.draw(shader)

                idx_buffer_offset += command.elem_count

        # restore modified GL state
        gl.glUseProgram(last_program)
        gl.glActiveTexture(last_active_texture)
        gl.glBindTexture(gl.GL_TEXTURE_2D, last_texture)
        gl.glBindVertexArray(last_vertex_array)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, last_array_buffer)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, last_element_array_buffer)
        gl.glBlendEquationSeparate(
            last_blend_equation_rgb, last_blend_equation_alpha)
        gl.glBlendFunc(last_blend_src, last_blend_dst)

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

        gl.glViewport(last_viewport[0], last_viewport[1],
                      last_viewport[2], last_viewport[3])
        gl.glScissor(last_scissor_box[0], last_scissor_box[1],
                     last_scissor_box[2], last_scissor_box[3])

    def _invalidate_device_objects(self):
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


class GlobalImgui:
    # Simple Singleton pattern, use GlobalImgui.get() rather
    # than creating your own instances of this calss
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = GlobalImgui()
        return cls._instance

    def __init__(self):
        self.imgui_ctx = None

    def init_imgui(self, scene):
        self.imgui_ctx = imgui.create_context()
        self.imgui_backend = BlenderImguiRenderer(scene)
        self.setup_key_map()
        self.draw_handlers = {}
        self.callbacks = {}
        self.next_callback_id = 0

    def shutdown_imgui(self):
        for SpaceType, draw_handler in self.draw_handlers.items():
            SpaceType.draw_handler_remove(self.draw_handler, 'WINDOW')
        imgui.destroy_context(self.imgui_ctx)
        self.imgui_ctx = None

    def handler_add(self, callback, SpaceType):
        """
        @param callback The draw function to add
        @param SpaceType Can be any class deriving from bpy.types.Space
        @return An identifing handle that must be provided to handler_remove in
                order to remove this callback.
        """
        if self.imgui_ctx is None:
            self.init_imgui()

        if SpaceType not in self.draw_handlers:
            self.draw_handlers[SpaceType] = SpaceType.draw_handler_add(
                self.draw, (SpaceType,), 'WINDOW', 'POST_PIXEL')

        handle = self.next_callback_id
        self.next_callback_id += 1

        self.callbacks[handle] = (callback, SpaceType)

        return handle

    def handler_remove(self, handle):
        if handle not in self.callbacks:
            print(f"Error: invalid imgui callback handle: {handle}")
            return

        del self.callbacks[handle]
        if not self.callbacks:
            self.shutdown_imgui()

    def draw(self, CurrentSpaceType):
        #context = bpy.context
        #eeregion = context.region

        io = imgui.get_io()
        io.display_size = bge.render.getWindowWidth(), bge.render.getWindowHeight()
        io.font_global_scale = 1.0  # context.preferences.view.ui_scale
        imgui.new_frame()

        for cb, SpaceType in self.callbacks.values():
            if SpaceType == CurrentSpaceType:
                cb(context)

        imgui.end_frame()
        imgui.render()
        self.imgui_backend.render(imgui.get_draw_data())

    def setup_key_map(self):
        io = imgui.get_io()
        keys = (
            imgui.KEY_TAB,
            imgui.KEY_LEFT_ARROW,
            imgui.KEY_RIGHT_ARROW,
            imgui.KEY_UP_ARROW,
            imgui.KEY_DOWN_ARROW,
            imgui.KEY_HOME,
            imgui.KEY_END,
            imgui.KEY_INSERT,
            imgui.KEY_DELETE,
            imgui.KEY_BACKSPACE,
            imgui.KEY_ENTER,
            imgui.KEY_ESCAPE,
            imgui.KEY_PAGE_UP,
            imgui.KEY_PAGE_DOWN,
            imgui.KEY_A,
            imgui.KEY_C,
            imgui.KEY_V,
            imgui.KEY_X,
            imgui.KEY_Y,
            imgui.KEY_Z,
        )
        for k in keys:
            # We don't directly bind Blender's event type identifiers
            # because imgui requires the key_map to contain integers only
            io.key_map[k] = k


def imgui_handler_add(callback, SpaceType):
    return GlobalImgui.get().handler_add(callback, SpaceType)


def imgui_handler_remove(handle):
    GlobalImgui.get().handler_remove(handle)



