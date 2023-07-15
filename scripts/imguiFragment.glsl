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