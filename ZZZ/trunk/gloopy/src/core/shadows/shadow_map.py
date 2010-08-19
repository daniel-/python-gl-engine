# -*- coding: UTF-8 -*-
'''
Created on 30.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
from gui.gl_app import GLApp
OpenGL = importGL()
import OpenGL.GL as gl
from OpenGL.GL import glLoadMatrixf, glMultMatrixf, glMatrixMode,glGetFloatv,\
                      glLoadIdentity, GL_PROJECTION, GL_MODELVIEW, glViewport,\
                      GL_LINEAR, glUseProgram, GL_DEPTH_BUFFER_BIT, glDrawBuffer, glClear, GL_NONE
from OpenGL.GL import GL_CLAMP_TO_EDGE, GL_LEQUAL, GL_COMPARE_R_TO_TEXTURE, GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MATRIX, GL_DEPTH_COMPONENT24, GL_FLOAT
from OpenGL.GL.framebufferobjects import \
        glGenFramebuffers, glBindFramebuffer, glFramebufferTextureLayer, GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT
from OpenGL.GLU import gluLookAt

from shader.shader_utils import compileProgram

from core.camera import DirectionalCamera, Camera
from core.textures.texture import DepthTexture3D
from core.textures.projective_texture import ProjectiveTextureMatrix
from core.constants import UP_VECTOR

from utils.algebra.matrix44 import getProjectionMatrix,\
                                   getDirectionalShadowMapMatrices

from numpy import float32, array, identity, transpose
from numpy.linalg import inv

class ShadowCamera(DirectionalCamera):
    """
    base class for shadow map cameras
    """
    def __init__(self, light):
        self.light = light
        DirectionalCamera.__init__(self)
        # camera has own projection
        self.projectionMatrix = None
    
    def enable(self):
        """ setup projection and model view matrix. """
        glMatrixMode (GL_PROJECTION)
        glLoadMatrixf (self.projectionMatrix)
        glMatrixMode (GL_MODELVIEW)
        glLoadMatrixf (self.modelViewMatrix)

class ShadowProjectiveTextureMatrix(ProjectiveTextureMatrix):
    """
    handles setting the texture matrix for the shadow texture.
    """
    def __init__(self, app, camera):
        # light point of view camera
        self.camera = camera
        self.sceneCamera =  app.sceneCamera
        ProjectiveTextureMatrix.__init__(self, app)
    
    def loadMatrixSlow(self):
        """ set the texture matrix to: bias * crop * projection * modelView * inverseSceneModelView. """
        glLoadMatrixf( ShadowProjectiveTextureMatrix.biasMatrix )
        glMultMatrixf( self.camera.modelViewProjectionCropMatrix )
        glMultMatrixf( self.sceneCamera.inverseModelViewMatrix )
        
        # compute a normal matrix for the same thing (to transform the normals)
        # Basically, N = ((L)^-1)^-t
        self.normalMatrix = transpose( inv(
                glGetFloatv( GL_TEXTURE_MATRIX ) ) )
    
class ShadowMapArray(object):
    """
    array of shadow map textures.
    uses GL_TEXTURE_2D_ARRAY.
    """
    
    defualtKernel = [
        (0.000000, 0.000000, 0.0, 0.0),
        (0.079821, 0.165750, 0.0, 0.0),
        (-0.331500, 0.159642, 0.0, 0.0),
        (-0.239463, -0.497250, 0.0, 0.0),
        (0.662999, -0.319284, 0.0, 0.0),
        (0.399104, 0.828749, 0.0, 0.0),
        (-0.994499, 0.478925, 0.0, 0.0),
        (-0.558746, -1.160249, 0.0, 0.0)
    ]
    
    def __init__(self,
                 app,
                 sceneCamera,
                 mapSize=2048,
                 kernelOffset=2.0/4096.0,
                 kernel=None):
        self.sizeI = int(mapSize)
        self.sizeF = float(mapSize)
        self.shadowMaps = []
        self.numShadowMaps = 0
        
        if kernel==None:
            self.kernel = ShadowMapArray.defualtKernel
        else:
            self.kernel = kernel
        self.kernelOffset = kernelOffset
        
        # recalculate some stuff if the modelview matrix changes
        sceneCamera.signalConnect( Camera.CAMERA_MODELVIEW_SIGNAL, self.update )
        app.signalConnect( GLApp.APP_SIZE_SIGNAL, self.update )
        
        self.textureType = "sampler2DArray"
        #self.textureType = "sampler2DArrayShadow"
    
    def addShadowMap(self, shadowMap):
        """ add shadow map to the array. """
        self.shadowMaps.append(shadowMap)
        self.numShadowMaps += 1
    
    def create(self, app):
        """ creates resources. """
        self.app = app
        
        shadowMaps = self.shadowMaps
        
        # reserve a texture unit for shadow texture 
        self.textureUnit = app.reserveTextureUnit()
        
        # create a 3D texture using GL_TEXTURE_2D_ARRAY
        self.texture = DepthTexture3D(self.sizeI, self.sizeI)
        self.texture.targetType = GL_TEXTURE_2D_ARRAY
        self.texture.internalFormat = GL_DEPTH_COMPONENT24
        self.texture.numTextures = self.numShadowMaps
        self.texture.pixelType = GL_FLOAT
        self.texture.minFilterMode = GL_LINEAR
        self.texture.magFilterMode = GL_LINEAR
        self.texture.wrapMode = GL_CLAMP_TO_EDGE
        self.texture.compareFunc = GL_LEQUAL
        if self.textureType=="sampler2DArrayShadow":
            self.texture.compareMode = GL_COMPARE_R_TO_TEXTURE
        else:
            self.texture.compareMode = GL_NONE
        self.texture.create()
        
        # create a depth only fbo for the 3D texture
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glDrawBuffer(GL_NONE)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
        # the frustum slice far value must be accessable in the shader.
        # uniforms does not support array, so we split
        # the frustum slices in vec4 instances....
        numVecs = self.numShadowMaps/4; mod = self.numShadowMaps%4
        self.farVecs = [4]*numVecs
        if mod != 0:
            self.farVecs.append( mod )
            numVecs += 1
        
        # create shadow maps
        for i in range(self.numShadowMaps):
            shadowMap = shadowMaps[i]
            shadowMap.textureMatrixUnit = app.reserveTextureMatrixUnit()
            shadowMap.textureLayer = i
            shadowMap.create(app)
    
    def update(self):
        pos  = self.app.sceneCamera.position
        view = self.app.sceneCamera.direction
        
        camProj = self.app.projectionMatrix
        sceneCamera10 = camProj[2, 2]
        sceneCamera14 = camProj[3, 2]
        
        def _updateShadowMap(shadowMap, farBound):
            frustum = shadowMap.camera.frustum
            farBound.append( 0.5 * (-frustum.far * sceneCamera10 + sceneCamera14 ) / frustum.far + 0.5 )
            # update frustum points in world space
            shadowMap.camera.frustum.calculatePoints(pos, view, UP_VECTOR)
        farBound = []
        map( lambda m: _updateShadowMap(m, farBound), self.shadowMaps )
        
        self.farBounds = []
        numVecs = len(self.farVecs)
        startIndex = 0
        for j in range(numVecs):
            endIndex = startIndex + self.farVecs[j]
            self.farBounds.append( array( farBound[startIndex:endIndex], float32 ) )
            startIndex = endIndex
    
    def drawShadowMaps(self):
        """ render shadow depth to texture. """
        
        # redirect rendering to the depth texture
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        # and render only to the shadowmap
        glViewport(0, 0, self.sizeI, self.sizeI)
        
        def _drawShadowMap(map):
            # make the current depth map a rendering target
            glFramebufferTextureLayer(GL_FRAMEBUFFER,
                                      GL_DEPTH_ATTACHMENT,
                                      self.texture.glID,
                                      0,
                                      map.textureLayer)
            # clear the depth texture from last time
            glClear(GL_DEPTH_BUFFER_BIT)
            
            map.drawShadowMap()
        map( _drawShadowMap, self.shadowMaps )


class ShadowMap(object):
    """
    a texture with depth values.
    """
    
    def __init__(self, camera):
        self.camera = camera
        self.textureLayer = 0
        self.textureMatrixUnit = -1
    
    def update(self):
        raise NotImplementedError
    
    def create(self, app):
        """ creates a projective texture. """
        self.app = app
        self.projectiveMatrix = ShadowProjectiveTextureMatrix(app, self.camera)
        
        # update texture matrix if shadow camera changes
        def _updateTextureMatrix():
            self.projectiveMatrix.load(self.textureMatrixUnit)
        self.camera.signalConnect( Camera.CAMERA_MODELVIEW_SIGNAL,
                                   _updateTextureMatrix )
    
    def drawShadowMap(self):
        """ draws scene to the texture, geometry only. """
        self.camera.enable()
        # TODO: SM: minZ drawing ?
        #float d = light_dir[0]*(v->x-half_width) + light_dir[1]*v->y + light_dir[2]*(v->z-half_height);
        #if(minCamZ < d): //MODEL_HEIGHT
        #    drawModel()
        self.app.drawSceneGeometry()

#### VISUALIZING DEPTH ####

class VisualizeDepthShaderFrag(object):
    @staticmethod
    def code():
        return """
#version 120
#extension GL_EXT_texture_array : enable

uniform sampler2DArray tex;
uniform float layer;

void main()
{
    vec4 tex_coord = vec4(gl_TexCoord[0].x, gl_TexCoord[0].y, layer, 1.0);
    gl_FragColor = texture2DArray(tex, tex_coord.xyz);
}
"""
class VisualizeDepthShaderVert(object):
    @staticmethod
    def code():
        return """
void main()
{
    gl_TexCoord[0] = vec4(0.5)*gl_Vertex + vec4(0.5);
    gl_Position = gl_Vertex;
}
"""
class VisualizeDepthShader(object):
    def __init__(self):
        self.program = compileProgram(VisualizeDepthShaderVert, None, VisualizeDepthShaderFrag)
    def enable(self):
        glUseProgram(self.program)
    def disable(self):
        glUseProgram(0)

#### SPOT LIGHTS: Simple Shadow Mapping ####

class SpotShadowMap(ShadowMap):
    def create(self, app):
        ShadowMap.create(self, app)
        # initially setup matrices
        self.camera.updateViewMatrix()
        self.camera.updateProjectionMatrix()

class SpotShadowCamera(ShadowCamera):
    def __init__(self, app, light):
        self.app = app
        ShadowCamera.__init__(self, light)
        
        # recalculate model view matrix if light position/direction changes,
        # imported here to avoid error for modules importing each other
        from core.light.light import Light
        self.light.signalConnect( Light.LIGHT_POSITION_SIGNAL,
                                  self.updateMatrix )
        self.light.signalConnect( Light.LIGHT_DIRECTION_SIGNAL,
                                  self.updateMatrix )
        app.signalConnect( GLApp.APP_PROJECTION_CHANGED, self.updateProjectionMatrix )
        # TODO: SM: light cutoff changed signal ?
        
        self.updateProjectionMatrix()
    
    def updateMatrix(self):
        """
        needs updating if light changes position or direction.
        """
        # for some reason this is faster then calling the cython code
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.light.lightPosition[0],
                  self.light.lightPosition[1],
                  self.light.lightPosition[2],
                  self.light.lightDirection[0],
                  self.light.lightDirection[1],
                  self.light.lightDirection[2],
                  0.0, 1.0, 0.0 )
        self.modelViewMatrix = glGetFloatv( gl.GL_MODELVIEW_MATRIX )
    
    def updateProjectionMatrix(self):
        """
        needs updating if near/far clip changes and when
        the light cutoff value changes.
        """
        # TODO: SM: what is faster gl* or this ?
        self.projectionMatrix =  getProjectionMatrix(
                                   2.0 * self.light.lightCutOff.value,
                                   1.0, # shadow map ratio is 1.0
                                   self.app.nearClip,
                                   self.app.farClip, float32 )

#### DIRECTIONAL LIGHTS ####

DirectionalShadowMap = ShadowMap

class DirectionalShadowCamera(ShadowCamera):
    """
    camera for directional light.
    """
    
    def __init__(self,
                 app,
                 light,
                 frustum,
                 mapSize=512.0,
                 minScale=None,
                 maxScale=None):
        self.app = app
        self.frustum = frustum
        ShadowCamera.__init__(self, light)
        
        self._projectionUpdatedThisFrame = False
        
        self.mapSize = float(mapSize)
        
        # TODO: SM: initially setup matrices,
        #   if light does not animate the scene might be messed up until cam moves.
        self.projectionCropMatrix = identity(4, float32)
        self.modelViewMatrix = identity(4, float32)
        
        # recalculate model view matrix if light position changes,
        # imported here to avoid error for modules importing each other
        from core.light.light import Light
        light.signalConnect( Light.LIGHT_POSITION_SIGNAL,
                             self.updateMatrix )
        # projection depends on scene modelview and projection
        app.signalConnect( GLApp.APP_PROJECTION_CHANGED,
                           self.updateProjectionMatrix )
        app.sceneCamera.signalConnect( Camera.CAMERA_MODELVIEW_SIGNAL,
                                       self.updateProjectionMatrix )
    
    def enable(self):
        # setup projection and model view matrix
        glMatrixMode (GL_PROJECTION)
        glLoadMatrixf (self.projectionCropMatrix)
        glMatrixMode (GL_MODELVIEW)
        glLoadMatrixf (self.modelViewMatrix)
        
        self._projectionUpdatedThisFrame = False
    
    def updateMatrix(self):
        """
        update the light rotation matrix.
        needs only updating if the light position changes.
        """
        
        # for some reason this is faster then calling the cython code
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 0.0,
                  -  self.light.lightPosition[0],
                  -  self.light.lightPosition[1],
                  -  self.light.lightPosition[2],
                  -1.0, 0.0, 0.0 )
        self.modelViewMatrix = glGetFloatv( gl.GL_MODELVIEW_MATRIX )
        
        # projection depends on modelview matrix
        self.updateProjectionMatrix()
    
    def updateProjectionMatrix(self):
        """
        updates the orthogonal projection of this light.
        needs updating if the frustum slice changes.
        """
        
        # make sure we do not update multiple times per frame
        if self._projectionUpdatedThisFrame: return
        self._projectionUpdatedThisFrame = True
        
        self.projectionCropMatrix,\
        self.modelViewProjectionCropMatrix =\
                getDirectionalShadowMapMatrices(\
                        self.modelViewMatrix,
                        self.frustum.points,
                        self.app.sceneBounds[0],
                        self.app.sceneBounds[1])
        
        # let handlers now we have a new matrix,
        # texture matrix will be set with this emit
        self.signalQueueEmit( Camera.CAMERA_MODELVIEW_SIGNAL )

### POINT LIGHTS ###

PointShadowMap = ShadowMap

# TODO: SM: point light can use the frustum too !
class PointShadowCamera(ShadowCamera):
    def __init__(self):
        raise NotImplementedError

