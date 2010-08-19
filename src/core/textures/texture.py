# -*- coding: UTF-8 -*-
'''
Created on 08.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl

from pygame import image

# TODO: textures could define states for texture matrix manipulation.
#            * texgen
#            * matrix in xml angeben

class Texture(object):
    """
    helper for loading opengl textures.
    this class has vars for most texture states,
    you can modify the states after calling __init__()
    and before calling create().
    default states match standard image texture.
    """
    
    # blend mode describes how a texture
    # will be mixed with existing pixels
    BLEND_MODE_MIX = 0
    BLEND_MODE_MULTIPLY = 1
    BLEND_MODE_ADD = 2
    BLEND_MODE_SUBSTRACT = 3
    BLEND_MODE_DIVIDE = 4
    BLEND_MODE_DIFFERENCE = 5
    BLEND_MODE_LIGHTEN = 6
    BLEND_MODE_DARKEN = 7
    BLEND_MODE_SCREEN = 8
    BLEND_MODE_OVERLAY = 9
    BLEND_MODE_HUE = 10
    BLEND_MODE_SATURATION = 11
    BLEND_MODE_VALUE = 12
    BLEND_MODE_COLOR = 13
    BLEND_MODE_DODGE = 14
    BLEND_MODE_BURN = 15
    BLEND_MODE_SOFT = 16
    BLEND_MODE_LINEAR = 17
    
    # The scene's Global 3D coordinates. This is also usefull for animations;
    # if you move the object, the texture moves across it.
    # It can be useful for letting objects appear or disappear at a certain position in space. 
    MAP_INPUT_GLOB = 0
    # Uses a child Object's texture space as source of coordinates.
    # The Object name must be specified in the text button on the right.
    # Often used with Empty objects, this is an easy way to place a small image as a logo or decal
    # at a given point on the object (see the example below). This object can also be animated,
    # to move a texture around or through a surface
    MAP_INPUT_OBJECT = 1
    # Each vertex of a mesh has its own UV co-ordinates which can be unwrapped and laid flat like a skin 
    MAP_INPUT_UV = 2
    # "Original Co-ordinates" - The object's local texture space.
    # This is the default option for mapping textures. 
    MAP_INPUT_ORCO = 3
    # Uses a mesh's sticky coordinates, which are a form of per-vertex UV co-ordinates.
    # If you have made Sticky co-ordinates first (F9  Mesh Panel, Sticky Button),
    # the texture can be rendered in camera view (so called "Camera Mapping"). 
    MAP_INPUT_STICK = 4
    # The rendered image window coordinates. This is well suited to blending two objects. 
    MAP_INPUT_WIN = 5
    # Uses the direction of the surface's normal vector as coordinates.
    # This is very useful when creating certain special effects that depend on viewing angle 
    MAP_INPUT_NOR = 6
    # Uses the direction of the reflection vector as coordinates.
    # This is useful for adding reflection maps - you will need this input when Environment Mapping.
    MAP_INPUT_REFL = 7
    
    # how a texture should be mapped on geometry
    MAPPING_FLAT = 0
    MAPPING_CUBE = 1
    MAPPING_TUBE = 2
    MAPPING_SPHERE = 3
    
    # should texture affect color/normals/....
    MAP_TO_COL = 1
    MAP_TO_NOR = 2
    MAP_TO_ALPHA = 3
    MAP_TO_CSP = 4
    MAP_TO_CMIR = 5
    MAP_TO_REF = 6
    MAP_TO_SPEC = 7
    MAP_TO_HARD = 8
    MAP_TO_EMIT = 9
    MAP_TO_RAYMIR = 10
    MAP_TO_DISP = 11
    MAP_TO_TRANSLU = 12
    MAP_TO_AMB = 13
    MAP_TO_WARP = 14
    MAP_TO_HEIGHT = 15
    
    def __init__(self, width=-1, height=-1):
        self.glID = -1
        self.width  = width
        self.height = height
        # texture destination
        self.targetType = gl.GL_TEXTURE_2D
        self.envMode = gl.GL_MODULATE
        self.wrapMode = gl.GL_CLAMP
        # scale function
        self.magFilterMode = gl.GL_LINEAR
        self.minFilterMode = gl.GL_LINEAR
        self.internalFormat = gl.GL_RGBA
        # format of pixel data
        self.format = gl.GL_RGBA
        # border widtg 0 | 1
        self.border = 0
        # type for pixels
        self.pixelType = gl.GL_UNSIGNED_INT
        # pixel data, or none for empty texture
        self.textureData = None
        self.useMipMap = False
        self.compareMode = gl.GL_NONE
        self.compareFunc = gl.GL_EQUAL
        self.depthMode = gl.GL_INTENSITY
        
        # blending stuff
        self.brightness = 1.0
        self.contrast = 0.0
        self.colfac = 1.0
        self.norfac = 0.5
        self.warpfac = 0.0
        self.dispfac = 0.0 
        self.col = (0.0, 0.0, 0.0)
        self.rgbCol = (0.0, 0.0, 0.0)
        self.noRGB = False
        self.stencil = False
        self.neg = False
        self.tangentSpace = False
        self.blendMode = self.BLEND_MODE_MIX
        self.mapInput = self.MAP_INPUT_UV
        self.mapping = self.MAPPING_FLAT
        self.mapTo = [self.MAP_TO_COL]
    
    def __del__(self):
        gl.glDeleteTextures([self.glID])
    
    def create(self):
        if self.glID!=-1:
            gl.glDeleteTextures([self.glID])
        
        self.glID = gl.glGenTextures(1)
        gl.glBindTexture(self.targetType, self.glID)
        
        gl.glTexEnvf(gl.GL_TEXTURE_ENV,
                     gl.GL_TEXTURE_ENV_MODE,
                     self.envMode)
        
        gl.glTexParameteri(self.targetType,
                           gl.GL_TEXTURE_MAG_FILTER,
                           self.magFilterMode)
        gl.glTexParameteri(self.targetType,
                           gl.GL_TEXTURE_MIN_FILTER,
                           self.minFilterMode)

        gl.glTexParameterf(self.targetType,
                           gl.GL_TEXTURE_WRAP_S,
                           self.wrapMode)
        gl.glTexParameterf(self.targetType,
                           gl.GL_TEXTURE_WRAP_T,
                           self.wrapMode)
        
        gl.glTexParameteri(self.targetType,
                           gl.GL_TEXTURE_COMPARE_MODE,
                           self.compareMode)
        gl.glTexParameteri(self.targetType,
                           gl.GL_TEXTURE_COMPARE_FUNC,
                           self.compareFunc)
        gl.glTexParameteri(self.targetType,
                           gl.GL_DEPTH_TEXTURE_MODE,
                           self.depthMode)
        
        if self.useMipMap:
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_GENERATE_MIPMAP,
                               True);
        
        self.texImage()
        # TODO: what difference ?
        #glGenerateMipmapEXT(GL_TEXTURE_2D)
        
        #gl.glBindTexture(self.targetType, 0)
    
    def texImage(self):
        raise NotImplementedError
    
    def setBlendMode(self, id):
        MODES = {
            'mix': self.BLEND_MODE_MIX,
            'mul': self.BLEND_MODE_MULTIPLY,
            'add': self.BLEND_MODE_ADD,
            'sub': self.BLEND_MODE_SUBSTRACT,
            'div': self.BLEND_MODE_DIVIDE,
            'diff': self.BLEND_MODE_DIFFERENCE,
            'light': self.BLEND_MODE_LIGHTEN,
            'dark': self.BLEND_MODE_DARKEN,
            'screen': self.BLEND_MODE_SCREEN,
            'overlay': self.BLEND_MODE_OVERLAY,
            'hue': self.BLEND_MODE_HUE,
            'sat': self.BLEND_MODE_SATURATION,
            'val': self.BLEND_MODE_VALUE,
            'col': self.BLEND_MODE_COLOR
        }
        try:
            self.blendMode = MODES[id]
        except:
            print "WARNING: unknown blend mode '%s'" % str(id)
    
    def setMapInput(self, id):
        if id == "uv":
            self.mapInput = self.MAP_INPUT_UV
        elif id == "orco":
            self.mapInput = self.MAP_INPUT_ORCO
        elif id in ["glob", "object", "stick", "win", "nor", "refl"]:
            print "WARNING: map input mode '%s' not supported yet" % str(id)
        else:
            print "WARNING: unknown map input mode '%s'" % str(id)
    
    def setMapping(self, id):
        if id == "flat":
            self.mappingMode = self.MAPPING_FLAT
        elif id in ["cube", "tube", "sphere"]:
            print "WARNING: mapping mode '%s' not supported yet" % str(id)
        else:
            print "WARNING: unknown mapping mode '%s'" % str(id)
    
    def setMapTo(self, ids):
        modes = []
        for id in ids:
            if id[0]=="-":
                id = id[1:]
                factor = -1
            else:
                factor = 1
            
            if id == "col":
                modes.append(factor * self.MAP_TO_COL)
            elif id == "nor":
                modes.append(factor * self.MAP_TO_NOR)
            elif id == "height":
                modes.append(factor * self.MAP_TO_HEIGHT)
            elif id in ["alpha", "csp", "cmir", "ref",
                        "spec", "hard", "emit", "raymir",
                        "disp", "translu", "amb", "warp"]:
                print "WARNING: map to mode '%s' not supported yet" % str(id)
            else:
                print "WARNING: unknown map to mode '%s'" % str(id)
        self.mapTo = modes

class DepthTexture(Texture):
    def __init__(self, width, height):
        Texture.__init__(self, width, height)
        self.magFilterMode = gl.GL_LINEAR
        self.minFilterMode = gl.GL_LINEAR
        self.format = gl.GL_DEPTH_COMPONENT
        self.internalFormat = gl.GL_DEPTH_COMPONENT
        self.pixelType = gl.GL_UNSIGNED_BYTE

class Texture2D(Texture):
    def texImage(self):
        gl.glTexImage2D(self.targetType,
                        0, # mipmap level
                        self.internalFormat,
                        self.width,
                        self.height,
                        self.border,
                        self.format,
                        self.pixelType,
                        self.textureData)
class DepthTexture2D(DepthTexture):
    def texImage(self):
        gl.glTexImage2D(self.targetType,
                        0, # mipmap level
                        self.internalFormat,
                        self.width,
                        self.height,
                        self.border,
                        self.format,
                        self.pixelType,
                        self.textureData)

class ImageTexture(Texture2D):
    """
    image file texture all formats of pygame.image are supprted.
    """
    
    def __init__(self, file=None):
        Texture2D.__init__(self)
        self.pixelType = gl.GL_UNSIGNED_BYTE
        self.file = file
        if file!=None:
            self.setFile(file)
    
    def setFile(self, file):
        """
        loads pixel data from file.
        """
        self.file = file
        surface = image.load("../textures/" + file)
        self.textureData = image.tostring(surface, "RGBA", 1)
        self.width, self.height = surface.get_size()
        del surface

class Texture3D(Texture):
    def __init__(self, width, height):
        Texture.__init__(self, width, height)
        self.numTextures = -1
    def texImage(self):
        gl.glTexImage3D(self.targetType,
                        0, # mipmap level
                        self.internalFormat,
                        self.width,
                        self.height,
                        self.numTextures,
                        self.border,
                        self.format,
                        self.pixelType,
                        self.textureData)
class DepthTexture3D(DepthTexture):
    def __init__(self, width, height):
        DepthTexture.__init__(self, width, height)
        self.numTextures = -1
    def texImage(self):
        gl.glTexImage3D(self.targetType,
                        0, # mipmap level
                        self.internalFormat,
                        self.width,
                        self.height,
                        self.numTextures,
                        self.border,
                        self.format,
                        self.pixelType,
                        self.textureData)
