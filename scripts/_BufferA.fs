uniform float bgl_RenderedTextureWidth;
uniform float bgl_RenderedTextureHeight;
uniform sampler2D bgl_RenderedTexture;
uniform sampler2D iChannel0;
//uniform sampler2D bgl_DataTextures[7];
// this line above is how to call the Attachments layers^^^

//average over frames: bigger values make trail effect.
#define average 128

// max fadeTime 1.0: higher than 1 make it burst.
#define fadeTime 0.99125

// set sampling: max 5
#define samples 3


vec2 iResolution = vec2(bgl_RenderedTextureWidth, bgl_RenderedTextureHeight); // viewport resolution (in pixels)

vec3 makeBloom(float lod, vec2 offset, vec2 bCoord){
    
    vec2 pixelSize = 1.0 / vec2(iResolution.x, iResolution.y);

    offset += pixelSize;
    float lodFactor = exp2(lod);

    vec3 bloom = vec3(0.0);
    vec3 bloom2 = vec3(0.0);
    
    vec2 scale = lodFactor * pixelSize;
    vec2 coord = (bCoord.xy-offset)*lodFactor;
    float totalWeight = 0.0;

    if (any(greaterThanEqual(abs(coord - 0.5), scale + 0.5)))
        return vec3(0.0);

    for (int i = -samples; i < samples; i++) {
        for (int j = -samples; j < samples; j++) {

            float wg = pow(1.0-length(vec2(i,j)) * 0.125,6.0);
            bloom = pow(texture(iChannel0,gl_FragCoord.xy/ iResolution.xy).rgb,vec3(2.2))*wg + bloom;
            
            bloom = bloom*(average-1);
            bloom2 = pow(texture(bgl_RenderedTexture,vec2(i,j)*scale+lodFactor*pixelSize+coord,lod).rgb, vec3(2.2))*wg+bloom2;   
            bloom = vec3(bloom+bloom2)*fadeTime;
            bloom = bloom/average;
            totalWeight += wg;
            
        }
    }

    bloom /= totalWeight;

    return max(bloom,0.0);
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = fragCoord / iResolution.xy;
    vec3 blur = vec3(0.0);
    
	    blur += makeBloom(2.0,vec2(0.0,0.0), uv);
	    blur += makeBloom(3.0,vec2(0.3,0.0), uv);
		blur += makeBloom(4.0,vec2(0.0,0.4), uv);
		blur += makeBloom(5.0,vec2(.25,0.4), uv);
		blur += makeBloom(6.0,vec2(.45,0.4), uv);

    fragColor = vec4(pow(blur, vec3(.4545)),1.0);
}

void main() {
    vec4 color = vec4(0.0, 0.0, 0.0, 1.0);
    mainImage(color, gl_FragCoord.xy);

    gl_FragColor = color;
}
