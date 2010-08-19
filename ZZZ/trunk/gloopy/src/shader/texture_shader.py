# -*- coding: UTF-8 -*-
'''
Created on 05.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from shader.shader_utils import FragShaderFunc

class TextureShaderMix(FragShaderFunc):
    """
    mixes texture shaders by averaging the output values.
    """
    def __init__(self, textureShaders):
        FragShaderFunc.__init__(self, 'mixTexels')
        self.textureShaders = textureShaders
    def code(self):
        code = """
    void %s(vec2 uv, out vec4 col)
    {
        vec4 col = vec4(0.0);
        vec4 texel;
""" % self.name
        for t in self.textureShaders:
            code += """
        %s;
        col += texel;
"""  % t.buildCall("uv", "texel")
        
        return code + """
        col /= %g;
    }
""" % float(len(self.textureShader))

class TextureShader(FragShaderFunc):
    """
    texture shader take as input uv cord and output a color:
        void texShader(vec2 uv, out vec4 col) {}
    """
    def __init__(self, name, textureIndex):
        FragShaderFunc.__init__(self, name)
        self.textureIndex = textureIndex
        self.addUniform("sampler2D", "Texture%d" % textureIndex)

class Sepia(TextureShader):
    DESATURATE_NAME = "sepiaDesaturate"
    TONING_NAME     = "supiaToning"
    
    def __init__(self, textureIndex=0):
        TextureShader.__init__(self, 'sepia', textureIndex)
        self.addConstant( type="float", name=self.DESATURATE_NAME, val=0.0 )
        self.addConstant( type="float", name=self.TONING_NAME, val=1.0 )
        self.addConstant( type="vec3", name="lightColor", val="{ 1.0, 0.9,  0.5  }" )
        self.addConstant( type="vec3", name="darkColor",  val="{ 0.2, 0.05, 0.0  }" )
        self.addConstant( type="vec3", name="grayXfer",   val="{ 0.3, 0.59, 0.11  }" )
    def code(self):
        return """
    void %(NAME)s(vec2 uv, out vec4 col)
    {
        vec3 scnColor = lightColor * texture2D ( Texture%(TEX)d, uv );
        float gray = dot( grayXfer, scnColor );
        vec3 muted = mix( scnColor, gray.xxx, %(DESATURATE)s );
        vec3 sepia = mix( darkColor, lightColor, gray );
        vec3 result = mix( muted, sepia, %(TONING)s );
        col = vec4( result.xyz, 1.0 );
    }
""" % { 'NAME': self.name,
        'TEX': self.textureIndex,
        'TONING': self.TONING_NAME,
        'DESATURATE': self.DESATURATE_NAME }


class Tiles(TextureShader):
    TILES_NAME       = "tilesVal"
    EDGE_WIDTH_NAME  = "tilesEdgeWidth"
    EDGE_COLOR_NAME  = "tilesEdgeColor"
    
    def __init__(self,
                 textureIndex=0,
                 textureSize=(800,600)):
        TextureShader.__init__(self, 'tiles', textureIndex)
        self.textureSize = (float(textureSize[0]), float(textureSize[1]))
        self.addConstant( type="float", name=self.TILES_NAME, val=50000.0 )
        self.addConstant( type="float", name=self.EDGE_WIDTH_NAME, val=0.25 )
        self.addConstant( type="vec3", name=self.EDGE_COLOR_NAME, val="{ 0.0, 0.0, 0.0 }" )
    def code(self):
        return """
    void %(NAME)s(vec2 uv, out vec4 col)
    {
        float thresholdB =  1.0 - %(EDGEW)s;
        float size = 1.0 / %(TILES)s;   
        vec4 buf;
        vec2 texsize = vec2( %(TEXH)g, %(TEXW)g );
        
        buf.xy = uv / texsize;
        buf.zw = buf.xy - mod( buf.xy, size.xx );
        
        vec2 center = buf.zw + ( size/2.0 ).xx;
        vec2 st = ( buf.xy - buf.zw )/size;
        
        if (st.x > thresholdB || st.x < %(EDGEW)s ||
            st.y > thresholdB || st.y < %(EDGEW)s)
        {
            col = vec4( %(ECOL)s, 1.0 );
        } else {
            col = texture2D( Texture%(TEX)d, center*texsize );
        }
        
    }
""" % { 'NAME': self.name,
        'TEX': self.textureIndex,
        'TEXW': self.textureSize[0],
        'TEXH': self.textureSize[1],
        'TILES': self.TILES_NAME,
        'EDGEW': self.EDGE_WIDTH_NAME,
        'ECOL': self.EDGE_COLOR_NAME }

class ConvolutionFilter(TextureShader):
    def __init__(self,
                 name='kernelShader',
                 textureIndex=0,
                 kernel=[],
                 offset=[]):
        TextureShader.__init__(self, name, textureIndex)
        self.kernel = kernel
        self.offset = offset
        self.kernelSize = len(kernel)
        assert(len(offset) == self.kernelSize)
    def buildSum(self):
        code = "        vec4 sum = vec4(0.0);\n"
        for i in range(self.kernelSize):
            code += """
        sum += texture2D( Texture%(TEX)d, uv +
                vec2( %(OFFSETX)g, %(OFFSETX)g ) ) * %(KERNEL)g;
""" % { 'TEX': self.textureIndex,
        'OFFSETX': self.offset[i][0],
        'OFFSETY': self.offset[i][1],
        'KERNEL': self.kernel[i],
        'FAC': self.FACTOR }
        return code;
    def code(self):
        return """
    void %(NAME)s(vec2 uv, out vec4 col)
    {
        %(SUM)s
        col = sum;
    }
""" % { 'NAME': self.name, 'SUM': self.buildSum() }


class ConvolutionFilterFac(ConvolutionFilter):
    FACTOR = "dummyFactor"
    def __init__( self, name='dummy', textureIndex=0, kernel=[], offset=[] ):
        ConvolutionFilter.__init__(self, name, textureIndex, kernel, offset)
    def buildSum(self):
        code = "        vec4 sum = vec4(0.0);\n"
        for i in range(self.kernelSize):
            code += """
        sum += texture2D( Texture%(TEX)d, uv +
                %(FAC)s * vec2( %(OFFSETX)g, %(OFFSETY)g ) ) * %(KERNEL)g;
""" % { 'TEX': self.textureIndex,
        'OFFSETX': self.offset[i][0],
        'OFFSETY': self.offset[i][1],
        'KERNEL': self.kernel[i],
        'FAC': self.FACTOR }
        
        return code;


class EmbossFilter(ConvolutionFilterFac):
    FACTOR = "embossFactor"
    def __init__(self,
                 textureIndex=0,
                 kernel=[],
                 offset=[]):
        ConvolutionFilterFac.__init__(self,
                                     name='embossFilter',
                                     textureIndex=textureIndex,
                                     kernel=kernel,
                                     offset=offset)
        self.addConstant( type="float", name=self.FACTOR, val="1.0" )
        
    def code(self):
        return """
    void %(NAME)s(vec2 uv, out vec4 col)
    {
        %(SUM)s
        col = sum + 0.5;
    }
""" % { 'NAME': self.name, 'SUM': self.buildSum() }

class SharpenFilter(ConvolutionFilterFac):
    FACTOR = "sharpenFactor"
    def __init__(self, textureIndex=0, kernel=[], offset=[]):
        ConvolutionFilterFac.__init__(self, 'sharpenFilter', textureIndex, kernel, offset)
        self.addConstant( type="float", name=self.FACTOR, val="1.0" )

class LaplaceEdgeDetectFilter(ConvolutionFilterFac):
    FACTOR = "laplaceFactor"
    def __init__(self, textureIndex=0, kernel=[], offset=[]):
        ConvolutionFilterFac.__init__(self, 'edgeDetectFilter', textureIndex, kernel, offset)
        self.addConstant( type="float", name=self.FACTOR, val="1.0" )

class MeanFilter(ConvolutionFilterFac):
    FACTOR = "meanFactor"
    def __init__(self, textureIndex=0, kernel=[], offset=[]):
        ConvolutionFilterFac.__init__(self, 'meanFilter', textureIndex, kernel, offset)
        self.addConstant( type="float", name=self.FACTOR, val="1.0" )

class GaussFilter(ConvolutionFilterFac):
    FACTOR = "gaussFactor"
    def __init__(self, textureIndex=0, kernel=[], offset=[]):
        ConvolutionFilterFac.__init__(self, 'gaussFilter', textureIndex, kernel, offset)
        self.addConstant( type="float", name=self.FACTOR, val="1.0" )


"""
            shaderCls = TEXTURE_SHADERS[shaderName]
            step_w = 1.0/self.winSize[0]
            step_h = 1.0/self.winSize[1]
            offset = [
                (-step_w, -step_h), (0.0, -step_h), (step_w, -step_h), 
                (-step_w, 0.0),     (0.0, 0.0),     (step_w, 0.0), 
                (-step_w, step_h),  (0.0, step_h),  (step_w, step_h)
            ]
            if shaderName == 'sepia':
                shaderInstance = shaderCls(textureIndex=0)
            elif shaderName == 'tiles':
                shaderInstance = shaderCls(textureIndex=0,
                                           textureSize=(800,600))
                shaderInstance.constantToUniform(Tiles.TILES_NAME)
                shaderInstance.constantToUniform(Tiles.EDGE_WIDTH_NAME)
            elif shaderName == 'sharpen':
                kernel = [
                    -1.0, -1.0, -1.0,
                    -1.0,  9.0, -1.0,
                    -1.0, -1.0, -1.0
                ]
                shaderInstance = shaderCls(textureIndex=0,
                                           kernel=kernel,
                                           offset=offset)
                shaderInstance.constantToUniform(SharpenFilter.FACTOR)
            elif shaderName == 'emboss':
                kernel = [
                    2.0, 0.0, 0.0,
                    0.0, -1.0, 0.0,
                    0.0, 0.0, -1.0
                ]
                shaderInstance = shaderCls(textureIndex=0,
                                           kernel=kernel,
                                           offset=offset)
                shaderInstance.constantToUniform(EmbossFilter.FACTOR)
            elif shaderName == 'edge_detect':
                kernel = [
                    0.0, 1.0,  0.0,
                    1.0, -4.0, 1.0,
                    0.0, 1.0,  0.0
                ]
                shaderInstance = shaderCls(textureIndex=0,
                                           kernel=kernel,
                                           offset=offset)
                shaderInstance.constantToUniform(LaplaceEdgeDetectFilter.FACTOR)
            elif shaderName == 'mean':
                kernel = [
                    1.0/9.0, 1.0/9.0, 1.0/9.0,
                    1.0/9.0, 1.0/9.0, 1.0/9.0,
                    1.0/9.0, 1.0/9.0, 1.0/9.0
                ]
                shaderInstance = shaderCls(textureIndex=0,
                                           kernel=kernel,
                                           offset=offset)
                shaderInstance.constantToUniform(MeanFilter.FACTOR)
            elif shaderName == 'gauss':
                kernel = [
                    1.0/16.0, 2.0/16.0, 1.0/16.0,
                    2.0/16.0, 4.0/16.0, 2.0/16.0,
                    1.0/16.0, 2.0/16.0, 1.0/16.0
                ]
                shaderInstance = shaderCls(textureIndex=0,
                                           kernel=kernel,
                                           offset=offset)
                shaderInstance.constantToUniform(GaussFilter.FACTOR)
            else:
                shaderInstance = shaderCls(textureIndex=0)
            shaderInstance.setArgs(["uv", "col"])
"""
