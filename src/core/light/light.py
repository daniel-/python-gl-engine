# -*- coding: UTF-8 -*-
'''
Created on 09.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL.GL import GL_TEXTURE_COMPARE_MODE,\
                      GL_COMPARE_R_TO_TEXTURE,\
                      GL_NONE,\
                      GL_QUADS,\
                      GL_LIGHT0,\
                      GL_TEXTURE_2D_ARRAY
from OpenGL.GL import glBindTexture,\
                      glTexParameteri,\
                      glVertex3f,\
                      glViewport,\
                      glEnd,\
                      glBegin,\
                      glUniform1f

from core.gl_object import GLObject
from core.shadows.shadow_map import DirectionalShadowCamera,\
                                    SpotShadowCamera,\
                                    DirectionalShadowMap,\
                                    SpotShadowMap, ShadowMapArray

from utils.algebra.frustum import splitFrustum

class Light(GLObject):
    DIRECTIONAL_LIGHT = 0
    POINT_LIGHT = 1
    SPOT_LIGHT = 2
    
    # signal stuff
    LIGHT_POSITION_SIGNAL = GLObject.signalCreate()
    LIGHT_DIRECTION_SIGNAL = GLObject.signalCreate()
    
    def __init__(self, params):
        # FIXME: lights may be on the same unit for long time,
        #            we do not have to set the states each frame then!
        self.name = params.get('name')
        GLObject.__init__(self, params)
        self.lightCutOff = self.getAttr("lightCutOff", 180.0)
        
        # signal stuff
        self.signalRegister( Light.LIGHT_POSITION_SIGNAL )
        self.signalRegister( Light.LIGHT_DIRECTION_SIGNAL )
        
        # shadow maps for this light
        self.shadowMapArray = None
        
        # TODO: make xml configurable
        self.dimming = 0.3
    
    def __str__(self):
        return self.name
    
    def setIndex(self, index):
        self.index = index
        self.glIndex = GL_LIGHT0+index
    
    def create(self, app, lights):
        """
        create the shadow maps.
        """
        
        if self.getAttr("useShadowMap", False):
            type = self.getLightType()
            #kernel = ShadowMap.noKernel()
            #kernel = ShadowMap.kernel44()
            if type==Light.POINT_LIGHT:
                # TODO: SM: point light shadows
                raise NotImplementedError
            
            elif type==Light.DIRECTIONAL_LIGHT:
                # directional light needs scene frustum
                app.needFrustumPoints = True
                
                mapSize = 2048.0
                numSplits = 4
                
                self.shadowMapArray = ShadowMapArray(app, app.sceneCamera, mapSize)
                frustas = splitFrustum(app.sceneFrustum, numSplits, 0.75)
                
                for frustum in frustas:
                    camera = DirectionalShadowCamera( app, self, frustum, mapSize )
                    self.shadowMapArray.addShadowMap( DirectionalShadowMap( camera ))
                
            else: # spot light
                mapSize = 2048
                
                self.shadowMapArray = ShadowMapArray(app, app.sceneCamera, mapSize)
                
                camera = SpotShadowCamera(app, self)
                self.shadowMapArray.addShadowMap( SpotShadowMap( camera  ) )
        
        if self.shadowMapArray!=None:
            self.shadowMapArray.create(app)
        
        GLObject.create(self, app, lights)
    
    def getLightType(self):
        if self.lightPosition[3]==0.0:
            return Light.DIRECTIONAL_LIGHT
        elif self.lightCutOff==180.0:
            return Light.POINT_LIGHT
        else:
            return Light.SPOT_LIGHT



def drawShadowMaps(lights, layerLoc):
    """
    draws shadow maps for debugging.
    note that a special shader is required to display the depth-component-only textures
    """
    
    i = 0
    for light in lights:
        if light.shadowMapArray==None: continue
        shadowMapArray = light.shadowMapArray
        shadowMaps = shadowMapArray.shadowMaps
        
        glBindTexture( GL_TEXTURE_2D_ARRAY, shadowMapArray.texture.glID )
        glTexParameteri( GL_TEXTURE_2D_ARRAY, GL_TEXTURE_COMPARE_MODE, GL_NONE )
        
        for j in range(len(shadowMaps)):
            glViewport(130*i, 0, 128, 128)
            
            glUniform1f(layerLoc, float(j))
            
            glBegin(GL_QUADS)
            glVertex3f(-1.0, -1.0, 0.0)
            glVertex3f( 1.0, -1.0, 0.0)
            glVertex3f( 1.0,  1.0, 0.0)
            glVertex3f(-1.0,  1.0, 0.0)
            glEnd()
            
            i += 1
        
        if shadowMapArray.textureType=="sampler2DArrayShadow":
            glTexParameteri( GL_TEXTURE_2D_ARRAY, GL_TEXTURE_COMPARE_MODE, GL_COMPARE_R_TO_TEXTURE )
        else:
            glTexParameteri( GL_TEXTURE_2D_ARRAY, GL_TEXTURE_COMPARE_MODE, GL_NONE )
