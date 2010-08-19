# -*- coding: UTF-8 -*-
'''
Created on 04.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from pygame.locals import MOUSEMOTION, MOUSEBUTTONUP, MOUSEBUTTONDOWN

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL.GL import GL_FRONT,\
                      GL_DEPTH_TEST,\
                      GL_COLOR_BUFFER_BIT,\
                      GL_PROJECTION,\
                      GL_MODELVIEW,\
                      GL_TEXTURE,\
                      GL_QUADS,\
                      GL_POLYGON_OFFSET_FILL,\
                      GL_TEXTURE_2D
from OpenGL.GL import glEnable, glDisable
from OpenGL.GL import glPushAttrib, glPopAttrib
from OpenGL.GL import glPushMatrix,\
                      glPopMatrix,\
                      glMatrixMode,\
                      glLoadMatrixf,\
                      glLoadIdentity
from OpenGL.GL import glCullFace
from OpenGL.GL import glBegin, glEnd,\
                      glTexCoord2f,\
                      glVertex3f,\
                      glGetUniformLocation,\
                      glBindTexture,\
                      glUseProgram,\
                      glViewport,\
                      glClearColor,\
                      glPolygonOffset
from OpenGL.GL import glFogi, glFogf, glFogfv,\
                      GL_FOG, GL_FOG_DENSITY,\
                      GL_FOG_START, GL_FOG_END,\
                      GL_FOG_COLOR, GL_FOG_MODE, GL_EXP2
from OpenGL.GL.framebufferobjects import glBindFramebuffer, GL_FRAMEBUFFER

from numpy import pi, array, float32, sin, cos

from gl_app import GLApp

from shader.shader_utils import DepthShader

from core.camera import UserCamera, Camera
from core.fbo import FBO
from core.textures.projective_texture import ProjectiveTextureMatrix
from core.textures.texture import Texture2D, DepthTexture2D
from core.shadows.shadow_map import VisualizeDepthShader
from core.light.light import drawShadowMaps, Light
from core.gl_object import GLObject

from utils.util import unique

from utils.algebra.frustum import Frustum


def _updateLightShadowMap(light):
    """ update light shadow maps. """
    shadowMapArray = light.shadowMapArray
    if shadowMapArray!=None:
        shadowMapArray.drawShadowMaps()
def _drawSegmentGeometry(segment):
    if segment.hidden: return
    if segment.popTransformations:
        glPushMatrix()
        segment.enableStates()
        segment.drawSegment()
        segment.disableStates()
        glPopMatrix()
    else:
        segment.enableStates()
        segment.drawSegment()
        segment.disableStates()
def _drawModelGeometry(model):
    # TODO: only handle geometry related states here !
    if model.popTransformations:
        glPushMatrix()
        model.enableStates()
        map(_drawSegmentGeometry, model.segments)
        model.disableStates()
        glPopMatrix()
    else:
        model.enableStates()
        map(_drawSegmentGeometry, model.segments)
        model.disableStates()


class ModelApp(GLApp):
    """
    ModelApp splits rendering in multiple passes using fbos.
    """
    
    def __init__(self):
        self.models = []
        self.lights = []
        # render to texture scenes
        self.sceneFBOS = []
        # all units <self.textureCounter are reserved
        self.textureCounter = 0
        self.textureMatrixCounter = 0
        
        # matrix used for projective textures will be stored at this unit
        # only used when self.useProjectiveTextures=True
        self.useProjectiveTextures = False
        self.projectiveTextureIndex = -1
        self.projectiveTextureMatrixIndex = -1
        self.projectivTextureMatrix = ProjectiveTextureMatrix(self)
        # set to true if you need the frustum points/centroid calculated
        self.needFrustumPoints = False
        
        # and the associated frustum
        self.sceneFrustum = Frustum(0.0, 1.0)
        
        GLApp.__init__(self)
        
        # camera for user movement
        self.sceneCamera = UserCamera(self)
        
        # create screen textures
        self.sceneTexture = Texture2D(width=self.winSize[0], height=self.winSize[1])
        self.sceneTexture.create()
        self.sceneDepthTexture = DepthTexture2D(width=self.winSize[0], height=self.winSize[1])
        self.sceneDepthTexture.create()
        
        # a shader that only handles the depth
        self.depthShader = DepthShader()
        self.visualizeDepthShader = VisualizeDepthShader()
        
        ### TESTING ###
        self.lightAngle = 0.0
    
    def reserveTextureUnit(self):
        """ increase texture counter. """
        self.textureCounter += 1
        return self.textureCounter - 1
    def reserveTextureMatrixUnit(self):
        """ increase texture counter. """
        self.textureMatrixCounter += 1
        return self.textureMatrixCounter - 1
    
    def enableProjectiveTextures(self):
        """
        sets flag for enabling projective textures
        and reserves one texture unit for the projection matrix.
        """
        if self.projectiveTextureIndex!=-1:
            return
        self.projectiveTextureIndex = self.reserveTextureUnit()
        self.projectiveTextureMatrixIndex = self.reserveTextureMatrixUnit()
        self.useProjectiveTextures = True
        
        def _loadProjectiveTextureMatrix():
            self.projectivTextureMatrix.load(self.projectiveTextureMatrixIndex)
        self.signalConnect( GLApp.APP_PROJECTION_CHANGED, _loadProjectiveTextureMatrix )
        self.sceneCamera.signalConnect( Camera.CAMERA_MODELVIEW_SIGNAL, _loadProjectiveTextureMatrix )
    
    def addModel(self, model):
        """
        adds a model to this application.
        """
        self.models.append(model)
        self.lights += model.lights
        self.lights = unique( self.lights )
        
        for s in model.segments:
            if s.usesProjectiveTexture():
                self.enableProjectiveTextures()
                break
    
    def prependFBO(self, sceneFBO, drawScene, sceneCamera):
        """
        prepends a render to texture operation before scene rendering is done.
        """
        self.sceneFBOS = [(sceneFBO, drawScene, sceneCamera)] + self.sceneFBOS
    def appendFBO(self, sceneFBO, drawScene, sceneCamera):
        """
        appends a render to texture operation before scene rendering is done.
        """
        self.sceneFBOS.append((sceneFBO, drawScene, sceneCamera))
    
    def setDefaultSceneFBO(self):
        """ set the default fbo for offscreen scene rendering. """
        drawSceneFBO = FBO()
        drawSceneFBO.addColorTexture(self.sceneTexture)
        drawSceneFBO.setDepthTexture(self.sceneDepthTexture)
        drawSceneFBO.create()
        self.appendFBO(drawSceneFBO, self.drawSceneComplete, self.sceneCamera)
    
    def drawSceneComplete(self):
        """ draws scene with color.  """
        map(lambda m: m.draw(self, m), self.models)
    def drawSceneGeometry(self):
        """
        draws the scene geometry only.
        usefull for depth value rendering.
        """
        map(_drawModelGeometry, self.models)
    
    def setWindowSize(self, size):
        """
        also set frustum projection.
        """
        ret = GLApp.setWindowSize(self, size)
        # set the frustum projection
        self.sceneFrustum.setProjection(self.fov,
                                        self.aspect,
                                        self.nearClip,
                                        self.farClip)
        return ret
    
    def orthogonalPass(self, debugShadows=False):
        """
        draw stuff in orthogonal projection.
        mainly the scene can be post processed here
        and some gui elements could be drawn.
        """
        
        ### DRAW THE SCENE ###
        
        # TODO: post shader magic !
        glUseProgram(0)
        
        # enable the scene texture
        # Note that texture unit 0 should be active now.
        glEnable(GL_TEXTURE_2D)
        glBindTexture (GL_TEXTURE_2D, self.sceneTexture.glID)
        # make sure texture matrix is set to identity
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex3f(0.0, 0.0, -1.0)
        glTexCoord2f(1.0, 0.0); glVertex3f(self.winSize[0], 0.0, -1.0)
        glTexCoord2f(1.0, 1.0); glVertex3f(self.winSize[0], self.winSize[1], -1.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(0.0, self.winSize[1], -1.0)
        glEnd()
        
        ### DEBUG DRAWINGS ###
        
        # debug shadow maps
        if debugShadows:
            # draw the shadow maps
            self.visualizeDepthShader.enable()
            layerLoc = glGetUniformLocation( self.visualizeDepthShader.program, "layer" )
            drawShadowMaps(self.lights, layerLoc)
            
            # reset viewport and reset to ffp
            glViewport(0, 0, self.winSize[0], self.winSize[1])
            glUseProgram( 0 )
        
        glBindTexture (GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        
        GLApp.orthogonalPass(self)
    
    def processEvent(self, event):
        """ processes one event. """
        # pass some events to the scene camera
        if event.type == MOUSEMOTION:
            self.sceneCamera.motion( * event.pos )
        elif event.type == MOUSEBUTTONUP or event.type == MOUSEBUTTONDOWN:
            self.sceneCamera.mouseEvent( event.button, event.type, event.pos[0], event.pos[1] )
    
    def animationStep(self):
        ####### TESTING ##########
        self.lightAngle += 0.005
        if self.lightAngle>=2.0*pi:
            self.lightAngle -= 2.0*pi
        lightRadius = 4.0
        self.lights[0].lightPosition = array ([
                    lightRadius*sin(self.lightAngle),
                    lightRadius,
                    lightRadius*cos(self.lightAngle), 0.0 ], float32)
        self.lights[0].signalQueueEmit( Light.LIGHT_POSITION_SIGNAL )
        ####### TESTING ##########
    
    def processFrame(self, timePassedSecs):
        """ draws a scene """
        
        # update the model view matrix
        self.sceneCamera.updateKeys()
        self.sceneCamera.update()
        
        # process queued GLObject events
        GLObject.signalsEmit()
        
        # enable some default scene states
        glEnable(GL_DEPTH_TEST)
        
        ######## SHADOW MAP RENDERING START ########
        
        # offset the geometry slightly to prevent z-fighting
        # note that this introduces some light-leakage artifacts
        glEnable( GL_POLYGON_OFFSET_FILL )
        glPolygonOffset( 1.1, 4096.0 )
        
        # cull front faces for shadow rendering,
        # this moves z-fighting to backfaces.
        glCullFace(GL_FRONT)
        # enable depth rendering shader.
        # FIXME: support segment geometry shader!
        #          geometry shader could change the shadow shape!
        self.depthShader.enable()
        
        map( _updateLightShadowMap, self.lights )
        glBindFramebuffer( GL_FRAMEBUFFER, 0 )
        
        glDisable( GL_POLYGON_OFFSET_FILL )
        ######## SHADOW MAP RENDERING STOP ########
        
        #### TODO: FOG: integrate FOG ####
        glEnable(GL_FOG)
        glFogi (GL_FOG_MODE, GL_EXP2)
        # approximate the atmosphere's filtering effect as a linear function
        sunDir = array( [4.0, 4.0, 4.0, 0.0], float32 ) # TODO: FOG: what is the sun dir ?
        skyColor = array( [0.8,
                           sunDir[1]*0.1 + 0.7,
                           sunDir[1]*0.4 + 0.5,
                           1.0], float32 )
        glClearColor( * skyColor )
        glFogf(GL_FOG_DENSITY, 0.4)
        glFogf(GL_FOG_START, 16.0)
        glFogf(GL_FOG_END, self.farClip)
        glFogfv(GL_FOG_COLOR, skyColor)
        
        # fill projection matrix
        glMatrixMode( GL_PROJECTION )
        glLoadMatrixf( self.projectionMatrix )
        glMatrixMode( GL_MODELVIEW )
        
        # draw stuff in 3d projection
        lastCam = None
        glPushAttrib(GL_COLOR_BUFFER_BIT)
        for (fbo, draw, cam) in self.sceneFBOS:
            # render to fbo
            fbo.enable()
            if cam!=lastCam:
                cam.enable()
                lastCam = cam
            draw()
        # disable render to texture
        FBO.disable()
        glPopAttrib()
        glViewport(0, 0, self.winSize[0], self.winSize[1])
        
        #### TODO: FOG: integrate FOG ####
        glDisable(GL_FOG)
        
        # change to orthogonal projection
        glMatrixMode( GL_PROJECTION )
        glLoadMatrixf( self.orthoMatrix )
        glMatrixMode( GL_MODELVIEW )
        glLoadIdentity()
        
        # no depth test needed in orthogonal rendering
        glDisable(GL_DEPTH_TEST)
        
        # draw orthogonal to the screen
        self.orthogonalPass()
