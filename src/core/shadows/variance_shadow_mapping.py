# -*- coding: UTF-8 -*-
'''
Created on 30.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''
from shader.shader_utils import VertShaderFunc, FragShaderFunc

VSM_VARYING_POS = "vPos"
class VSMDepthVert(VertShaderFunc):
    def __init__(self):
        VertShaderFunc.__init__(self, name="vsmShadow")
        self.addVarying(type="vec4", name=VSM_VARYING_POS)
    def code(self):
        return """
    void %(NAME)s()
    {
        %(POS_VAR)s = gl_Position;
    }
""" % { 'NAME': self.name, 'POS_VAR': VSM_VARYING_POS }
class VSMDepthFrag(FragShaderFunc):
    def __init__(self):
        FragShaderFunc.__init__(self, name="vsmShadow")
        self.addVarying(type="vec4", name=VSM_VARYING_POS)
    def code(self):
        return """
    void %(NAME)s(out vec4 color)
    {
        float depth = %(POS_VAR)s.z / %(POS_VAR)s.w ;
        //Don't forget to move away from unit cube ([-1,1]) to [0,1] coordinate system
        depth = depth * 0.5 + 0.5;
    
        float moment1 = depth;
        float moment2 = depth * depth;
    
        // Adjusting moments (this is sort of bias per pixel) using derivative
        float dx = dFdx(depth);
        float dy = dFdy(depth);
        moment2 += 0.25*(dx*dx+dy*dy) ;
    
        color = vec4( moment1,moment2, 0.0, 0.0 );
    }
""" % { 'NAME': self.name, 'POS_VAR': VSM_VARYING_POS }
class VSMVert(VertShaderFunc):
    PROJ_NAME = "vsmShadowProj"
    def __init__(self, textureIndex=0):
        VertShaderFunc.__init__(self, name="vsmShadow")
        self.textureIndex = textureIndex
    def code(self):
        return """
    void %(NAME)s(vec4 v)
    {
        %(SHADOWPROJ)s = gl_TextureMatrix[%(TEX)d] * gl_Vertex;
    }
""" % { 'NAME': self.name,
        'TEX': self.textureIndex,
        'SHADOWPROJ': self.PROJ_NAME }
class VSMFrag(FragShaderFunc):
    PROJ_NAME = "vsmShadowProj"
    def __init__(self):
        FragShaderFunc.__init__(self, name="vsmShadow")
    def code(self):
        return """
    vec4 ShadowCoordPostW;
    
    float chebyshevUpperBound( float distance)
    {
        vec2 moments = texture2D(%(SHADOWMAP)s, ShadowCoordPostW.xy).rg;
        
        // Surface is fully lit. as the current fragment is before the light occluder
        if (distance <= moments.x)
            return 1.0 ;
    
        // The fragment is either in shadow or penumbra. We now use chebyshev's upperBound to check
        // How likely this pixel is to be lit (p_max)
        float variance = moments.y - (moments.x*moments.x);
        variance = max(variance,0.00002);
    
        float d = distance - moments.x;
        float p_max = variance / (variance + d*d);
    
        return p_max;
    }

    void %(NAME)s(out float shadow)
    {
        ShadowCoordPostW = %(SHADOWPROJ)s / %(SHADOWPROJ)s.w;
        //ShadowCoordPostW = ShadowCoordPostW * 0.5 + 0.5; This is done via a bias matrix in main.c
        
        shadow = chebyshevUpperBound(ShadowCoordPostW.z);
    }
""" % { 'NAME': self.name,
        'SHADOWMAP': self.MAP_NAME,
        'SHADOWPROJ': self.PROJ_NAME }
