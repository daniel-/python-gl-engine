# -*- coding: UTF-8 -*-
'''
Created on 30.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from shader.shader_utils import FragShaderFunc
from core.light.normal_mapping import BumpMapVert

class ParallaxFrag(FragShaderFunc):
    """
    ... also known as offset mapping, texel displacement shader
    implements a simple parallax shader, using a normal and a height map.
    the initial surface is at height value 0.5 here.
    """
    def __init__(self,
                 enabledLights=[0],
                 normalTexture=0,
                 heightTexture=1,
                 scaleBias=(0.04, 0.02)):
        FragShaderFunc.__init__(self, name='parallax')
        self.numLights = len(enabledLights)
        self.enabledLights = enabledLights
        self.normalTexture = normalTexture
        self.heightTexture = heightTexture
        self.scaleBias = scaleBias
        
        self.addUniform(type="sampler2D", name="Texture%d" % normalTexture)
        self.addUniform(type="sampler2D", name="Texture%d" % heightTexture)
    
    def code(self):
        return """
    void %(NAME)s(vec3 v, inout vec2 uv, inout vec3 n)
    {
        // height of untransformed point
        float height = texture2D( Texture%(HEIGHT)d, uv).r;
        
        float buf = height * %(BIAS0)g - %(BIAS1)g;
        vec3 eye = normalize(v);
        uv = uv + (eye.xy * buf);
        
        // calculated bumped normal
        n = normalize( 2.0 * texture2D( Texture%(NORMAL)d, uv ).xyz - 1.0);
    }
""" % { 'NAME': self.name,
        'HEIGHT' : self.heightTexture,
        'NORMAL' : self.normalTexture,
        'BIAS0' : self.scaleBias[0],
        'BIAS1' : self.scaleBias[1] }
class ParallaxVert(BumpMapVert):
    def __init__(self, enabledLights=[0]):
        BumpMapVert.__init__(self, enabledLights=enabledLights)
        self.name = "parallax"



class ParallaxOffsetFrag(FragShaderFunc):
    """
    implements a parallax offset shader, using a normal and a height map.
    the initial surface is at height value 1.0 here.
    """
    def __init__(self,
                 enabledLights=[0],
                 normalTexture=0,
                 heightTexture=1):
        FragShaderFunc.__init__(self, name='parallaxO')
        self.numLights = len(enabledLights)
        self.enabledLights = enabledLights
        self.normalTexture = normalTexture
        self.heightTexture = heightTexture
        
        self.addUniform(type="sampler2D", name="Texture%d" % normalTexture)
        self.addUniform(type="sampler2D", name="Texture%d" % heightTexture)
    
    def code(self):
        return """
    void %(NAME)s(vec3 v, inout vec2 uv, out vec3 n)
    {
        // calculate uv using cut points of height map
        // uv = doParallax()
        uv = vec2(0.0);
        // calculated bumped normal
        n = normalize( 2.0 * texture2D( Texture%(NORMAL)d, uv ).xyz - 1.0);
    }
""" % { 'NAME': self.name,
        'HEIGHT' : self.heightTexture,
        'NORMAL' : self.normalTexture }
class ParallaxOffsetVert(BumpMapVert):
    def __init__(self, enabledLights=[0]):
        BumpMapVert.__init__(self, enabledLights=enabledLights)
        self.name = "parallaxO"
