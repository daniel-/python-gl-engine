# -*- coding: UTF-8 -*-
'''
Created on 18.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from core.segments.tspace_varray import TSpaceSegment
from core.segments.normal_generator import genVertexNormalsUnplane
from core.segments.tangent_generator import genVertexTangentsUnplane

class PolygonSegment(TSpaceSegment):
    """
    a segment of triangles.
    """
    
    def __init__(self, name, params):
        TSpaceSegment.__init__(self, name, params)
    
    # polygon segment must generate tangents for unplane faces
    def generateTangents(self):
        return genVertexTangentsUnplane(self)
    def generateNormals(self):
        return genVertexNormalsUnplane(self)
