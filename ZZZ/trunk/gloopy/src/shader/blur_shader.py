# -*- coding: UTF-8 -*-
'''
Created on 03.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from shader_utils import FragShaderFunc, VertShaderFunc
from texture_shader import TextureShader

class RadialBlurFrag(FragShaderFunc):
    """
    blurs by distance to center.
    """
    
    # distance between samples
    BLUR_DIST     = "radialBlurDist"
    # influence of texel distance to center
    BLUR_STRENGTH = "radialBlurStrength"
    
    def __init__(self,
                 textureIndex=0):
        FragShaderFunc.__init__(self, "radialBlur")
        self.textureIndex = textureIndex
        self.addUniform(type="sampler2D", name="Texture%d" % textureIndex)
        self.addConstant(type="float", name=self.BLUR_STRENGTH, val=7.0 )
        self.addConstant(type="float", name=self.BLUR_DIST, val=0.1 )
        # 10 samples next to the current texel
        self.offsets = [-0.08,-0.05,-0.03,-0.02,-0.01,0.01,0.02,0.03,0.05,0.08]

    def code(self):
        code = """
    void %(NAME)s(out vec4 outcol)
    {
        // a vector pointing to the middle of the screen
        vec2 dir = 0.5 - gl_TexCoord[0]; 
        // distance to the center of the screen
        float dist = sqrt(dir.x*dir.x + dir.y*dir.y); 
        dir = dir/dist;
        // original color
        vec4 texel = texture2D( Texture%(TEX)d, gl_TexCoord[0] ); 
        vec4 sum = texel;
""" % { 'NAME': self.name, 'TEX': self.textureIndex }
        
        for offset in self.offsets:
            code += "        sum += texture2D( Texture%d, " % self.textureIndex+\
                    "gl_TexCoord[0] + dir * %g * %s );\n" % (offset, self.BLUR_DIST)
        return code + """
         sum *= 1.0/%(NSAMPLES)f;
         outcol = mix( texel, sum, clamp( dist * %(BULRS)s , 0.0, 1.0 ));
    }
""" % { 'NSAMPLES': float(len(self.offsets) + 1),
        'BULRS': self.BLUR_STRENGTH }


RADIAL_BLUR_TEXCO  = "radialBlurTexco"
class RadialBlurFastVert(VertShaderFunc):
    """
    radial blur based on nvidia example.
    """
    
    # distance between samples
    BLUR_DIST   = "radialBlurFastDist"
    # blur origin, (0.5, 0.5) is centered blur with untranslated texture
    BLUR_CENTER = "radialBlurFastCenter"
    
    def __init__(self,
                 numSamples=8,
                 texelSize=1.0/256.0):
        VertShaderFunc.__init__(self, 'radialBlurFast')
        self.numSamples = numSamples
        self.texelSize = texelSize
        
        self.addVarying("vec2[%d]" % numSamples, RADIAL_BLUR_TEXCO)
        
        self.addConstant( "vec2", self.BLUR_CENTER, (0.5, 0.5))
        self.addConstant( "float", self.BLUR_DIST, 0.14)
        
    def code(self):
        return """
    void %(NAME)s()
    {
        vec2 s = gl_MultiTexCoord0 + %(TEXELS)f * 0.5 - %(BLURC)s;
        for(int i=0; i < %(NSAMPLES_INT)d ; i++) {
            %(TEXCO)s[i].xy = s * ( 1.0 - %(BLURD)s *
                    ( float(i) / %(NSAMPLES)f ) ) + %(BLURC)s;
       }
    }
""" % { 'NAME': self.name,
        'NSAMPLES_INT': self.numSamples,
        'NSAMPLES': float(self.numSamples - 1),
        'TEXELS': self.texelSize,
        'BLURD': self.BLUR_DIST,
        'BLURC': self.BLUR_CENTER,
        'TEXCO': RADIAL_BLUR_TEXCO }
class RadialBlurFastFrag(TextureShader):
    """
    radial blur based on nvidia example.
    """
    
    def __init__(self,
                 textureIndex=0,
                 numSamples=8):
        TextureShader.__init__(self, "radialBlurFast", textureIndex)
        self.numSamples = numSamples
        self.addVarying("vec2[%d]" % numSamples, RADIAL_BLUR_TEXCO)

    def code(self):
        return """
    void %(NAME)s(out vec4 col)
    {
        vec4 c = vec4(0.0);
        for(int i = 0; i < %(NSAMPLES_INT)d ; i++) {
            c += texture2D( Texture%(TEX)d, %(TEXCO)s[i].xy );
        }
        col = c / %(NSAMPLES_FLOAT)d;
    }
""" % { 'NAME': self.name,
        'TEX': self.textureIndex,
        'NSAMPLES_INT': self.numSamples,
        'NSAMPLES_FLOAT': float(self.numSamples),
        'TEXCO': RADIAL_BLUR_TEXCO }
