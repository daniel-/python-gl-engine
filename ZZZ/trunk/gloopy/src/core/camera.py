# -*- coding: UTF-8 -*-
'''
Created on 02.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

import pygame
from pygame.locals import *

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL.GL import glLoadIdentity, glMatrixMode, glLoadMatrixf, glGetFloatv
from OpenGL.GL import GL_PROJECTION, GL_PROJECTION_MATRIX
from OpenGL.GLU import gluLookAt

from numpy import array, float32

from utils.algebra.vector import normalize, rotateView
from utils.algebra.matrix44 import lookAtCameraInverse
from core.gl_object import GLObject

class Camera(GLObject):
    """
    a camera object with a position that can be enabled.
    """
    
    # signal stuff
    CAMERA_MODELVIEW_SIGNAL = GLObject.signalCreate()
    
    def __init__(self, position=None):
        GLObject.__init__(self, {})
        
        # the camera position
        self.position = position
        # model viw matrix of this camera
        self.modelViewMatrix = None
        print "REGISTER CAM MV ", Camera.CAMERA_MODELVIEW_SIGNAL
        # register the signal on this object
        self.signalRegister( Camera.CAMERA_MODELVIEW_SIGNAL )
    
    def setPosition(self, position):
        self.position = position
    def getPosition(self):
        return self.position
    
    def updateMatrix(self):
        """ recalculate matrix. """
        raise NotImplementedError

    def enable(self):
        """ enable float32 matrix. """
        glLoadMatrixf( self.modelViewMatrix )


class DirectionalCamera(Camera):
    """
    a camera that points in a direction.
    """
    
    def __init__(self, position=None, direction=None):
        Camera.__init__(self, position)
        self.direction = direction
    
    def getDirection(self):
        return self.direction
    def setDirection(self, direction):
        self.direction = direction
    
    def updateMatrix(self):
        # create float32 look at matrix
        pos  = self.position
        view = self.direction
        
        # for some reason this is faster then calling the cython code
        glMatrixMode( GL_PROJECTION )
        glLoadIdentity()
        gluLookAt(pos[0], pos[1], pos[2],
                  pos[0] + view[0],
                  pos[1] + view[1],
                  pos[2] + view[2],
                  0.0, 1.0, 0.0)
        self.modelViewMatrix = glGetFloatv( GL_PROJECTION_MATRIX )
        
        # emit signal that the modelview matrix changed
        self.signalQueueEmit( Camera.CAMERA_MODELVIEW_SIGNAL )

class UserCamera(DirectionalCamera):
    """
    a camera with some event handling for changing
    position and direction.
    """
    
    class JoyHandler():
        def __init__(self, numAxes):
            self.axes = []
            for _ in range(numAxes):
                self.axes.append(0.0)
        def setAxisActive(self, axis, positive):
            if positive:
                self.axes[axis] = 1.0
            else:
                self.axes[axis] = -1.0
        def setAxisInactive(self, axis):
            self.axes[axis] = 0.0
    
    def __init__(self,
                 app,
                 sensitivity=0.002,
                 walkSpeed=0.5,
                 position=None,
                 direction=None):
        # make sure we have a position and direction
        if position==None:
            position = array([0.0, 1.0, 4.0], float32)
        if direction==None:
            direction = array([0.0, 0.0, -1.0], float32)
        
        DirectionalCamera.__init__(self, position, direction)
        
        self.app = app
        self.joyHandler = None
        
        # mouse movement sensitivity
        self.sensitivity = sensitivity
        # translation speed
        self.walkSpeed = walkSpeed
        
        # remember last position
        self.lastX = 0
        self.lastY = 0
        
        # toggle for left mouse button
        self.leftMouseButtonPressed = False
        self.needsUpdate = False
        
        # initialize the matrix
        self.updateMatrix()
    
    def useJoyStick(self, joy):
        if self.joyHandler == None:
            self.joyHandler = self.JoyHandler(joy.numAxes)
            joy.addAxisMaxHandler(self.joyHandler)
    
    def motion(self, x, y):
        """ mouse motion event handler,
            only rotates if button 1 pressed. """
        
        x -= self.app.halfSize[0]
        y -= self.app.halfSize[1]
        
        if not self.leftMouseButtonPressed:
            self.lastX = x
            self.lastY = y
            return
    
        rotX = - float(x - self.lastX) * self.sensitivity
        rotY = - float(y - self.lastY) * self.sensitivity

        rotateView( self.direction, rotX, 0.0, 1.0, 0.0 )
        
        rotAxis = array( [ -self.direction[2], 0.0, self.direction[0] ] , float32 )
        normalize( rotAxis )
        rotateView( self.direction, rotY, rotAxis[0], rotAxis[1], rotAxis[2] )
        
        self.lastX = x
        self.lastY = y
        self.needsUpdate = True

    def updateKeys(self):
        """ updates translation with pressed keys. """
        pressed = pygame.key.get_pressed()
            
        if pressed[K_w]:
            self.position += self.direction * self.walkSpeed
            self.needsUpdate = True
        if pressed[K_s]:
            self.position -= self.direction * self.walkSpeed
            self.needsUpdate = True
        if pressed[K_a]:
            self.position[0] += self.direction[2] * self.walkSpeed
            self.position[2] -= self.direction[0] * self.walkSpeed
            self.needsUpdate = True
        if pressed[K_d]:
            self.position[0] -= self.direction[2] * self.walkSpeed
            self.position[2] += self.direction[0] * self.walkSpeed
            self.needsUpdate = True
        
        if self.joyHandler != None:
            pass
            #self.movementDirection[0] += self.joyHandler.axes[0]
            #self.movementDirection[2] += self.joyHandler.axes[1]
            #self.rotationDirection[0] -= self.joyHandler.axes[2]
            #self.rotationDirection[1] -= self.joyHandler.axes[3]
    
    
    def updateMatrix(self):
        DirectionalCamera.updateMatrix(self)
        self.inverseModelViewMatrix = lookAtCameraInverse(self.modelViewMatrix)
    
    def update(self):
        if not self.needsUpdate:
            return
        self.needsUpdate = False
        self.updateMatrix()
    
    def mouseEvent(self, button, state, x, y):
        """ mouse button event handler. """
        self.lastX = x - self.app.halfSize[0]
        self.lastY = y - self.app.halfSize[1]
        
        if button==1:
            if state==MOUSEBUTTONUP:
                self.leftMouseButtonPressed = False
            elif state==MOUSEBUTTONDOWN:
                self.leftMouseButtonPressed = True

