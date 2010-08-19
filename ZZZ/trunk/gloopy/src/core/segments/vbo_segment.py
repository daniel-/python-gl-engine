# -*- coding: UTF-8 -*-
'''
Created on 22.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl

from core.vbo import DynamicIntervealedVBO,\
                     StaticIntervealedVBO, VBO
from core.segments.varray import IndexedSegment
import numpy

class VBOSegment(IndexedSegment):
    def __init__(self, id, params):
        # static vertex data
        self.staticVBO = None
        # and dynamic vertex data for animations
        self.dynamicVBO = None
        # and static data for vertex indexes
        self.indexVBO = None
        
        self.staticAttributes = []
        self.dynamicAttributes = []
        
        IndexedSegment.__init__(self, id, params)
    
    def addAttribute(self, attribute):
        """
        must be called before create.
        """
        if not bool(attribute): return
        if self.isDynamicAttribute(attribute):
            self.dynamicAttributes.append(attribute)
        else:
            self.staticAttributes.append(attribute)
    
    def isDynamicAttribute(self, attribute):
        return False
    
    def postCreate(self):
        IndexedSegment.postCreate(self)
        
        # add attributes defined by parent class VArray
        self.addAttribute(self.vertices)
        self.addAttribute(self.normals)
        self.addAttribute(self.uvs)
        self.addAttribute(self.colors)
        
        # vertex data is supposed to be set up now,
        # and the segment shader created.
        # we can create the vbos now.
        self.createVBOs()
        
        # some stuff is not needed after create, delete it
        del self.staticAttributes
        del self.dynamicAttributes
        
        del self.indexes
        
        del self.vertices
        del self.normals
        del self.uvs
        del self.colors
        
    def createVBOs(self):
        # vbo containing the index data
        # the index data cannot be changed after creation.
        self.indexVBO = VBO(data=numpy.array( self.indexes, dtype=self.dtype ),
                            attributes=[],
                            segment=self,
                            bufferSize=self.indexBufferSize,
                            target=gl.GL_ELEMENT_ARRAY_BUFFER,
                            usage=gl.GL_STATIC_DRAW)
        # vbo containing static vertex data that cannot be changed
        self.staticVBO = StaticIntervealedVBO(
                            attributes=self.staticAttributes,
                            segment=self,
                            target=gl.GL_ARRAY_BUFFER)
        # vertex data for animations
        self.dynamicVBO = DynamicIntervealedVBO(
                            attributes=self.dynamicAttributes,
                            segment=self,
                            target=gl.GL_ARRAY_BUFFER)
    
    def enableStaticStates(self):
        IndexedSegment.enableStaticStates(self)
        self.indexVBO.bind()
        self.staticVBO.bind()
        self.staticVBO.bindAttributes()
    def enableDynamicStates(self):
        IndexedSegment.enableDynamicStates(self)
        self.dynamicVBO.bind()
        self.dynamicVBO.bindAttributes()
    
    def drawSegment(self):
        gl.glDrawElements(self.faceType,
                          self.numIndexes,
                          self.indextype,
                          self.indexVBO)
        # usefull if one vbo manages multiple segments
        #gl.glDrawRangeElements(self.faceType,
        #                       0, self.numVertices-1,
        #                       self.numIndexes,
        #                       self.indextype,
        #                       self.indexVBO)


