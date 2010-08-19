# -*- coding: UTF-8 -*-
'''
Created on 01.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from core.gl_object import GLObject

class GLMaterial(GLObject):
    def __init__(self, params):
        GLObject.__init__(self, params)
        self.matReflection = self.getAttr("matReflectionIntensity", 0.0)
        
        self.textures = []
        textures = params.get('textures', [])
        for tex in textures:
            self.addTexture(tex)
    
    def create(self, app, lights):
        for tex in self.textures:
            tex.create()
        GLObject.create(self, app, lights)
    
    def addTexture(self, tex):
        """
        material textures will be blended over face color/texture
        """
        self.textures.append(tex)
