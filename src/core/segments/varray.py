# -*- coding: UTF-8 -*-
'''
Created on 06.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl

from segment import ModelSegment

class VArraySegment(ModelSegment):
    def __init__(self, name, params):
        # remember duplicated vertices for animation purpose
        self.duplicatedIndexes = {}
        
        # Note: vertex data here maybe deleted later (after create) to save some ram
        
        self.vertices = params['cos']
        conf = params.get('verticesConf')
        if conf!=None and conf.dynamic:
            self.dynamicVertices = True
        else:
            self.dynamicVertices = False
        
        self.normals = params.get('nos', None)
        conf = params.get('normalsConf')
        if conf!=None and conf.dynamic:
            self.dynamicNormals = True
        else:
            self.dynamicNormals = False
        
        self.uvs = params.get('uvco')
        conf = params.get('uvsConf')
        if conf!=None and conf.dynamic:
            self.dynamicUvs = True
        else:
            self.dynamicUvs = False
        
        self.colors = params.get('cols')
        conf = params.get('colorsConf')
        if conf!=None and conf.dynamic:
            self.dynamicColors = True
        else:
            self.dynamicColors = False
        
        self.numVertices = len(self.vertices.data)
        # num of vertices may change,
        # display lists may need lists with vertices added
        # multiple times.
        self.numInitialVertices = self.numVertices
        
        ModelSegment.__init__(self, name, params)
    
    def isDynamicAttribute(self, attribute):
        if self.vertices==attribute:
            return self.dynamicTangents
        elif self.normals==attribute:
            return self.dynamicNormals
        elif self.uvs==attribute:
            return self.dynamicUvs
        elif self.colors==attribute:
            return self.dynamicColors
        else:
            return VArraySegment.isDynamicAttribute(self, attribute)
    
    def duplicatePerVertexAttribute(self, index):
        """
        add vertex at @index to the end of the vertex list.
        vertex count will be 1 higher then before.
        this might be done for per face parameters.
        """
        
        # remember duplication for animations
        try:
            self.duplicatedIndexes[index].append(self.numVertices)
        except:
            self.duplicatedIndexes[index] = [self.numVertices]
        
        # one more vertex in the geometry
        self.numVertices += 1
        
        # duplicate vertex data
        self.vertices.data.append(self.vertices.data[index])
        if self.hasNor():
            self.normals.data.append(self.normals.data[index])
        if self.hasOrco():
            self.uvs.data.append(self.uvs.data[index])
        if self.hasCol():
            self.colors.data.append(self.colors.data[index])
    
    def addShaderAttributes(self, shaderFunc):
        """
        adds a per vertex shader attribute.
        """
        ModelSegment.addShaderAttributes(self, shaderFunc)
        if self.hasCol():
            shaderFunc.addAttribute(type="vec4", name="vertexColor")
        if self.hasOrco():
            shaderFunc.addAttribute(type="vec2", name="vertexUV")
        if self.hasNor():
            shaderFunc.addAttribute(type="vec3", name="vertexNormal")
    
    def hasCol(self):
        """
        returns if the segment has per vertex colors.
        """
        return bool(self.colors)
    def hasOrco(self):
        """
        returns if the segment has per vertex uv coordinates.
        """
        return bool(self.uvs)
    def hasNor(self):
        """
        returns if the segment has per vertex normals.
        """
        return bool(self.normals)

class IndexedSegment(VArraySegment):
    """
    segment with index list attribute.
    """
    
    def __init__(self, id, params):
        VArraySegment.__init__(self, id, params)
        
        self.indexes = params.get('indexes')
        self.numIndexes = params.get('numIndexes')
        self.faceType = params.get('primitive')
    
    def createResourcesPost(self):
        VArraySegment.createResourcesPost(self)
        
        # we can use different index array types depending
        # on the number of vertices.
        if self.numVertices<0xF:
            self.dtype='byte'
            self.indexBufferSize=self.numIndexes*1
            self.indextype = gl.GL_UNSIGNED_BYTE
        elif self.numVertices<0xFF:
            self.dtype='uint16'
            self.indexBufferSize=self.numIndexes*2
            self.indextype = gl.GL_UNSIGNED_SHORT
        elif self.numVertices<0xFFFF:
            self.dtype='uint32'
            self.indexBufferSize=self.numIndexes*4
            self.indextype = gl.GL_UNSIGNED_INT
        else:
            print "WARNING: more then %d vertices in one segment!" % 0xFFFF
            self.dtype='uint32'
            self.indexBufferSize=self.numIndexes*4
            self.indextype = gl.GL_UNSIGNED_INT
    
    def drawSegment(self):
        gl.glDrawElements(self.faceType,
                          self.numIndexes,
                          self.indextype,
                          self.indexes)
