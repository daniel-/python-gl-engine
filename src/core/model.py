# -*- coding: UTF-8 -*-
'''
Created on 08.05.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl

from core.gl_object import GLObject

class Model(GLObject):
    
    def __init__(self, segments, params):
        GLObject.__init__(self, params)
        
        # list of segments
        self.segments = segments
        self.lights = []
    
    def create(self, app):
        """
        creates gl resources of model.
        @param lights: list of gl_helper.light.Light instances
        """
        
        GLObject.create(self, app, self.lights)
        
        self.createDrawFunction()
        
        for l in self.lights:
            l.createGuard(app, self.lights)
        for s in self.segments:
            s.createGuard(app, self.lights)
        # TODO: VBO: create some bigger vbos for vbo segments
        
        self.postCreate()
    
    def createDrawFunction(self):
        for l in self.lights:
            l.createDrawFunction()
        GLObject.createDrawFunction(self)
    
    def enableStaticStates(self):
        GLObject.enableStaticStates(self)
        for l in self.lights:
            l.enableStaticStates()
    def disableStaticStates(self):
        GLObject.disableStaticStates(self)
        for l in self.lights:
            l.disableStaticStates()
    def enableDynamicStates(self):
        GLObject.enableDynamicStates(self)
        for l in self.lights:
            l.enableDynamicStates()
    def disableDynamicStates(self):
        GLObject.disableDynamicStates(self)
        for l in self.lights:
            l.disableDynamicStates()
    
    def setLights(self, lights):
        self.lights = lights
        for i in range(len(lights)):
            lights[i].setIndex(i)
    
    def draw(self, app, _):
        self.app = app
        
        if self.popTransformations:
            gl.glPushMatrix()
        self.enableStates()
        
        # draw segments of model
        for segment in self.segments:
            # not drawing hidden element,
            # for example used in reflection by the reflector.
            # TODO: can be done without this if ;)
            if segment.hidden: continue
            
            segment.shader.enable()
            
            if segment.popTransformations:
                gl.glPushMatrix()
                segment.enableStates()
                
                # light position must be transformed too
                for l in self.lights:
                    l.enableLightPosition()
                
                segment.drawSegment()
                
                segment.disableStates()
                gl.glPopMatrix()
                
                # light position must be transformed back
                # FIXME: maybe unneeded to unset?
                for l in self.lights:
                    l.disableLightPosition()
            else:
                segment.enableStates()
                segment.drawSegment()
                segment.disableStates()
            
            segment.shader.disable()
        
        self.disableStates()
        if self.popTransformations:
            gl.glPopMatrix()
