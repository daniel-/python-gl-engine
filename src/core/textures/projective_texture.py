# -*- coding: UTF-8 -*-
'''
Created on 30.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl

from numpy import matrix as NumpyMatrix

class ProjectiveTextureMatrix(object):
    # the matrix for texture access,
    # maps values from [-1,1] to [0,1]
    biasMatrix = NumpyMatrix([ [0.5, 0.0, 0.0, 0.0],
                               [0.0, 0.5, 0.0, 0.0],
                               [0.0, 0.0, 0.5, 0.0],
                               [0.5, 0.5, 0.5, 1.0] ], "float32")
    biasMatrixD = NumpyMatrix([ [0.5, 0.0, 0.0, 0.0],
                                [0.0, 0.5, 0.0, 0.0],
                                [0.0, 0.0, 0.5, 0.0],
                                [0.5, 0.5, 0.5, 1.0] ], "float64")
    
    def __init__(self, app):
        self.app = app
        self.loadMatrix = self.loadMatrixSlow
    
    def getBiasProjection(self):
        raise NotImplementedError
    def getModelViewMatrix(self):
        return self.app.sceneCamera.modelViewMatrix
    def getProjectionMatrix(self):
        return self.app.projectionMatrix
    def getBiasMatrix(self):
        return self.biasMatrix
    
    def loadMatrixSlow(self):
        gl.glLoadMatrixf(self.getBiasMatrix())
        gl.glMultMatrixf(self.getProjectionMatrix())
        gl.glMultMatrixf(self.getModelViewMatrix())
    def loadMatrixFast(self):
        gl.glLoadMatrixf(self.getBiasProjection())
        gl.glMultMatrixf(self.getModelViewMatrix())
    
    def load(self, texUnit):
        """
        sets up the texture matrix for using the reflection map
        in the scene rendering pass.
        """
        gl.glMatrixMode(gl.GL_TEXTURE)
        gl.glActiveTexture(gl.GL_TEXTURE0 + texUnit)
        self.loadMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)

