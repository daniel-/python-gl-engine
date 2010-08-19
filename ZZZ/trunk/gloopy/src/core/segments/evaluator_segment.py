# -*- coding: UTF-8 -*-
'''
Created on 18.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from core.segments.segment import ModelSegment
from utils.util import doNothing, joinFunctions

class EvaluatorSegment(ModelSegment):
    """
    manages multiple evaluators.
    evaluators can have different targets (normal,uv,...)
    """
    
    def __init__(self, name, params):
        self.evaluators = params['evaluators']
        # launch all evaluators
        self._drawEvaluators = doNothing
        
        ModelSegment.__init__(self, name, params)
        
        self.vertexPositionName = "gl_Vertex"
        self.vertexNormalName = "gl_Normal"
        self.vertexColorName = "gl_Color"
        self.vertexUVName = "gl_MultiTexCord[0]"
    
    def create(self, app, lights):
        for e in self.evaluators: e.create(app, lights)
        ModelSegment.create(self, app, lights)
    
    def createDrawFunction(self):
        ModelSegment.createDrawFunction(self)
        # create evaluator state enabler and draw function
        for e in self.evaluators:
            e.createDrawFunction()
            
            # include evaluator states
            self.joinStaticStates(enable=e.enableStaticStates,
                                  disable=e.disableStaticStates)
            self.joinDynamicStates(enable=e.enableDynamicStates,
                                   disable=e.disableDynamicStates)
            
            # include evaluator draw function
            self._drawEvaluators = joinFunctions(self._drawEvaluators, e.draw)
    
    def addShaderAttributes(self, _):
        """
        overwrite method and do nothing. 
        """
        pass
    
    def drawSegment(self):
        # launch all evaluators
        self._drawEvaluators()
