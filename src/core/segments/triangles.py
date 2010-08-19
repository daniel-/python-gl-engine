# -*- coding: UTF-8 -*-
'''
Created on 18.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from core.segments.tspace_varray import TSpaceSegment
from core.segments.normal_generator import genVertexNormalsPlane
from core.segments.tangent_generator import genVertexTangentsPlane

class TriangleSegment(TSpaceSegment):
    """
    a segment of triangles.
    """
    
    def __init__(self, name, params):
        TSpaceSegment.__init__(self, name, params)
    
    # triangles are plane surfaces
    def generateTangents(self):
        return genVertexTangentsPlane(self)
    def generateNormals(self):
        return genVertexNormalsPlane(self)
    