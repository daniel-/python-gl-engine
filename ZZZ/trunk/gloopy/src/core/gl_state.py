# -*- coding: UTF-8 -*-
'''
Created on 20.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''
from utils.util import doNothing

class GLState(object):
    """
    object representing a opengl state.
    """
    
    def __init__(self, name, value, dynamic=False):
        # state name
        self.name = name
        # value of the state
        self.value = value
        # state value changes ?
        self.dynamic = dynamic
        
        # enable this state
        self.enable  = doNothing
        # disable this state
        self.disable = doNothing
