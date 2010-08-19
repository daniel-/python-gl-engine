# -*- coding: UTF-8 -*-
'''
planar reflection can be used for mirror like effects on plane surfaces.
this can also usefull implementing the reflections of water.

Created on 24.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

import sys
sys.path.append("../utils/algebra/")

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl

from numpy import ndarray, array, identity, outer, vdot, float32
from utils.algebra.vector import crossVec3Float32Normalized
from utils.algebra.matrix44 import inverseCContiguous

from core.fbo import FBO
from core.textures.texture import DepthTexture2D, Texture2D

from shader.shader_utils import FragShaderFunc,\
                                VertShaderFunc,\
                                FRAG_SHADER,\
                                VERT_SHADER

class PlanarReflection(object):
    def __init__(self, app, segment):
        self.app = app
        self.segment = segment
        # reflection color texture
        self.reflectionColor = None
        # point on the reflecting surface
        self.position = None
        # normal of surface
        self.normal = None
        # matrix that mirrors the scene
        self.mirrorMat = None
    
    def create(self):
        # adds a render pass to create reflection color map
        self._setupReflectionPass()
        
        self.shadowMatrixUnits = []
        for l in self.app.lights:
            if l.shadowMapArray == None: continue
            for map in l.shadowMapArray.shadowMaps:
                self.shadowMatrixUnits.append( map.textureMatrixUnit )
    
    def setOrigin(self, position, normal):
        self.position = position
        self.normal = normal
        # scene reflection matrix must be updated
        self._calcSceneReflectionMatrix()
        
        # calculate the clipping plane.
        # clip plane works with equation:
        #    A*x + B*y + C*z + D > 0    (holds true for unclipped geometry)
        A, B, C = normal[0], normal[1], normal[2]
        D = vdot( (-position), ( normal ) )
        self.clipPlane = array([ A, B, C, D ], "float64")
    
    def _setupReflectionPass(self):
        """
        prepends a rendering pass each frame,
        rendering the reflected scene to fbo.
        """
        # get configurable map size
        w, h = self.segment.getAttr("reflectionMapSize", (512,512))
        self.reflectionColor = Texture2D(width=w, height=h)
        self.reflectionColor.create()
        reflectionDepth = DepthTexture2D(width=w, height=h)
        reflectionDepth.create()
        
        reflectionFBO = FBO()
        reflectionFBO.addColorTexture(self.reflectionColor)
        reflectionFBO.setDepthTexture(reflectionDepth)
        reflectionFBO.create()
        
        # draw the reflected scene with same camera as scene
        self.app.prependFBO(reflectionFBO,
                            self._drawReflectedScene,
                            self.app.sceneCamera)
    
    def _calcSceneReflectionMatrix(self):
        """
        calculates a matrix that reflects the scene at the given point.
        """
        n = self.normal
        p = self.position
        self.mirrorMat = identity(4, dtype=float32)
        self.mirrorMat[:3,:3] -=  2.0 * outer( n, n )
        self.mirrorMat[ 3,:3]  = (2.0 * vdot( p, n )) * n
        
        self.inverseMirrorMatrix = inverseCContiguous(self.mirrorMat)
    
    def _drawReflectedScene(self):
        gl.glPushMatrix()
        # apply the reflection matrix
        gl.glMultMatrixf(self.mirrorMat)
        
        # maintain shadow projection for reflection.
        # the shadow texture matrix was multiplied by the inverse scene model view matrix last,
        # but we need the inverse mirror matrix applied before, so this must be done:
        #   FOO * MV^-1 * MV * R^-1 * MV^-1
        #   the reflector could show shadows not visible in depth maps.
        gl.glMatrixMode(gl.GL_TEXTURE)
        for texMatUnit in self.shadowMatrixUnits:
            gl.glActiveTexture(gl.GL_TEXTURE0 + texMatUnit)
            gl.glPushMatrix()
            # TODO: mv * r^-1 * mv^-1 can be precalculated -> event handler
            gl.glMultMatrixf( self.app.sceneCamera.modelViewMatrix )
            gl.glMultMatrixf( self.inverseMirrorMatrix )
            gl.glMultMatrixf( self.app.sceneCamera.inverseModelViewMatrix )
        gl.glMatrixMode(gl.GL_MODELVIEW)
        
        # clip away everything below the plane
        gl.glClipPlane(gl.GL_CLIP_PLANE0, self.clipPlane)
        gl.glEnable(gl.GL_CLIP_PLANE0)
        
        # switch culling (since we scaled by -1)
        gl.glCullFace(gl.GL_FRONT)
        
        # TODO: recursive reflections ?
        #         at least if we see a reflector 'r'
        #         in this reflector, the reflector 'r'
        #         should allready have reflectionsapplied to it.
        #         there is also the rare case two reflectors reflect each other (maybe infinite),
        self.segment.hidden = True
        self.app.drawSceneComplete()
        self.segment.hidden = False
        
        # switch back some states
        gl.glDisable(gl.GL_CLIP_PLANE0)
        gl.glCullFace(gl.GL_BACK)
        
        # reset texture matrices for other passes
        gl.glMatrixMode(gl.GL_TEXTURE)
        for texMatUnit in self.shadowMatrixUnits:
            gl.glActiveTexture(gl.GL_TEXTURE0 + texMatUnit)
            gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        
        gl.glPopMatrix()

class PlanarReflectionFrag(FragShaderFunc):
    def __init__(self, intensity=1.0):
        FragShaderFunc.__init__(self, name='planarReflection')
        self.addConstant(type="float", name="reflectionIntensity", val=str(intensity.value))
        self.addUniform("sampler2D", "reflectionMap")
        self.addVarying("vec4", "reflectionUV")
    
    def code(self):
        return """
    void %(NAME)s(inout vec4 col)
    {
        col.xyz = mix( col.xyz, texture2DProj( reflectionMap, reflectionUV ).rgb , reflectionIntensity );
    }
""" % { 'NAME': self.name }

class PlanarReflectionVert (VertShaderFunc):
    def __init__(self, texIndex=0):
        VertShaderFunc.__init__(self, 'planarReflection')
        self.texIndex = texIndex
        self.addVarying("vec4", "reflectionUV")
    
    def code(self):
        return """
    void %(NAME)s()
    {
        // TODO: allow reflection distortion along normal
        reflectionUV = gl_TextureMatrix[%(TEX_INDEX)d] * vec4(vertexPosition, 1.0);
    }
""" % { 'NAME': self.name, 'TEX_INDEX': self.texIndex }



def createPlaneReflectionHandler(app, segment, shaderRet, textureRet):
    reflectionHandler = PlanarReflection(app, segment)
    reflectionHandler.create()
    
    # calculate plane normal
    pos = segment.vertices.data[0]
    
    x = ndarray( shape=(3,), dtype=float32, buffer=(segment.vertices.data[0] - segment.vertices.data[1]) )
    y = ndarray( shape=(3,), dtype=float32, buffer=(segment.vertices.data[2] - segment.vertices.data[1]) )
    nor = crossVec3Float32Normalized( x, y )
    
    reflectionHandler.setOrigin(pos, nor)
    # shader class must enable reflection map on specified unit
    textureRet.append((reflectionHandler.reflectionColor.glID,
                    gl.GL_TEXTURE_2D,
                    "sampler2D",
                    "reflectionMap", app.projectiveTextureIndex))
    # add shaders
    shader = PlanarReflectionFrag(segment.material.matReflection)
    shader.setArgs(["col"])
    shaderRet[FRAG_SHADER].functions.append(shader)
    
    shader = PlanarReflectionVert(app.projectiveTextureMatrixIndex)
    shader.setArgs([])
    shaderRet[VERT_SHADER].functions.append(shader)
    
    return reflectionHandler

