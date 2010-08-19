# -*- coding: UTF-8 -*-
'''
Created on 19.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl
import OpenGL.GLU as glu

from core.gl_object import GLObject

class EvalParam(object):
    def __init__(self, name):
        self.name = name
        self.min = 0.0
        self.max = 1.0
        self.steps = 20

class Evaluator(GLObject):
    def __init__(self, params):
        GLObject.__init__(self, params)
        
        self.controlPoints = params.get('ctrls')
        self.params = params.get('params')
        self.target = params.get('target')
    
    def draw(self):
        pass

class GLEvaluator(Evaluator):
    def __init__(self, params):
        Evaluator.__init__(self, params)
        # only a single target
        self.target = params.get('target')
    

class CurveEvaluator(GLEvaluator):
    def __init__(self, params):
        GLEvaluator.__init__(self, params)
        self.u = self.params[0]
        try:
            self.evalPolygonMode
        except AttributeError:
            self.evalPolygonMode = gl.GL_LINE
    
    def enableStaticStates(self):
        GLEvaluator.enableStaticStates(self)
        
        gl.glMap1f(self.target,
                   self.u.min, self.u.max,
                   self.controlPoints)
        gl.glEnable(self.target)
        gl.glMapGrid1f(self.u.steps, self.u.min, self.u.max)
    
    def draw(self):
        gl.glEvalMesh1(self.evalPolygonMode, 0, self.u.steps)

class PatchEvaluator(GLEvaluator):
    def __init__(self, params):
        GLEvaluator.__init__(self, params)
        self.u = self.params[0]
        self.v = self.params[1]
        self.generateNormals = False
        
        try:
            self.evalPolygonMode
        except AttributeError:
            self.evalPolygonMode = gl.GL_LINE
    
    def enableStaticStates(self):
        GLEvaluator.enableStaticStates(self)
        
        gl.glMap2f(self.target,
                   self.u.min, self.u.max,
                   self.v.min, self.v.max,
                   self.controlPoints)
        gl.glEnable(self.target)
        
        gl.glMapGrid2f(self.u.steps, self.u.min, self.u.max,
                       self.v.steps, self.v.min, self.v.max)
        
        if self.generateNormals:
            gl.glEnable( gl.GL_AUTO_NORMAL )
    def disableStaticStates(self):
        GLEvaluator.disableStaticStates(self)
        
        if self.generateNormals:
            gl.glDisable( gl.GL_AUTO_NORMAL )
    
    def draw(self):
        gl.glEvalMesh2(self.evalPolygonMode, 0, self.u.steps,
                                             0, self.v.steps)


class NURBEvaluator(Evaluator):
    def __init__(self, params):
        Evaluator.__init__(self, params)
        self.knots = params.get('knots')
        # TODO: support multiple nurb targets
        self.target = params.get('target')
    
    def create(self, app, lights):
        Evaluator.create(self, app, lights)
        self.glID = glu.gluNewNurbsRenderer()
    
    def enableStaticStates(self):
        Evaluator.enableStaticStates(self)
    
    def __del__(self):
        glu.gluDeleteNurbsRenderer(self.glID)

class NURBCurveEvaluator(NURBEvaluator):
    def __init__(self, params):
        NURBEvaluator.__init__(self, params)
        self.uKnot = self.knots[0]
    
    def draw(self):
        glu.gluBeginCurve(self.glID)
        glu.gluNurbsCurve(self.glID,
                          self.uKnot,
                          self.controlPoints,
                          self.target)
        glu.gluEndCurve(self.glID)

class NURBPatchEvaluator(NURBEvaluator):
    def __init__(self, params):
        NURBEvaluator.__init__(self, params)
        self.uKnot = self.knots[0]
        self.vKnot = self.knots[1]
        self.generateNormals = False
    
    def enableStaticStates(self):
        NURBEvaluator.enableStaticStates(self)
        
        if self.generateNormals:
            gl.glEnable( gl.GL_AUTO_NORMAL )
    
    def disableStaticStates(self):
        if self.generateNormals:
            gl.glDisable( gl.GL_AUTO_NORMAL )
        NURBEvaluator.disableStaticStates(self)
    
    def draw(self):
        glu.gluBeginSurface(self.glID)
        glu.gluNurbsSurface(self.glID,
                            self.uKnot,
                            self.vKnot,
                            self.controlPoints,
                            self.target)
        glu.gluEndSurface(self.glID)

