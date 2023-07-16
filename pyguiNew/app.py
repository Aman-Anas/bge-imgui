from . import pygui
import glfw
import OpenGL.GL as gl
from pygui_demo import demo_fonts_init, pygui_demo_window


vsync_enabled = pygui.Bool(True)
show_imgui_demo = pygui.Bool(True)
show_pygui_demo = pygui.Bool(True)


def render():
    pygui.begin("Hello from pygui!")
    pygui.text("FPS: {}".format(round(pygui.get_io().framerate)))
    if pygui.checkbox("Enable vsync", vsync_enabled):
        glfw.swap_interval(int(vsync_enabled.value))
    pygui.checkbox("Show pygui Demo", show_pygui_demo)
    pygui.same_line()
    pygui.checkbox("Show ImGui Demo", show_imgui_demo)
    pygui.end()

    if show_imgui_demo:
        pygui.show_demo_window()

    if show_pygui_demo:
        pygui_demo_window()


def main(cont):
    if not glfw.init():
        return

    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
    glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)

    window = glfw.create_window(1024, 768, "Hello World!", None, None)
    if window is None:
        print("Failed to create window! Terminating")
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # Vsync:
    # 1: On
    # 0: Off
    glfw.swap_interval(int(vsync_enabled.value))

    # Setup imgui
    pygui.create_context()

    # Setup config flags
    io = pygui.get_io()
    io.config_flags |= pygui.CONFIG_FLAGS_NAV_ENABLE_KEYBOARD
    io.config_flags |= pygui.CONFIG_FLAGS_NAV_ENABLE_GAMEPAD
    io.config_flags |= pygui.CONFIG_FLAGS_DOCKING_ENABLE
    io.config_flags |= pygui.CONFIG_FLAGS_VIEWPORTS_ENABLE

    pygui.impl_glfw_init_for_open_gl(window, True)
    pygui.impl_open_gl3_init()

    # Check opengl version
    print("Opengl version: {}".format(gl.glGetString(gl.GL_VERSION).decode()))
    print("glfw version: {}.{}.{}".format(glfw.VERSION_MAJOR,
          glfw.VERSION_MINOR, glfw.VERSION_REVISION))
    print("ImGui version: {}".format(pygui.get_version()))

    # Try out different styles
    pygui.style_colors_dark()
    # pygui.style_colors_light()
    # pygui.style_colors_classic()
    clear_color = (0.45, 0.55, 0.6, 1.0)

    pygui.IM_ASSERT(True, "You should never see this")
    try:
        pygui.IM_ASSERT(False, "Checking pygui's IM_ASSERT. Raises ")
    except pygui.ImGuiError as e:
        print(e, end="")
        if isinstance(e, AssertionError):
            print("AssertionError")
        else:
            print("pygui.ImGuiError")

    demo_fonts_init()

    try:
        while not glfw.window_should_close(window):
            glfw.poll_events()
            pygui.impl_open_gl3_new_frame()
            pygui.impl_glfw_new_frame()
            pygui.new_frame()

            render()

            pygui.render()
            glfw.make_context_current(window)

            gl.glViewport(
                0, 0, int(io.display_size[0]), int(io.display_size[1]))
            gl.glClearColor(*clear_color)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

            draw_data = pygui.get_draw_data()
            pygui.impl_open_gl3_render_draw_data(draw_data)

            if io.config_flags & pygui.CONFIG_FLAGS_VIEWPORTS_ENABLE:
                backup_current_window = glfw.get_current_context()
                pygui.update_platform_windows()
                pygui.render_platform_windows_default()
                glfw.make_context_current(backup_current_window)

            glfw.swap_buffers(window)
    except KeyboardInterrupt:
        print("Closing")

    pygui.impl_open_gl3_shutdown()
    pygui.impl_glfw_shutdown()
    pygui.destroy_context()
    glfw.destroy_window(window)
    glfw.terminate()


if __name__ == "__main__":
    main()
