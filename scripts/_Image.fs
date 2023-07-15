uniform float bgl_RenderedTextureWidth;
uniform float bgl_RenderedTextureHeight;
uniform sampler2D bgl_RenderedTexture;
uniform sampler2D bgl_DataTextures[7];
vec2 iResolution = vec2(bgl_RenderedTextureWidth, bgl_RenderedTextureHeight); // viewport resolution (in pixels)
uniform sampler2D iChannel0; //! buffer[xbuf: 1, wrap: GL_CLAMP_TO_EDGE, mipmap: false, filter: GL_NEAREST]

//set overall bloom intensity.
#define intensity 0.8

//set overall exponentiation factor.
#define power 2.4
//2.4

vec3 bloomTile(float lod, vec2 offset, vec2 uv)
{
//    vec3 color1 = texture(bgl_RenderedTexture, uv * exp2(-lod) + offset).rgb;
    vec3 color2 = texture(iChannel0, uv * exp2(-lod) + offset).rgb;
        
    return color2;
}

vec3 getBloom(vec2 uv){

    vec3 blur = vec3(0.0);
    blur += pow(bloomTile(2.0, vec2(0.0,0.0), uv),vec3(2.2))*.25;
    blur += pow(bloomTile(3.0, vec2(0.3,0.0), uv),vec3(2.0))*.20;
    blur += pow(bloomTile(4.0, vec2(0.0,0.4), uv),vec3(1.8))*.15;
    blur += pow(bloomTile(5.0, vec2(.25,0.4), uv),vec3(1.6))*.10;
    blur += pow(bloomTile(6.0, vec2(.45,0.4), uv),vec3(1.4))*.05;

    return blur * intensity;
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
	vec2 uv = fragCoord.xy / iResolution.xy;
    
    vec3 color = texture(bgl_RenderedTexture, uv).rgb;
    color += pow(getBloom(uv), vec3(power));
    
	fragColor = vec4(max(color,0.0),1.0);
}

void main() {
    vec4 color = vec4(0.0, 0.0, 0.0, 1.0);
    mainImage(color, gl_FragCoord.xy);
        
    gl_FragColor = color;
}