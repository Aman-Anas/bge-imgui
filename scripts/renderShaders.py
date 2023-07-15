VERTEX_SHADER = """
uniform sampler2D colorMap;

void main()
{
    gl_Position = gl_Vertex;
}
"""


FRAGMENT_SHADER = """
uniform sampler2D bgl_RenderedTexture;
uniform sampler2D bgl_DepthTexture;
uniform float bgl_RenderedTextureWidth;
uniform float bgl_RenderedTextureHeight;


#define texCoord gl_TexCoord[0].st

//uniform sampler2D inTex;

float width = bgl_RenderedTextureWidth;
float height = bgl_RenderedTextureHeight;

vec4 srgb_to_linear(vec4 srgb) {
    return mix(
        pow((srgb + 0.055) / 1.055, vec4(2.4)),
        srgb / 12.92,
        step(srgb, vec4(0.04045))
    );
}

void main()
{   
    vec4 texcolor = texture2D(bgl_RenderedTexture, texCoord);
    gl_FragColor = texcolor;
}
"""

FRAGMENT_SHADER2 = """
uniform float bgl_RenderedTextureWidth;
uniform float bgl_RenderedTextureHeight;
uniform sampler2D bgl_RenderedTexture;
uniform sampler2D bgl_DataTextures[7];
vec2 iResolution = vec2(bgl_RenderedTextureWidth, bgl_RenderedTextureHeight); // viewport resolution (in pixels)
uniform sampler2D iChannel0; //! buffer[xbuf: 1, wrap: GL_CLAMP_TO_EDGE, mipmap: false, filter: GL_NEAREST]

in vec2 Frag_UV;
in vec4 Frag_Color;
vec4 Out_Color;

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
    Out_Color = Frag_Color * texture(bgl_RenderedTexture, Frag_UV.st);
    Out_Color.rgba = srgb_to_linear(Out_Color.rgba);
    vec4 color = vec4(0.0, 0.0, 0.0, 1.0);
    gl_FragColor = texture2D(bgl_RenderedTexture, Frag_UV / iResolution);
}"""
