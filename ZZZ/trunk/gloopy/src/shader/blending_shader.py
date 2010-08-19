# -*- coding: UTF-8 -*-
'''
Created on 02.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from shader.shader_utils import FragShaderFunc
from core.textures.texture import Texture2D

###################################################################
# NOTE: most shader functions are copied from blender glsl code.
###################################################################

### HELPER FUNCTIONS ###

rgb_to_hsv = """
    void rgb_to_hsv(vec4 rgb, out vec4 col2)
    {
        float cmax, cmin, h, s, v, cdelta;
        vec3 c;
    
        cmax = max(rgb[0], max(rgb[1], rgb[2]));
        cmin = min(rgb[0], min(rgb[1], rgb[2]));
        cdelta = cmax-cmin;
    
        v = cmax;
        if (cmax!=0.0)
            s = cdelta/cmax;
        else {
            s = 0.0;
            h = 0.0;
        }
    
        if (s == 0.0) {
            h = 0.0;
        }
        else {
            c = (vec3(cmax, cmax, cmax) - rgb.xyz)/cdelta;
    
            if (rgb.x==cmax) h = c[2] - c[1];
            else if (rgb.y==cmax) h = 2.0 + c[0] -  c[2];
            else h = 4.0 + c[1] - c[0];
    
            h /= 6.0;
    
            if (h<0.0)
                h += 1.0;
        }
    
        col2 = vec4(h, s, v, rgb.w);
    }
"""

hsv_to_rgb = """
    void hsv_to_rgb(vec4 hsv, out vec4 col2)
    {
        float i, f, p, q, t, h, s, v;
        vec3 rgb;
    
        h = hsv[0];
        s = hsv[1];
        v = hsv[2];
    
        if(s==0.0) {
            rgb = vec3(v, v, v);
        }
        else {
            if(h==1.0)
                h = 0.0;
            
            h *= 6.0;
            i = floor(h);
            f = h - i;
            rgb = vec3(f, f, f);
            p = v*(1.0-s);
            q = v*(1.0-(s*f));
            t = v*(1.0-(s*(1.0-f)));
            
            if (i == 0.0) rgb = vec3(v, t, p);
            else if (i == 1.0) rgb = vec3(q, v, p);
            else if (i == 2.0) rgb = vec3(p, v, t);
            else if (i == 3.0) rgb = vec3(p, q, v);
            else if (i == 4.0) rgb = vec3(t, p, v);
            else rgb = vec3(v, p, q);
        }
    
        col2 = vec4(rgb, hsv.w);
    }
"""

### 1 COLOR SHADER FUNCTIONS ###

class Invert(FragShaderFunc):
    def __init__(self):
        FragShaderFunc.__init__(self, name='invert')
        self.facVar = "invFac"
        self.addConstant(type="float", name=self.facVar, val=1.0)
    def code(self):
        return """
    void %s(inout vec4 col)
    {
        col.xyz = mix(col.xyz, vec3(1.0, 1.0, 1.0) - col.xyz, %s);
    }
""" % (self.name, self.facVar)

class Brightness(FragShaderFunc):
    def __init__(self):
        FragShaderFunc.__init__(self, name='brightness')
        self.facVar = "brightnessFac"
        self.addConstant(type="float", name=self.facVar, val=1.0)
    def code(self):
        return """
    void %s(inout vec4 col)
    {
        col.xyz = col.xyz * %s;
    }
""" % (self.name, self.facVar)

class Contrast(FragShaderFunc):
    def __init__(self):
        FragShaderFunc.__init__(self, name='contrast')
        self.facVar = "contrastFac"
        self.addConstant(type="float", name=self.facVar, val=1.0)
    def code(self):
        return """
    void %s(inout vec4 col)
    {
        float buf = %s * 0.5 - 0.5;
        if (col.x > 0.5) {
            col.x = clamp( col.x + buf, 0.5, 1.0);
        } else {
            col.x = max( 0.0, 0.5*(2.0*col.x + 1.0 - %s) );
        }
        if (col.y > 0.5) {
            col.y = clamp( col.y + buf, 0.5, 1.0);
        } else {
            col.y = max( 0.0, 0.5*(2.0*col.y + 1.0 - %s) );
        }
        if (col.z > 0.5) {
            col.z = clamp( col.x + buf, 0.5, 1.0);
        } else {
            col.z = max( 0.0, 0.5*(2.0*col.z + 1.0 - %s) );
        }
    }
""" % (self.name)

### 2 COLOR SHADER FUNCTIONS ###

# abstract baseclass for 2 color blenders
class TextureBlenderCol2(FragShaderFunc):
    def __init__(self, name):
        FragShaderFunc.__init__(self, name=name)
        self.facVar = "%sFac" % name
        self.addConstant(type="float", name=self.facVar, val=1.0)

class Mix(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_mix')
    def code(self):
        return """
    void %s(vec4 col1, inout vec4 col2)
    {
        col2.xyz = mix(col2.xyz, col1.xyz, %s);
    }
""" % (self.name, self.facVar)

class Add(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_add')
    def code(self):
        return """
    void %s(vec4 col1, inout vec4 col2)
    {
        col2.rgb = mix(col2.rgb, col2.rgb + col1.rgb, %s);
    }
""" % (self.name, self.facVar)


class Mul(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_mul')
    def code(self):
        return """
    void %s(vec4 col1, inout vec4 col2)
    {
        col2.xyz = mix(col2.xyz, col2.xyz * col1.xyz, %s);
    }
""" % (self.name, self.facVar)


class Screen(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_screen')
    def code(self):
        return """
    void %s(vec4 col1, inout vec4 col2)
    {
        float facm = 1.0 - %s;

        col2.xyz = vec3(1.0) - (vec3(facm) + %s*(vec3(1.0) - col1.xyz))*(vec3(1.0) - col2.xyz);
    }
""" % (self.name, self.facVar, self.facVar)

class Overlay(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_overlay')
    def code(self):
        return """
    void %(NAME)s(vec4 col1, inout vec4 col2)
    {
        float facm = 1.0 - %(FAC)s;
    
        if(col2.r < 0.5)
            col2.r *= facm + 2.0* %(FAC)s *col1.r;
        else
            col2.r = 1.0 - (facm + 2.0* %(FAC)s *(1.0 - col1.r))*(1.0 - col2.r);
    
        if(col2.g < 0.5)
            col2.g *= facm + 2.0* %(FAC)s *col1.g;
        else
            col2.g = 1.0 - (facm + 2.0* %(FAC)s *(1.0 - col1.g))*(1.0 - col2.g);
    
        if(col2.b < 0.5)
            col2.b *= facm + 2.0* %(FAC)s *col1.b;
        else
            col2.b = 1.0 - (facm + 2.0* %(FAC)s *(1.0 - col1.b))*(1.0 - col2.b);
    }
""" % { 'NAME': self.name, 'FAC': self.facVar }


class Sub(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_sub')
    def code(self):
        return """
    void %s(vec4 col1, inout vec4 col2)
    {
        col2.xyz = mix(col2.xyz, col2.xyz - col1.xyz, %s);
    }
""" % (self.name, self.facVar)


class Div(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_div')
    def code(self):
        return """
    void %(NAME)s(vec4 col1, inout vec4 col2)
    {
        float facm = 1.0 - %(FAC)s;
    
        if(col1.r != 0.0) col2.r = facm*col2.r + %(FAC)s *col2.r/col1.r;
        if(col1.g != 0.0) col2.g = facm*col2.g + %(FAC)s *col2.g/col1.g;
        if(col1.b != 0.0) col2.b = facm*col2.b + %(FAC)s *col2.b/col1.b;
    }
""" % { 'NAME': self.name, 'FAC': self.facVar }


class Diff(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_diff')
    def code(self):
        return """
    void %s(vec4 col1, inout vec4 col2)
    {
        col2.xyz = mix(col2.xyz, abs(col2.xyz - col1.xyz), %s);
    }
""" % (self.name, self.facVar)


class Dark(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_dark')
    def code(self):
        return """
    void %s(vec4 col1, inout vec4 col2)
    {
        col2.rgb = min(col2.rgb, col1.rgb*%s);
    }
""" % (self.name, self.facVar)


class Light(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_light')
    def code(self):
        return """
    void %s(vec4 col1, inout vec4 col2)
    {
        col2.rgb = max(col2.rgb, col1.rgb*%s);
    }
""" % (self.name, self.facVar)


class Dodge(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_dodge')
    def code(self):
        return """
    void %(NAME)s(vec4 col1, inout vec4 col2)
    {
        if(col2.r != 0.0) {
            float tmp = 1.0 - %(FAC)s *col1.r;
            if(tmp <= 0.0)
                col2.r = 1.0;
            else if((tmp = col2.r/tmp) > 1.0)
                col2.r = 1.0;
            else
                col2.r = tmp;
        }
        if(col2.g != 0.0) {
            float tmp = 1.0 - %(FAC)s *col1.g;
            if(tmp <= 0.0)
                col2.g = 1.0;
            else if((tmp = col2.g/tmp) > 1.0)
                col2.g = 1.0;
            else
                col2.g = tmp;
        }
        if(col2.b != 0.0) {
            float tmp = 1.0 - %(FAC)s *col1.b;
            if(tmp <= 0.0)
                col2.b = 1.0;
            else if((tmp = col2.b/tmp) > 1.0)
                col2.b = 1.0;
            else
                col2.b = tmp;
        }
    }
""" % { 'NAME': self.name, 'FAC': self.facVar }


class Burn(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_burn')
    def code(self):
        return """
    void %(NAME)s(vec4 col1, inout vec4 col2)
    {
        float tmp, facm = 1.0 - %(FAC)s ;
    
        tmp = facm + %(FAC)s *col1.r;
        if(tmp <= 0.0)
            col2.r = 0.0;
        else if((tmp = (1.0 - (1.0 - col2.r)/tmp)) < 0.0)
            col2.r = 0.0;
        else if(tmp > 1.0)
            col2.r = 1.0;
        else
            col2.r = tmp;
    
        tmp = facm + %(FAC)s *col1.g;
        if(tmp <= 0.0)
            col2.g = 0.0;
        else if((tmp = (1.0 - (1.0 - col2.g)/tmp)) < 0.0)
            col2.g = 0.0;
        else if(tmp > 1.0)
            col2.g = 1.0;
        else
            col2.g = tmp;
    
        tmp = facm + %(FAC)s *col1.b;
        if(tmp <= 0.0)
            col2.b = 0.0;
        else if((tmp = (1.0 - (1.0 - col2.b)/tmp)) < 0.0)
            col2.b = 0.0;
        else if(tmp > 1.0)
            col2.b = 1.0;
        else
            col2.b = tmp;
    }
""" % { 'NAME': self.name, 'FAC': self.facVar }


class Hue(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_hue')
        self.addDep(name='rgb_to_hsv', code=rgb_to_hsv)
        self.addDep(name='hsv_to_rgb', code=hsv_to_rgb)
    def code(self):
        return """
    void %(NAME)s(vec4 col1, inout vec4 col2)
    {
        float facm = 1.0 - %(FAC)s ;
        
        vec4 buf = col2;
    
        vec4 hsv, hsv2, tmp;
        rgb_to_hsv(col1, hsv2);
        
        if(hsv2.y != 0.0) {
            rgb_to_hsv(col2, hsv);
            hsv.x = hsv2.x;
            hsv_to_rgb(hsv, tmp);
            
            col2 = mix(buf, tmp, %(FAC)s );
            col2.a = buf.a;
        }
    }
""" % { 'NAME': self.name, 'FAC': self.facVar }


class Sat(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_sat')
        self.addDep(name='rgb_to_hsv', code=rgb_to_hsv)
        self.addDep(name='hsv_to_rgb', code=hsv_to_rgb)
    def code(self):
        return """
    void %(NAME)s( vec4 col1, inout vec4 col2)
    {
        float facm = 1.0 - %(FAC)s ;
    
        vec4 hsv = vec4(0.0);
        vec4 hsv2 = vec4(0.0);
        rgb_to_hsv(col2, hsv);
    
        if(hsv.y != 0.0) {
            rgb_to_hsv(col1, hsv2);
            hsv.y = facm*hsv.y + %(FAC)s *hsv2.y;
            hsv_to_rgb(hsv, col2);
        }
    }
""" % { 'NAME': self.name, 'FAC': self.facVar }


class Val(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_val')
        self.addDep(name='rgb_to_hsv', code=rgb_to_hsv)
        self.addDep(name='hsv_to_rgb', code=hsv_to_rgb)
    def code(self):
        return """
    void %(NAME)s(vec4 col1, inout vec4 col2)
    {
        float facm = 1.0 - %(FAC)s ;
    
        vec4 hsv, hsv2;
        rgb_to_hsv(col2, hsv);
        rgb_to_hsv(col1, hsv2);
    
        hsv.z = facm*hsv.z + %(FAC)s *hsv2.z;
        hsv_to_rgb(hsv, col2);
    }
""" % { 'NAME': self.name, 'FAC': self.facVar }


class Col(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_col')
        self.addDep(name='rgb_to_hsv', code=rgb_to_hsv)
        self.addDep(name='hsv_to_rgb', code=hsv_to_rgb)
    def code(self):
        return """
    void %(NAME)s(vec4 col1, inout vec4 col2)
    {
        float facm = 1.0 - %(FAC)s ;
    
        vec4 hsv, hsv2, tmp;
        rgb_to_hsv(col1, hsv2);
    
        if(hsv2.y != 0.0) {
            rgb_to_hsv(col2, hsv);
            hsv.x = hsv2.x;
            hsv.y = hsv2.y;
            hsv_to_rgb(hsv, tmp); 
    
            col2.rgb = mix(col2.rgb, tmp.rgb, %(FAC)s );
        }
    }
""" % { 'NAME': self.name, 'FAC': self.facVar }


class Soft(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_soft')
    def code(self):
        return """
    void %(NAME)s(vec4 col1, inout vec4 col2)
    {
        float facm = 1.0 - %(FAC)s ;
    
        vec4 one = vec4(1.0);
        vec4 scr = one - (one - col1)*(one - col2);
        col2 = facm*col2 + %(FAC)s *((one - col2)*col1*col2 + col2*scr);
    }
""" % { 'NAME': self.name, 'FAC': self.facVar }


class Linear(TextureBlenderCol2):
    def __init__(self):
        TextureBlenderCol2.__init__(self, name='blend_linear')
    def code(self):
        return """
    void %(NAME)s(vec4 col1, inout vec4 col2)
    {
        if(col1.r > 0.5)
            col2.r= col2.r + %(FAC)s *(2.0*(col1.r - 0.5));
        else
            col2.r= col2.r + %(FAC)s *(2.0*(col1.r) - 1.0);
    
        if(col1.g > 0.5)
            col2.g= col2.g + %(FAC)s *(2.0*(col1.g - 0.5));
        else
            col2.g= col2.g + %(FAC)s *(2.0*(col1.g) - 1.0);
    
        if(col1.b > 0.5)
            col2.b= col2.b + %(FAC)s *(2.0*(col1.b - 0.5));
        else
            col2.b= col2.b + %(FAC)s *(2.0*(col1.b) - 1.0);
    }
""" % { 'NAME': self.name, 'FAC': self.facVar }


BLEND_SHADER = {
    Texture2D.BLEND_MODE_MIX: Mix,
    Texture2D.BLEND_MODE_ADD: Add,
    Texture2D.BLEND_MODE_MULTIPLY: Mul,
    Texture2D.BLEND_MODE_SCREEN: Screen,
    Texture2D.BLEND_MODE_OVERLAY: Overlay,
    Texture2D.BLEND_MODE_SUBSTRACT: Sub,
    Texture2D.BLEND_MODE_DIVIDE: Div,
    Texture2D.BLEND_MODE_DIFFERENCE: Diff,
    Texture2D.BLEND_MODE_DARKEN: Dark,
    Texture2D.BLEND_MODE_LIGHTEN: Light,
    Texture2D.BLEND_MODE_DODGE: Dodge,
    Texture2D.BLEND_MODE_BURN: Burn,
    Texture2D.BLEND_MODE_HUE: Hue,
    Texture2D.BLEND_MODE_SATURATION: Sat,
    Texture2D.BLEND_MODE_VALUE: Val,
    Texture2D.BLEND_MODE_COLOR: Col,
    Texture2D.BLEND_MODE_SOFT: Soft,
    Texture2D.BLEND_MODE_LINEAR: Linear
}

