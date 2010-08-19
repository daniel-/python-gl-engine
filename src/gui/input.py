# -*- coding: UTF-8 -*-
'''
Created on 03.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

class JoyStick(object):
    '''
    joystick input device.
    you can add event handlers.
    '''
    
    STATE_INACTIVE = 0
    STATE_ACTIVE = 1
    # TODO: handle plug in/out JoyStick
    
    def __init__(self,
                 pygameJoy,
                 minThreshold=0.0,
                 maxThreshold=1.0):
        pygameJoy.init()
        
        self.pygameJoy = pygameJoy
        
        self.numButtons = pygameJoy.get_numbuttons()
        self.numHats    = pygameJoy.get_numhats()
        self.numAxes    = pygameJoy.get_numaxes()
        self.numBalls   = pygameJoy.get_numballs()
        
        self.buttonDownHandler = []
        self.buttonUpHandler = []
        self.hatHander = []
        self.axesMaxHandler = []
        self.axesDiffHandler = []
        
        for _ in range(self.numButtons):
            self.buttonUpHandler.append([])
            self.buttonDownHandler.append([])
        self.axes = []
        for _ in range(self.numAxes):
            self.axes.append((self.STATE_INACTIVE, 0.0))
    
    def setAxis(self, axis, newVal):
        """
        @param axis: a valid axis index
        @param value: the axis value
        """
        (state, lastVal) = self.axes[axis]
        
        # switch state with min threshold
        if state == self.STATE_ACTIVE:
            if newVal<=0.0:
                newState = self.STATE_INACTIVE
            else:
                newState = state
        else:
            if newVal>0.0:
                newState = self.STATE_ACTIVE
            else:
                newState = state
        
        if newState==self.STATE_ACTIVE:
            valDiff = lastVal - newVal
            if valDiff!=0.0:
                for handler in self.axesDiffHandler:
                    handler.setAxisDiff(axis, valDiff)
        
        wasMax = abs(lastVal)>=1.0
        isMax  = abs(newVal)>=1.0
        if not wasMax and isMax:
            for handler in self.axesMaxHandler:
                handler.setAxisActive(axis, newVal>0.0)
        elif wasMax and not isMax:
            for handler in self.axesMaxHandler:
                handler.setAxisInactive(axis)
        
        self.axes[axis] = (newState, newVal)
        
    def setBall(self, ball, rel):
        # TODO: setBall
        pass
    
    def setHat(self, hat, value):
        """
        @param hat: valif hat index
        @param value: int tuple descriping the state
        """
        
        (hor, vert) = value
        leftActive   = False
        rightActive  = False
        bottomActive = False
        topActive    = False
        
        if hor==-1:
            leftActive = True
        elif hor==1:
            rightActive = True
        if vert==-1:
            bottomActive = True
        elif vert==1:
            topActive = True
        
        for handler in self.hatHander:
            handler.setHat(hat,
                           leftActive, rightActive,
                           bottomActive, topActive)
    
    def buttonUp(self, button):
        for handler in self.buttonUpHandler[button]:
            handler.buttonUp(button)
    
    def buttonDown(self, button):
        for handler in self.buttonDownHandler[button]:
            handler.buttonDown(button)
    
    def addButtonUpHandler(self, button, handler):
        self.buttonUpHandler[button].append(handler)
    def addButtonDownHandler(self, button, handler):
        self.buttonDownHandler[button].append(handler)
    def addAxisMaxHandler(self, handler):
        self.axesMaxHandler.append(handler)
    def addAxisDiffHandler(self, handler):
        self.axesDiffHandler.append(handler)
    def addHatHandler(self, handler):
        self.hatHander.append(handler)
