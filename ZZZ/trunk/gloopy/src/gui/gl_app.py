# -*- coding: UTF-8 -*-
'''
Created on 02.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from sys import maxint

from utils.gl_config import importGL, printGLInfo
OpenGL = importGL()
from OpenGL.GL import GL_CULL_FACE,\
                      GL_COMPILE,\
                      GL_PERSPECTIVE_CORRECTION_HINT,\
                      GL_NICEST
from OpenGL.GL import glGenLists,\
                      glNewList,\
                      glCallList,\
                      glEndList,\
                      glEnable,\
                      glHint

import pygame
from pygame.locals import *
from pygame import image
from pygame.display import flip as flipDisplay
from pygame.event import get as getEvents

from utils.algebra.matrix44 import getProjectionMatrix, getOrthogonalProjectionMatrix

from core.free_type import FontData
from core.gl_object import GLObject

from gui.input import JoyStick

        
# default fullscreen toggling
isFullscreenEvent = \
    lambda e: e.type == KEYDOWN and e.key == K_F10
# default exit function
isQuitEvent = lambda e: e.type == KEYDOWN and \
    e.key == K_F4 and bool(e.mod & KMOD_ALT)

class GLApp(GLObject):
    '''
    creates gl window and handles event management and drawing.
    '''
    
    APP_SIZE_SIGNAL = GLObject.signalCreate()
    APP_PROJECTION_CHANGED = GLObject.signalCreate()

    def __init__(self,
                 winSize=(1024,768),
                 modes=OPENGL|DOUBLEBUF|HWSURFACE,
                 nearClip=1.0,
                 farClip=200.0,
                 fov=45.0,
                 caption='OpenGL fun',
                 iconName=None,
                 useJoysticks=[0],
                 hideCursor=False):
        '''
        Constructor, opens the window and initials opengl/pygame.
        '''
        
        GLObject.__init__(self, {})
        # signal stuff
        self.signalRegister( GLApp.APP_SIZE_SIGNAL )
        self.signalRegister( GLApp.APP_PROJECTION_CHANGED )
        
        self.modes = modes
        self.winSize = winSize
        
        self.timePassed = 0
        self.FPS = 0
        
        self.farClip  = farClip
        self.nearClip = nearClip
        self.fov      = fov
        
        self.caption = caption
        
        self.sceneBounds = None
        
        # save the projection for faster calculations
        self.projectionMat = None
        
        pygame.init()
        
        # init display
        pygame.display.gl_set_attribute(pygame.GL_RED_SIZE,   8)
        pygame.display.gl_set_attribute(pygame.GL_GREEN_SIZE, 8)
        pygame.display.gl_set_attribute(pygame.GL_BLUE_SIZE,  8)
        pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)
        # vsync
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        
        (self.screen, self.winSize) = self.setWindowSize(winSize)
        
        print "INFO: OpenGL and PyGame initialed."
        printGLInfo()
        
        # hide cursor for custom mouse drawing
        pygame.mouse.set_visible(not hideCursor)
        
        # lookup joystick devices
        if useJoysticks!=[]:
            numJoysticks = pygame.joystick.get_count()
            self.joypads = []
            
            if not numJoysticks:
                print "WARNING: No joystick connected."
            else:
                if numJoysticks<len(useJoysticks):
                    print "WARNING: Only %d joysticks connected." % numJoysticks
                for x in useJoysticks:
                    if x < numJoysticks:
                        j = pygame.joystick.Joystick(x)
                        self.joypads.append(JoyStick(j))
                        
                        print "INFO: Using joystick: '%s' with %d buttons and %d axes." \
                                    % (j.get_name(), j.get_numbuttons(), j.get_numaxes())
        else:
            self.joypads = []
        
        # set window title
        pygame.display.set_caption(caption)
        # set window icon
        if iconName!=None:
            surface = image.load("../textures/" + iconName)
            pygame.display.set_icon(surface)
        
        self.loadFonts()
        
        self.running = True
        (self.mouseX, self.mouseY) = (0, 0)
        
        self.initGL()
    
    def setSceneBounds(self, bounds, radius):
        self.sceneBounds = ( bounds, radius )
    
    def initGL(self):
        glEnable(GL_CULL_FACE)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    
    def __del__(self):
        """
        cleanup...
        """
        pass
    
    def loadFonts(self):
        self.mainFont = FontData ("../data/arial.ttf", 16)
    
    def setWindowSize(self, (w,h)):
        """sets the window size."""
        modes = pygame.display.list_modes()
        
        self.halfSize = [0.5*w, 0.5*h]
        
        # get the mode that matches w/h best
        size = (0,0)
        minDiff = maxint
        for (fw,fh) in modes:
            diff = abs(fw-w) + abs(fh-h)
            if diff<minDiff:
                minDiff = diff
                size = (fw,fh)
        
        if minDiff!=0:
            print "WARNING: cannot set window size to (%d,%d) !" % (w,h) +\
                  "falling back to (%d,%d)." % (size[0],size[1])
        
        # set the size
        screen = pygame.display.set_mode(size, self.modes)
        
        self.aspect = float(size[0])/float(size[1])
        
        # remember projection matrices
        self.projectionMatrix = getProjectionMatrix(self.fov,
                                                    self.aspect,
                                                    self.nearClip,
                                                    self.farClip)
        self.orthoMatrix = getOrthogonalProjectionMatrix(0.0, float(size[0]),
                                                         0.0, float(size[1]),
                                                         -1.0, 1.0)
        
        self.signalQueueEmit( GLApp.APP_SIZE_SIGNAL )
        
        return (screen, size)
    
    def toggleFullscreen(self):
        pygame.display.toggle_fullscreen()
    
    def getMousePosition(self):
        return (self.mouseX, self.mouseY)
    
    def close(self):
        """ sets running flag to false """
        self.running = False
    
    def mainloop(self):
        clock = pygame.time.Clock()
        self.timePassed = 1.0
        self.fpsDisplayList = glGenLists(1)
        
        # introduce some local variables to avoid the dot operator
        processFrame = self.processFrame
        processEvent = self.processEvent
        tick = clock.tick
        self.getFPS = clock.get_fps
        self.printFPS = self.mainFont.glPrint
        self.fpsY = self.winSize[1]-5-self.mainFont.fontHeight
        
        def _processEvent(event):
            if event.type == MOUSEMOTION:
                (self.mouseX, self.mouseY) = event.pos
            
            if isFullscreenEvent(event):
                self.toggleFullscreen()
            # Joystick event handling
            elif event.type == JOYAXISMOTION:
                joystick = self.joypads[event.joy]
                joystick.setAxis(event.axis, event.value)
            elif event.type == JOYBALLMOTION:
                joystick = self.joypads[event.joy]
                joystick.setBall(event.ball, event.rel)
            elif event.type == JOYHATMOTION:
                joystick = self.joypads[event.joy]
                joystick.setHat(event.hat, event.value)
            elif event.type == JOYBUTTONUP:
                joystick = self.joypads[event.joy]
                joystick.buttonUp(event.button)
            elif event.type == JOYBUTTONDOWN:
                joystick = self.joypads[event.joy]
                joystick.buttonDown(event.button)
            elif event.type == QUIT or isQuitEvent(event):
                self.running = False
            # Custom event handling
            else:
                processEvent(event)
        
        while self.running:
            # process events
            map(_processEvent, getEvents())
            
            self.timePassed = tick()
            self.passedSecs = self.timePassed/1000.0
            
            # redraw
            processFrame(self.passedSecs)
            
            # Show the screen, wait on monitor vertical retrace to avoid tearing
            flipDisplay()
            
            self.animationStep()
    
    def animationStep(self):
        pass
    
    def orthogonalPass(self):
        """ display FPS. """
        
        secs = self.passedSecs
        self.timePassed += secs
        
        if self.timePassed>=1.0:
            self.timePassed -= 1.0
            fps = self.getFPS()
            
            if fps!=self.FPS:
                self.FPS = fps
                glNewList(self.fpsDisplayList, GL_COMPILE)
                self.printFPS(5, self.fpsY, "FPS %d" % self.FPS)
                glEndList()
        
        # we expect to be in orthogonal projection now
        glCallList(self.fpsDisplayList)
        
    def processEvent(self, event):
        """ process one event in queue """
        pass
    def processFrame(self, timePassedSecs):
        """ draws a scene """
        pass
                

if __name__ == '__main__':
    app = GLApp()
    app.mainloop()
