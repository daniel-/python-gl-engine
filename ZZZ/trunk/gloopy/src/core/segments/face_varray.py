# -*- coding: UTF-8 -*-
'''
Created on 18.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.util import listGet
from core.gl_vertex_attribute import uvAttribute, colorAttribute, normalAttribute
from core.segments.vbo_segment import VBOSegment
from utils.algebra.vector import almostEqual

class FaceVArray(VBOSegment):
    """
    vertex array with faces structure.
    """
    
    def __init__(self, name, params):
        # list of segment faces
        (self.faces, self.faceType, self.numFaceVertices) = params['faces']
        
        VBOSegment.__init__(self, name, params)
    
    def createResources(self):
        """
        face array creates per vertex data.
        some vertices may occur multiple times in the resulting array,
        depending on the per face data.
        """
        
        VBOSegment.createResources(self)
        
        if not self.hasNor() and not self.hasFaceNor():
            # we need to generate normals now
            self.updateNormalsArray()
    
    def createResourcesPost(self):
        """
        face array creates per vertex data.
        some vertices may occur multiple times in the resulting array,
        depending on the per face data.
        """
        
        VBOSegment.createResourcesPost(self)
        
        faceCol = self.hasFaceCol()
        faceUV  = self.hasFaceUV()
        faceNor = self.hasFaceNor()
        
        groupIndexes = []
        if faceNor:
            groupNormals = [None]*self.numVertices
        if faceUV:
            groupUV = [None]*self.numVertices
        if faceCol:
            groupColors = [None]*self.numVertices
        
        # remember processed vertices and per face data
        processedVertices = {}
        
        for f in self.faces:
            for i in range(len(f.indexes)):
                # get the index to per vertex lists
                j = f.indexes[i]
                
                # vertex index processed before?
                data = processedVertices.get(j)
                if data==None:
                    # if not set the data
                    processedVertices[j] = [(listGet(f.normals, i),
                                             listGet(f.uv, i),
                                             listGet(f.colors, i))]
                    if faceNor:
                        groupNormals[j] = f.normals[i]
                    if faceUV:
                        groupUV[j] = f.uv[i]
                    if faceCol:
                        groupColors[j] = f.colors[i]
                else:
                    # if this vertex index was processed before,
                    # check if per face data equals,
                    # else we need to add this vertex to the list.
                    # the vertex data will then be multiple times in the list.
                    (n0,u0,c0) = (listGet(f.normals, i),
                                  listGet(f.uv, i),
                                  listGet(f.colors, i))
                    
                    # check if face vertex equals saved vertex
                    isEqualVertex = True
                    for d in data:
                        (n1,u1,c1) = d
                        if almostEqual(n0,n1) and almostEqual(u0,u1) and almostEqual(c0,c1):
                            # if per face data is equal, do nothing
                            pass
                        else:
                            isEqualVertex = False
                            break
                    
                    if not isEqualVertex:
                        # let the class hierarchy push back one vertex attribute.
                        # for example a class may want to add a tangent now to the end of
                        # its tangent list.
                        self.duplicatePerVertexAttribute(j)
                        # face vertex index changed.
                        f.indexes[i] = self.numVertices-1
                        # remember this vertex.
                        processedVertices[j].append( (n0,u0,c0) )
                        if faceNor:
                            groupNormals.append( f.normals[i] )
                        if faceUV:
                            groupUV.append( f.uv[i] )
                        if faceCol:
                            groupColors.append( f.colors[i] )
            
            groupIndexes += list(f.indexes)
        
        self.indexes = groupIndexes
        if faceNor:
            self.normals.data = groupNormals
        if faceUV:
            self.uvs = uvAttribute(groupUV)
        if faceCol:
            self.colors = colorAttribute(groupColors)
    
    def addShaderAttributes(self, shaderFunc):
        VBOSegment.addShaderAttributes(self, shaderFunc)
        if self.hasFaceCol():
            shaderFunc.addAttribute(type="vec4", name="vertexColor")
        if self.hasFaceUV():
            shaderFunc.addAttribute(type="vec2", name="vertexUV")
        if self.hasFaceNor():
            shaderFunc.addAttribute(type="vec3", name="vertexNormal")
    
    def updateNormalsArray(self):
        if bool(self.normals):
            self.normals.data = self.generateNormals()
        else:
            self.normals = normalAttribute(self.generateNormals())
    def generateNormals(self):
        """
        method generates per vertex normals.
        """
        raise NotImplementedError
    
    def hasFaceCol(self):
        """
        per face color used?
        """
        for f in self.faces:
            if bool(f.colors):
                return True
        return False
    def hasCol(self):
        # implement for shader generating
        return self.hasFaceCol() or VBOSegment.hasCol(self)
    def hasFaceUV(self):
        """
        per face uv used?
        """
        for f in self.faces:
            if bool(f.uv):
                return True
        return False
    def hasFaceNor(self):
        """
        per face normal used?
        """
        for f in self.faces:
            if bool(f.normals):
                return True
        return False
