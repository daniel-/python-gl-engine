# -*- coding: UTF-8 -*-
'''
Created on 22.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl

def normalAttribute(normals):
    return GLVertexAttribute(name="vertexNormal",
                            data=normals,
                            elementSize=3*4,      # 3 (x/y/z) times 4 byte (sizeof float)
                            normalize=False,
                            dataType=gl.GL_FLOAT)

def uvAttribute(uvs):
    return GLVertexAttribute(name="vertexUV",
                            data=uvs,
                            elementSize=2*4,      # 2 (u/v) times 4 byte (sizeof float)
                            normalize=False,
                            dataType=gl.GL_FLOAT)

def colorAttribute(colors):
    return GLVertexAttribute(name="vertexColor",
                            data=colors,
                            elementSize=4*4,      # 4 (r/g/b/a) times 4 byte (sizeof float)
                            normalize=False,
                            dataType=gl.GL_FLOAT)

class GLVertexAttribute(object):
    def __init__(self,
                 name,
                 data,
                 elementSize=12,
                 normalize=False,
                 isDynamic=False,
                 dataType=gl.GL_FLOAT):
        self.name = name
        self.data = data
        # data is normalized ?
        self.normalize = normalize
        self.dataType = dataType
        # size of a single attribute in byte
        self.elementSize = elementSize
        # how many values are stored per vertex 
        self.valsPerElement = len(data[0])
        # location of the attribute in the shader program
        self.location = -1
        # offset in the array where this attribute starts
        self.offset = 0
        # offset to the next attribute of this type.
        self.stride = 0
    
    def __str__(self):
        return self.name
