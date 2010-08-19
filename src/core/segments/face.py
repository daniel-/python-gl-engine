# -*- coding: UTF-8 -*-
'''
Created on 01.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''
from utils.algebra.vector import almostEqual, crossVec3Float32

class VArrayFace(object):
    def __init__(self, params):
        # indexes of vertexes in array
        self.indexes = params['i']
        # per face coordinates
        self.uv = params.get('uv')
        self.colors = params.get('col')
        self.normals = params.get('nor')
    
    def getPlaneFaces(self, segment):
        """
        create multiple plane faces for this face.
        """
        
        # successive vertices with same normal
        normalGroups = []
        # normal of last processed vertex
        lastNormal = None
        currentGroup = None
        
        # create face groups, with vertices sharing a plane.
        vertices = map(lambda i: segment.vertices.data[i], self.indexes)
        for i in range(len(vertices)):
            # lookup indexes of neighbor vertices in segment
            i0 = self.indexes[i-2]
            i1 = self.indexes[i-1]
            i2 = self.indexes[i]
            v0 = segment.vertices.data[i0]
            v1 = segment.vertices.data[i1]
            v2 = segment.vertices.data[i2]
            
            # Calculate vertex normal.
            edge1 = v2 - v1
            edge2 = v0 - v1
            normal = crossVec3Float32( edge1, edge2 )
            if lastNormal!=None and almostEqual(normal, lastNormal):
                currentGroup[0].append(i1)
            else:
                if currentGroup!=None:
                    currentGroup[0].append(i1)
                    normalGroups.append(currentGroup)
                    currentGroup = ([i0, i1], normal)
                else:
                    currentGroup = ([i1], normal)
            lastNormal = normal
        if currentGroup!=None:
            normalGroups.append(currentGroup)
        
        # all vertex in plane
        if len(normalGroups)==1:
            return [self]
        
        # first and last group may get joined
        if almostEqual( normalGroups[0][1], normalGroups[-1][1] ):
            indexes = normalGroups[0][0] + normalGroups[-1][0]
            normalGroups = normalGroups[:-1]
            normalGroups[0] = (indexes, normalGroups[0][1])
        
        # groups must have at least three member,
        # this way we can remove groups of
        # vertices acting as bridge between planes.
        normalGroups = filter(lambda x: len(x)>2, normalGroups)
        
        # create VArrayFace instances for each group
        groupFaces = []
        for (indexes, _) in normalGroups:
            params = { 'i': indexes }
            uv = None; col = None; nor = None
            numIndexes = len(indexes)
            
            for i in range(len(indexes)):
                j = indexes[i]
                for k in self.indexes:
                    if k==j: break
                
                # set params
                if bool(self.uv):
                    if not bool(uv): uv = [None]*numIndexes
                    uv[i] = self.uv[j]
                if bool(self.col):
                    if not bool(col): col = [None]*numIndexes
                    col[i] = self.col[j]
                if bool(self.nor):
                    if not bool(nor): nor = [None]*numIndexes
                    nor[i] = self.nor[j]
            
            face = VArrayFace(params)
            groupFaces.append(face)
        
        return groupFaces
