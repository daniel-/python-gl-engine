# -*- coding: UTF-8 -*-
'''
Created on 20.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl
import OpenGL.GLU as glu

from utils.util import doNothing, joinFunctions
from core.gl_state import GLState

class SignalData(object):
    def __init__(self, id):
        self.id = id
        self.handlers = []
        self.queueEmit = False

class GLObject(object):
    queuedSignals = []
    nextSignalID = 0
    
    def __init__(self, params):
        # hashtable with state name as key
        self.states = {}
        
        self.signals = {}
        
        # static states will be saved in a list
        self.staticStateListIds = None
        self._enableStaticStates = doNothing
        self._disableStaticStates = doNothing
        
        # enable/disable all states that may change
        self._enableDynamicStates = doNothing
        self._disableDynamicStates = doNothing
        
        self.created = False
        self.popTransformations = False
        
        # add states
        states = params.get('states', [])
        stateSetter = {
            'pointSize': (self.enablePointSize, self.disablePointSize),
            'lineWidth': (self.enableLineWidth, self.disableLineWidth),
            'lineStipple': (self.enableLineStipple, self.disableLineStipple),
            'shadeModel': (self.enableShadeModel, self.disableShadeModel),
            'polygonMode': (self.enablePolygonMode, self.disablePolygonMode),
            'translation': (self.enableTranslation, doNothing),
            'rotation': (self.enableRotation, doNothing),
            'scaling': (self.enableScaling, doNothing),
            'evalPolygonMode': (doNothing, doNothing),
            'evalPolygonModeGLU': (self.enableEvalPolygonMode, doNothing),
            'evalTolerance': (self.enableEvalTolerance, doNothing),
            'lightDirection': (self.enableDirection, doNothing),
            'lightExponent': (self.enableExponent, doNothing),
            'lightCutOff': (self.enableCutOff, doNothing),
            'constantAttenuation': (self.enableConstAttenuation, doNothing),
            'linearAttenuation': (self.enableLinaerAttenuation, doNothing),
            'quadricAttenuation': (self.enableQuadricAttenuation, doNothing),
            'lightPosition': (self.enableLightPosition, doNothing),
            'lightAmbient': (self.enableLightAmbient, doNothing),
            'lightDiffuse': (self.enableLightDiffuse, doNothing),
            'lightSpecular': (self.enableLightSpecular, doNothing),
            'useShadowMap': (doNothing, doNothing),
            'matEmission': (self.enableMatEmission, doNothing),
            'matDiffuse': (self.enableMatDiffuse, doNothing),
            'matAmbient': (self.enableMatAmbient, doNothing),
            'matSpecular': (self.enableMatSpecular, doNothing),
            'matShininess': (self.enableMatShininess, doNothing),
            'matReflectionIntensity': (doNothing, doNothing),
            'matColor': (self.enableMatColor, self.disableMatColor),
            'reflectionMapSize': (doNothing, doNothing),
            'isPlane': (doNothing, doNothing)
        }
        for state in states:
            funcs = stateSetter.get(state.name)
            if funcs==None:
                print "ERROR: unknown state %s... skipping" % state.name
            else:
                state.enable, state.disable = funcs
                self.addState(state)
        
        # add state groups as simple states
        self.stateGroups = params.get('stateGroups', [])
        for group in self.stateGroups:
            state = GLState(group.name, None, dynamic=group.dynamic)
            if group.dynamic:
                state.enable  = group.enableDynamicStates
                state.disable = group.disableDynamicStates
            else:
                state.enable  = group.enableStaticStates
                state.disable = group.disableStaticStates
            self.addState(state)
    
    def getAttr(self, name, default=None):
        try:
            return self.__getattr__(name)
        except:
            return default
        
    
    def __getattr__(self, name):
        """
        make states accessable as attributes.
        """
        try:
            return self.states[name].value
        except:
            return object.__getattribute__(self, name)
    
    def addState(self, state):
        self.states[state.name] = state
    def removeState(self, state):
        del self.states[state.name]
    
    def createGuard(self, app, lights):
        if not self.created:
            self.create(app, lights)
    
    def create(self, app, lights):
        # remember to be created
        for grp in self.stateGroups:
            grp.create(app, lights)
        
        self.created = True
    def postCreate(self):
        # check if enabling this object will modify the model view matrix 
        self.popTransformations = self.hasTranslation() or\
                                  self.hasRotation() or\
                                  self.hasScaling()
    
    def createDrawFunction(self):
        """
        generate functions for enablin/disabling states.
        """
        staticStates = []
        dynamicStates = []
        
        for grp in self.stateGroups:
            grp.createDrawFunction()
        
        # split dynamic and static states
        for state in self.states.values():
            if state.dynamic:
                dynamicStates.append(state)
            else:
                staticStates.append(state)
        
        # create static state functions
        if bool(staticStates):
            self._enableStaticStates = doNothing
            self._disableStaticStates = doNothing
            for state in staticStates:
                self.joinStaticStates(enable=state.enable, disable=state.disable)
            
            self.staticStateListIds = [gl.glGenLists(1), gl.glGenLists(1)]
        
            # create list for setting static states
            gl.glNewList(self.staticStateListIds[0], gl.GL_COMPILE)
            self._enableStaticStates()
            gl.glEndList()
            def enableStaticList():
                gl.glCallList(self.staticStateListIds[0])
            self._enableStaticStates = enableStaticList
            
            # create list for unsetting static states
            gl.glNewList(self.staticStateListIds[1], gl.GL_COMPILE)
            self._disableStaticStates()
            gl.glEndList()
            def disableStaticList():
                gl.glCallList(self.staticStateListIds[1])
            self._disableStaticStates = disableStaticList
        else:
            self._enableStaticStates = doNothing
            self._disableStaticStates = doNothing
        
        # create dynamic state functions
        self._enableDynamicStates = doNothing
        self._disableDynamicStates = doNothing
        for state in dynamicStates:
            self.joinDynamicStates(enable=state.enable, disable=state.disable)
    
    def joinDynamicStates(self, enable=doNothing, disable=doNothing):
        """
        adds a enable and a disable dynamic state function to the state setter/unsetter
        of this object.
        """
        self._enableDynamicStates  = joinFunctions(self._enableDynamicStates, enable)
        self._disableDynamicStates = joinFunctions(self._disableDynamicStates, disable)
    def joinStaticStates(self, enable=doNothing, disable=doNothing):
        """
        adds a enable and a disable sstatic tate function to the state setter/unsetter
        of this object.
        """
        self._enableStaticStates  = joinFunctions(self._enableStaticStates, enable)
        self._disableStaticStates = joinFunctions(self._disableStaticStates, disable)
    
    # main entry functions for modifying the state
    def enableStaticStates(self):
        self._enableStaticStates()
    def disableStaticStates(self):
        self._disableStaticStates()
    def enableDynamicStates(self):
        self._enableDynamicStates()
    def disableDynamicStates(self):
        self._disableDynamicStates()
    
    def enableStates(self):
        self.enableStaticStates()
        self.enableDynamicStates()
    def disableStates(self):
        self.disableStaticStates()
        self.disableDynamicStates()
    
    def hasState(self, state):
        try:
            self.states[state]
            return True
        except KeyError:
            return False
    def hasTranslation(self):
        return self.hasState("translation")
    def hasRotation(self):
        return self.hasState("rotation")
    def hasScaling(self):
        return self.hasState("scaling")
    
    ### BASIC SIGNAL HANDLING
    
    def signalRegister(self, id):
        # create signal data
        self.signals[id] = SignalData(id)
    def signalUnregister(self, id):
        """ forget about a signal. """
        # delete the signal data
        del self.signals[id]
    
    def signalConnect(self, id, handler):
        """ connect a handler from a signal. """
        # FIXME: SIGNALS:  better way to ensure the correct order of handlers ?
        self.signals[id].handlers.append(handler)
    def signalDisconnect(self, id, handler):
        """ disconnect a handler from a signal. """
        self.signals[id].handlers.remove(handler)
    
    def signalQueueEmit(self, id):
        """ queues a signal for emitting. """
        signalData = self.signals[id]
        
        if signalData.queueEmit: return
        signalData.queueEmit = True
        GLObject.queuedSignals.append( signalData )
    
    @classmethod
    def signalsEmit(cls):
        """ emits queued signals for all objects. """
        # we use pop to allow handlers queue signals
        while cls.queuedSignals!=[]:
            signalData = cls.queuedSignals.pop()
            map( lambda h: h(), signalData.handlers )
            signalData.queueEmit = False
    @classmethod
    def signalCreate(cls):
        """ creates a signal, returing the id. """
        cls.nextSignalID += 1
        return cls.nextSignalID-1
    
    ### DEFAULT STATE HANDLER (nice to have them here)
    ### Note: state handler can access states as attributes with the dot operator,
    ###       the attributes dont need to be specified explicit,
    ###       addState does this job.
    
    def enablePointSize(self):
        gl.glPointSize( self.pointSize )
    def disablePointSize(self):
        gl.glPointSize( 1.0 )
    
    def enableLineWidth(self):
        gl.glPointSize( self.lineWidth )
    def disableLineWidth(self):
        gl.glPointSize( 1.0 )
    
    def enableLineStipple(self):
        stipple = self.lineStipple
        gl.glEnable( gl.GL_LINE_STIPPLE )
        gl.glLineStipple( stipple[0], stipple[1] )
    def disableLineStipple(self):
        gl.glDisable(gl.GL_LINE_STIPPLE)
    
    def enableShadeModel(self):
        gl.glShadeModel( self.shadeModel )
    def disableShadeModel(self):
        gl.glShadeModel( gl.GL_SMOOTH )
    
    def enablePolygonMode(self):
        front, back = self.polygonMode
        if front==back:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, front)
        else:
            gl.glPolygonMode(gl.GL_FRONT, front)
            gl.glPolygonMode(gl.GL_BACK, back)
    def disablePolygonMode(self):
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
    
    def enableEvalPolygonMode(self):
        glu.gluNurbsProperty(self.glID,
                             glu.GLU_DISPLAY_MODE,
                             self.evalPolygonMode)
    
    def enableEvalTolerance(self):
        glu.gluNurbsProperty(self.glID,
                             glu.GLU_SAMPLING_TOLERANCE,
                             self.evalTolerance)
    
    def enableTranslation(self):
        gl.glTranslatef(self.translation[0],
                        self.translation[1],
                        self.translation[2])
    
    def enableRotation(self):
        # TODO: allow centered rotation ?
        # TODO: quaternion rotation ?
        gl.glRotatef(self.rotation[0], 1.0, 0.0, 0.0)
        gl.glRotatef(self.rotation[1], 0.0, 1.0, 0.0)
        gl.glRotatef(self.rotation[2], 0.0, 0.0 ,1.0)
    
    def enableScaling(self):
        gl.glScalef(self.scale[0], self.scale[1], self.scale[2])

    def enableLightPosition(self):
        gl.glLightfv(self.glIndex,
                     gl.GL_POSITION,
                     self.lightPosition)
    def enableLightAmbient(self):
        gl.glLightfv(self.glIndex,
                     gl.GL_AMBIENT,
                     self.lightAmbient)
    def enableLightDiffuse(self):
        gl.glLightfv(self.glIndex,
                     gl.GL_DIFFUSE,
                     self.lightDiffuse)
    def enableLightSpecular(self):
        gl.glLightfv(self.glIndex,
                     gl.GL_SPECULAR,
                     self.lightSpecular)
    
    def enableConstAttenuation(self):
        gl.glLightf(self.glIndex,
                    gl.GL_CONSTANT_ATTENUATION,
                    self.constantAttenuation)
    def enableLinaerAttenuation(self):
        gl.glLightf(self.glIndex,
                    gl.GL_LINEAR_ATTENUATION,
                    self.linearAttenuation)
    def enableQuadricAttenuation(self):
        gl.glLightf(self.glIndex,
                    gl.GL_QUADRATIC_ATTENUATION,
                    self.quadricAttenuation)
    
    def enableDirection(self):
        gl.glLightfv(self.glIndex,
                     gl.GL_SPOT_DIRECTION,
                     self.lightDirection)
    def enableExponent(self):
        gl.glLightf(self.glIndex,
                    gl.GL_SPOT_EXPONENT,
                    self.lightExponent)
    def enableCutOff(self):
        gl.glLightf(self.glIndex,
                    gl.GL_SPOT_CUTOFF,
                    self.lightCutOff)
    
    def enableMatEmission(self):
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_EMISSION,  self.matEmission )
    def enableMatDiffuse(self):
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_DIFFUSE,   self.matDiffuse )
    def enableMatAmbient(self):
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT,   self.matAmbient )
    def enableMatSpecular(self):
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_SPECULAR,  self.matSpecular )
    def enableMatShininess(self):
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_SHININESS, (self.matShininess ))
    def enableMatColor(self):
        gl.glEnable( gl.GL_COLOR_MATERIAL )
        gl.glColor4fv( self.matColor )
    def disableMatColor(self):
        gl.glColor3f( 1.0, 1.0, 1.0 )
        gl.glDisable( gl.GL_COLOR_MATERIAL )
