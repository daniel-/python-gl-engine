# -*- coding: UTF-8 -*-
'''
Created on 18.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from core.segments.vbo_segment import VBOSegment

class PointSegment(VBOSegment):
    def __init__(self, name, params):
        VBOSegment.__init__(self, name, params)
