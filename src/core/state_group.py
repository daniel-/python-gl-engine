# -*- coding: UTF-8 -*-
'''
Created on 24.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from core.gl_object import GLObject

class GLStateGroup(GLObject):
    """
    groups together some states.
    """
    
    def __init__(self, params, name, dynamic=False):
        self.name = name
        self.dynamic = dynamic
        GLObject.__init__(self, params)

