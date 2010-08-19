# -*- coding: UTF-8 -*-
'''
Created on 11.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl
from OpenGL.arrays.arraydatatype import ArrayDatatype
from OpenGL.arrays.vbo import VBO as GLVBO
from OpenGL.raw.GL.VERSION.GL_1_5 import glBindBuffer as glBindBufferRAW

import numpy

from utils.util import doNothing

class VBO(GLVBO):
    def __init__(self,
                 data,
                 attributes,
                 segment,
                 bufferSize,
                 target=gl.GL_ARRAY_BUFFER,
                 usage=gl.GL_STATIC_DRAW):
        self.target = target
        self.usage = usage
        
        if data==None or data.size==0:
            self.bind = doNothing
            self.bindAttributes = doNothing
            self.unbind = doNothing
            return
        
        GLVBO.__init__(self,
                       data=data,
                       usage=usage,
                       target=target,
                       size=bufferSize)
        
        self.segment = segment
        
        # GLVertexAttribute instances
        self.attributes = []
        
        # queued slices
        self.slices = []
        
        self.DUMMY = False
        
        # remember attribute locations in the shader
        for att in attributes:
            att.location = gl.glGetAttribLocation(segment.shaderProgram, att.name)
            if att.location!=-1:
                self.attributes.append(att)
            else:
                print "WARNING: cannot find attribute %s in shader" % att.name
    
    def queueSetSlice(self, start, size, data):
        """
        adds a data slice for later uploading to gl.
        """
        self.slices.append( (start, size, data) )
    def doSetSlices(self):
        """
        insert previously queued slice data into vbo.
        """
        for (start, size, data) in self.slices:
            self.setSlice(start, size, data)
        self.slices = []
    
    def setSlice(self, start, size, data):
        """
        sets a slice of data.
        """
        dataptr = ArrayDatatype.voidDataPointer( data )
        gl.glBufferSubData( self.target, start, size, dataptr )
    
    def setAttributeData(self, attributeIndex, data):
        """
        updates data for one attribute only.
        """
        raise NotImplementedError
    
    def bindAttributes(self):
        """
        bind the vertex attributes to the shader locations.
        """
        for att in self.attributes:
            if att.normalize:
                normalize = gl.GL_TRUE
            else:
                normalize = gl.GL_FALSE
            # FIXME: VBO: bottleneck NO.1 bad glVertexAttribPointer
            gl.glVertexAttribPointer(att.location,
                                     att.valsPerElement,
                                     att.dataType,
                                     normalize,
                                     att.stride,          # offset in data array to the next attribute
                                     self + att.offset)   # offset in data array to the first attribute
    
    def bind(self):
        """
        bind the vbo to the gl context.
        needs to be done before accessing the vbo.
        """
        GLVBO.bind(self)
        for att in self.attributes:
            gl.glEnableVertexAttribArray( att.location )


class SerializedVBO(VBO):
    def __init__(self,
                 attributes,
                 segment,
                 target=gl.GL_ARRAY_BUFFER,
                 usage=gl.GL_STATIC_DRAW):
        vertexData = []
        currOffset = 0
        for att in attributes:
            # all attributes of this type come one after another in the array
            att.stride = 0
            
            # offset in the serialized array where this attribute starts
            att.offset = currOffset
            currOffset += segment.numVertices * att.elementSize
            
            # calc size used by this attribute
            att.size = att.elementSize * segment.numVertices
            
            # add the attribute data, att.data not needed afterwards
            for d in att.data:
                for i in range(len(d)):
                    vertexData.append(d[i])
            del att.data
        
        VBO.__init__(self,
                     attributes=attributes,
                     segment=segment,
                     data=numpy.array( vertexData, dtype='float32' ),
                     bufferSize=currOffset,
                     target=target,
                     usage=usage)
        
        self.bufferSize = currOffset
    
    def setAttributeData(self, attriuteIndex, data):
        """
        cheanges data for only one attribute.
        """
        att = self.attributes[attriuteIndex]
        self.setSlice(start=att.offset, stop=att.size, data=data)
    
class DynamicSerializedVBO(SerializedVBO):
    def __init__(self,
                 attributes,
                 segment,
                 target=gl.GL_ARRAY_BUFFER):
        SerializedVBO.__init__(self,
                     attributes=attributes,
                     segment=segment,
                     target=target,
                     usage=gl.GL_DYNAMIC_DRAW)
class StaticSerializedVBO(SerializedVBO):
    def __init__(self,
                 attributes,
                 segment,
                 target=gl.GL_ARRAY_BUFFER):
        SerializedVBO.__init__(self,
                     attributes=attributes,
                     segment=segment,
                     target=target,
                     usage=gl.GL_STATIC_DRAW)

class IntervealedVBO(VBO):
    def __init__(self,
                 attributes,
                 segment,
                 target=gl.GL_ARRAY_BUFFER,
                 usage=gl.GL_STATIC_DRAW):
        # add the attribute data
        data = []
        for i in range(segment.numVertices):
            for att in attributes:
                for d in att.data[i]:
                    data.append(d)
        
        # get the attribute struct size
        attributeStructSize = 0
        for att in attributes:
            attributeStructSize += att.elementSize
        
        attSize = 0
        bufferSize = 0
        for att in attributes:
            # offset to the next attribute of this type (from start of this element).
            att.stride = attributeStructSize
            # offset in the intervealed array where this attribute starts
            att.offset = attSize
            attSize += att.elementSize
            bufferSize += segment.numVertices * att.elementSize
            # att.data will not be used anymore
            del att.data
        
        VBO.__init__(self,
                     attributes=attributes,
                     segment=segment,
                     data=numpy.array( data, dtype='float32' ),
                     bufferSize=bufferSize,
                     target=target,
                     usage=usage)

        
class DynamicIntervealedVBO(IntervealedVBO):
    def __init__(self,
                 attributes,
                 segment,
                 target=gl.GL_ARRAY_BUFFER):
        IntervealedVBO.__init__(self,
                     attributes=attributes,
                     segment=segment,
                     target=target,
                     usage=gl.GL_DYNAMIC_DRAW)
class StaticIntervealedVBO(IntervealedVBO):
    def __init__(self,
                 attributes,
                 segment,
                 target=gl.GL_ARRAY_BUFFER):
        IntervealedVBO.__init__(self,
                     attributes=attributes,
                     segment=segment,
                     target=target,
                     usage=gl.GL_STATIC_DRAW)
