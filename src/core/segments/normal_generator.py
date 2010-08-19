# -*- coding: UTF-8 -*-
'''
Created on 18.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''
from numpy import zeros, float32
from utils.algebra.vector import crossVec3Float32, normalize

def _genPlaneFaceNormals(segment, face, normals):
    v = map(lambda i: segment.vertices.data[i], face.indexes)
    
    # Calculate plane face normal
    # v[0] and left neighbor v[-1] and right neighbor v[1] are used.
    edge1 = v[ 1] - v[0]
    edge2 = v[-1] - v[0]
    normal = crossVec3Float32( edge1, edge2 )

    # Accumulate the normals.
    for i in face.indexes:
        normals[i] = normals[i]+normal

def genVertexNormalsPlane(segment):
    """
    generate per vertex normals.
    segment must consist of plane polygon faces.
    """
    normals = [ zeros( 3, float32 ) ]*segment.numVertices
    
    # Calculate the vertex normals.
    for face in segment.faces:
        _genPlaneFaceNormals(segment, face, normals)

    # Normalize the vertex normals.
    for i in range(segment.numVertices):
        normalize( normals[i] )
    
    return normals


def genVertexNormalsUnplane(segment):
    """
    generate normals for not plane faces.
    """
    normals = [ zeros(3,float32) ]*segment.numVertices
    
    # Calculate the vertex normals.
    for face in segment.faces:
        planeFaces = face.getPlaneFaces(segment)
        for face in planeFaces:
            _genPlaneFaceNormals(segment, face, normals)
    
    # Normalize the vertex normals.
    for i in range(segment.numVertices):
        normalize( normals[i] )
    
    return normals
