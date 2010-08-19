# -*- coding: UTF-8 -*-
'''
Created on 18.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL.GL import glGetUniformLocation, \
                      glUniform1i, \
                      glUniform1fv, glUniform2fv, glUniform3fv, glUniform4fv,\
                      glUniformMatrix4fv
from OpenGL.GL import glUseProgram, \
                      glActiveTexture, glBindTexture,\
                      GL_TEXTURE0

from shader.shader_utils import ShaderWrapper

from numpy import array, float32

class SegmentShader(ShaderWrapper):
    def __init__(self, segment, glHandle, textures):
        self.segment = segment
        self.app = segment.app
        self.textures = []
        self.texLocs = []
        
        ShaderWrapper.__init__(self, glHandle)
        
        # remember textur uniform locations
        for i in range(len(textures)):
            tex = textures[i]
            (_, _, _, name, _) = tex
            
            loc = glGetUniformLocation( self.glHandle, name )
            if loc==-1:
                print "WARNING: cannot find texture name '%s' in shader." % name
                continue
            
            self.textures.append( (tex,loc) )
        
        # init some shadow map stuff for saving time on enable()
        uniformfvFuncs = [glUniform1fv,
                          glUniform2fv,
                          glUniform3fv,
                          glUniform4fv]
        self.shadowMapArrays = []
        for i in range(len(self.segment.lights)):
            light = self.segment.lights[i]
            shadowMapArray = light.shadowMapArray
            if shadowMapArray==None: continue
            
            numVecs = len(shadowMapArray.farVecs)
            farLocs = []
            norMatData = []
            for j in range(numVecs):
                farLocs.append( ( glGetUniformLocation(self.glHandle, "shadowFar%d%d" % (i,j)),
                                  uniformfvFuncs[shadowMapArray.farVecs[j]-1] ) )
            norMatData = ( glGetUniformLocation(self.glHandle, "shadowNormalMat%d" % (i)),
                           map( lambda m: m.projectiveMatrix, shadowMapArray.shadowMaps ),
                           len(shadowMapArray.shadowMaps) )
            self.shadowMapArrays.append( (shadowMapArray, farLocs, norMatData) )
    
    def enable(self):
        # replace fixed function pipeline
        glUseProgram(self.glHandle)
        
        # activate and bind textures
        def _bindTexture((tex,loc)):
            (tex, target, _, _, i) = tex
            glActiveTexture(GL_TEXTURE0 + i)
            glUniform1i(loc, i)
            glBindTexture(target, tex)
        map( _bindTexture, self.textures )
        
        # enable shadow maps far uniforms
        def _enableFarLoc(((farLoc, uniformFunc), farBound)):
            uniformFunc ( farLoc, 1, farBound )
        def _enableShadowMaps((shadowMapArray, farLocs, norMatData)):
            map( _enableFarLoc, zip( farLocs, shadowMapArray.farBounds ) )
            
            norMatLoc, norMats, numArrays = norMatData
            norMats = map(lambda m: m.normalMatrix, norMats)
            glUniformMatrix4fv ( norMatLoc, numArrays, False, array( norMats, float32 ) )
            
        map( _enableShadowMaps, self.shadowMapArrays ) 
        
    def disable(self):
        # TODO: needed to switch unit ?
        glActiveTexture( GL_TEXTURE0 )

