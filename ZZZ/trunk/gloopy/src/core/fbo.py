# -*- coding: UTF-8 -*-
'''
Created on 08.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl
from OpenGL.GL import framebufferobjects as glFBO

from numpy import array as NumpyArray

class FBOError(ValueError):
    def __init__(self, message):
        ValueError.__init__(self, message)

class FBO(object):
    """
    helper for frame buffer objects.
    you can add textures to this class, then calling create() to create the fbo.
    """
    
    MAX_TARGETS = None

    def __init__(self):
        # gl handle
        self.glFBO = -1
        # size of textures
        self.size = None
        # list of color textures (can be accessed by fragData[i])
        self.colorTextures = []
        # depth, stencil, depthStencil texture to use
        self.depthTexture = None
        self.stencilTexture = None
        self.depthStencilTexture = None
        # some flags
        self.hasColor = False
        self.hasDepth = False
        self.hasStencil = False
        self.hasDepthStencil = False
        self.depthOnly = False
        # set class var (gl needs to be initialled before)
        if FBO.MAX_TARGETS==None:
            FBO.MAX_TARGETS = gl.glGetInteger(glFBO.GL_MAX_COLOR_ATTACHMENTS)
    
    def __del__(self):
        if self.glFBO!=-1:
            if bool(glFBO.glDeleteFramebuffers):
                glFBO.glDeleteFramebuffers(1, [self.glFBO])
            else:
                # gl module might already uninitialled
                pass
    
    def _setSize(self, tex):
        #if self.size==None:
        self.size = (tex.width, tex.height)
    
    def checkError(self):
        """
        raises fbo error if something went wrong.
        """
        error = glFBO.glCheckFramebufferStatusEXT(glFBO.GL_FRAMEBUFFER)
        if error == glFBO.GL_FRAMEBUFFER_COMPLETE:
            pass
        elif error == glFBO.GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT:
            raise FBOError, 'Incomplete attachment'
        elif error == glFBO.GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT:
            raise FBOError, 'Missing attachment'
        elif error == glFBO.GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS:
            raise FBOError, 'Incomplete dimensions'
        elif error == glFBO.GL_FRAMEBUFFER_INCOMPLETE_FORMATS:
            raise FBOError, 'Incomplete formats'
        elif error == glFBO.GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER:
            raise FBOError, 'Incomplete draw buffer'
        elif error == glFBO.GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER:
            raise FBOError, 'Incomplete read buffer'
        elif error == glFBO.GL_FRAMEBUFFER_UNSUPPORTED:
            raise FBOError, 'Framebufferobjects unsupported'
    
    # add textures to fbo
    def setDepthTexture(self, depthTexture):
        self.depthTexture = depthTexture
        self._setSize(depthTexture)
    def setStencilTexture(self, stencilTexture):
        self.stencilTexture = stencilTexture
        self._setSize(stencilTexture)
    def setDepthStencilTexture(self, depthStencilTexture):
        self.depthStencilTexture = depthStencilTexture
        self._setSize(depthStencilTexture)
    def addColorTexture(self, colorTexture):
        if FBO.MAX_TARGETS==len(self.colorTextures):
            raise FBOError, "number of render targets error!"
        self.colorTextures.append(colorTexture)
        self._setSize(colorTexture)
    
    def enable(self):
        """
        enables render to texture.
        Note: you must set the colormask before for depth only textures.
        """
        glFBO.glBindFramebuffer(glFBO.GL_FRAMEBUFFER, self.glFBO)
        
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        # set viewport to textures size
        gl.glViewport(0, 0, self.size[0], self.size[1])
        
        if self.colorTextures != []:
            # enable draw buffers
            gl.glDrawBuffers(self.numBuffers, self.colorBuffers)
    def enableDepthFast(self):
        glFBO.glBindFramebuffer(glFBO.GL_FRAMEBUFFER, self.glFBO)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)
    
    @staticmethod
    def disable():
        """
        disables render to texture.
        """
        glFBO.glBindFramebuffer(glFBO.GL_FRAMEBUFFER, 0)
        gl.glDrawBuffers(1, 0)
    
    def create(self):
        """
        creates the fbo, call only once after configuration done.
        you have to add textures before.
        """
        
        self.hasColor        = self.colorTextures != []
        self.hasDepth        = self.depthTexture != None
        self.hasStencil      = self.stencilTexture != None
        self.hasDepthStencil = self.depthStencilTexture != None
        self.depthOnly       = self.hasDepth and not self.hasColor
        
        # create and bind fbo
        self.glFBO = glFBO.glGenFramebuffers(1)
        glFBO.glBindFramebuffer(glFBO.GL_FRAMEBUFFER, self.glFBO)
        
        if self.depthOnly:
            # only draw depth
            gl.glDrawBuffer(gl.GL_NONE)
            gl.glReadBuffer(gl.GL_NONE)
        
        # add textures
        for i in range(len(self.colorTextures)):
            tex = self.colorTextures[i]
            glFBO.glFramebufferTexture2D(glFBO.GL_FRAMEBUFFER,
                                         glFBO.GL_COLOR_ATTACHMENT0+i,
                                         tex.targetType,
                                         tex.glID,
                                         0)
        if self.hasDepth:
            glFBO.glFramebufferTexture2D(glFBO.GL_FRAMEBUFFER,
                                         glFBO.GL_DEPTH_ATTACHMENT,
                                         self.depthTexture.targetType,
                                         self.depthTexture.glID,
                                         0)
        if self.hasStencil:
            glFBO.glFramebufferTexture2D(glFBO.GL_FRAMEBUFFER,
                                         glFBO.GL_STENCIL_ATTACHMENT,
                                         self.stencilTexture.targetType,
                                         self.stencilTexture.glID,
                                         0)
        if self.hasDepthStencil:
            glFBO.glFramebufferTexture2D(glFBO.GL_FRAMEBUFFER,
                                         glFBO.GL_DEPTH_STENCIL_ATTACHMENT,
                                         self.depthStencilTexture.targetType,
                                         self.depthStencilTexture.glID,
                                         0)
        
        # check if everything is ok with the fbo
        self.checkError()
        
        # release fbo
        glFBO.glBindFramebuffer(glFBO.GL_FRAMEBUFFER, 0)
        
        # remember color buffers
        if self.colorTextures != []:
            self.numBuffers = len(self.colorTextures)
            data = map(lambda x: glFBO.GL_COLOR_ATTACHMENT0+x, range(self.numBuffers))
            self.colorBuffers = NumpyArray(data, "I")
        
        