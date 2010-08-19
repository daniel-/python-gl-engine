# -*- coding: UTF-8 -*-
'''
Created on 05.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

"""
Bloom (sometimes referred to as light bloom or glow)
is a effect to reproduce an imaging artifact of real-world cameras.
The effect produces fringes (or feathers) of light around very bright objects in an image.
"""

from texture_shader import ConvolutionFilterFac

class BlurBloomFrag(ConvolutionFilterFac):
    FACTOR = "bloomFactor"
    
    def __init__(self, textureIndex=0):
        kernel = [
            0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
            0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
            0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
            0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
            0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
            0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
            0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
            0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25,
            0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25
        ]
        offset = [
            (-3, -4), (-2, -4), (-1, -4), (0, -4), (1, -4), (2, -4), (3, -4),
            (-3, -3), (-2, -3), (-1, -3), (0, -3), (1, -3), (2, -3), (3, -3),
            (-3, -2), (-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (3, -2),
            (-3, -1), (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1), (3, -1),
            (-3,  0), (-2,  0), (-1,  0), (0,  0), (1,  0), (2,  0), (3,  0),
            (-3,  1), (-2,  1), (-1,  1), (0,  1), (1,  1), (2,  1), (3,  1),
            (-3,  2), (-2,  2), (-1,  2), (0,  2), (1,  2), (2,  2), (3,  2),
            (-3,  3), (-2,  3), (-1,  3), (0,  3), (1,  3), (2,  3), (3,  3),
            (-3,  4), (-2,  4), (-1,  4), (0,  4), (1,  4), (2,  4), (3,  4)
        ]
        offset = map(lambda x: (float(x[0])*0.004, float(x[1])*0.004), offset)
        
        ConvolutionFilterFac.__init__(self,
                                      name='blurBloom',
                                      textureIndex=textureIndex,
                                      kernel=kernel,
                                      offset=offset)
        self.addConstant( type="float", name=self.FACTOR, val="1.0" )
    def code(self):
        return """
    void %(NAME)s(vec2 uv, out vec4 col)
    {
        vec4 texel = texture2D(Texture%(TEX)d, uv);
        %(SUM)s
        if (texel.r < 0.3) {
            col = sum*sum*0.012 + texel;
        } else if (texel.r < 0.5) {
            col = sum*sum*0.009 + texel;
        } else {
            col = sum*sum*0.0075 + texel;
        }
    }
""" % { 'NAME': self.name, 'TEX': self.textureIndex, 'SUM': self.buildSum() }
