from .core import *

ImGuiError = core.get_imgui_error()
if ImGuiError is None:
    ImGuiError = AssertionError


import OpenGL.GL as gl
from PIL import Image

# From https://stackoverflow.com/questions/72325672/opengl-doesnt-draw-anything-if-i-use-pil-or-pypng-to-load-textures
def load_image(image: Image) -> int:
    convert = image.convert("RGBA")
    image_data = convert.tobytes()
    # image_data = convert.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()
    w = image.width
    h = image.height

    # create the texture in VRAM
    texture: int = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture)

    # configure some texture settings
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT) # when you try to reference points beyond the edge of the texture, how should it behave?
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT) # in this case, repeat the texture data
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR) # when you zoom in, how should the new pixels be calculated?
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR) # when you zoom out, how should the existing pixels be combined?
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_BASE_LEVEL, 0)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAX_LEVEL, 0)

    # load texture onto the GPU
    gl.glTexImage2D(
        gl.GL_TEXTURE_2D,    # where to load texture data
        0,                   # mipmap level
        gl.GL_RGBA8,         # format to store data in
        w,                   # image dimensions
        h,                   #
        0,                   # border thickness
        gl.GL_RGBA,          # format data is provided in
        gl.GL_UNSIGNED_BYTE, # type to read data as
        image_data
    )          # data to load as texture
    # gl.debug.check_gl_error()

    # generate smaller versions of the texture to save time when its zoomed out
    gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

    # clean up afterwards
    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
    return texture
