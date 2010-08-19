# -*- coding: UTF-8 -*-
'''
Created on 18.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

"""
this module implements a plane polygonal segment.
for tangent and normal generating its relevant
if the faces of a segment are plane.
"""


from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl

from numpy import array, vdot
from utils.algebra.vector import scalarCopy

from core.gl_vertex_attribute import GLVertexAttribute

def tangentAttribute(tangents):
    return GLVertexAttribute(name="vertexTangent",
                            data=tangents,
                            elementSize=4*4,      # 4 (x/y/z/w) times 4 byte (sizeof float)
                            normalize=False,
                            dataType=gl.GL_FLOAT)


def generateFaceTangent(segment, face):
    """
    generates tangent and binormal based on
    uv coordinates and vertex positions.
    the face is expected to be in plane.
    only the first three coordinates are used.
    """
    v = map(lambda i: segment.vertices.data[i], face.indexes)
    uv = face.uv
    
    # TODO: problem for faces with more then 3 vertices?
    edge1 = v[ 1] - v[0]
    edge2 = v[-1] - v[0]
    texEdge1 = uv[ 1] - uv[0]
    texEdge2 = uv[-1] - uv[0]
    
    det = texEdge1[0] * texEdge2[1] - texEdge2[0] * texEdge1[1]
    if abs(det) < 0.00001:
        tangent  = array((1.0, 0.0, 0.0))
        binormal = array((0.0, 1.0, 0.0))
    else:
        det = 1.0 / det
        tangent = array((
            (texEdge2[1] * edge1[0] - texEdge1[1] * edge2[0]) * det,
            (texEdge2[1] * edge1[1] - texEdge1[1] * edge2[1]) * det,
            (texEdge2[1] * edge1[2] - texEdge1[1] * edge2[2]) * det
        ))
        binormal = array((
            (-texEdge2[0] * edge1[0] + texEdge1[0] * edge2[0]) * det,
            (-texEdge2[0] * edge1[1] + texEdge1[0] * edge2[1]) * det,
            (-texEdge2[0] * edge1[2] + texEdge1[0] * edge2[2]) * det
        ))
        
    return (tangent, binormal)

def genVertexTangentsPlane(segment):
    """
    generates per vertex tangents for vertices used by given faces.
    all faces must be plane.
    @param segment: must be a vertex array segment,
    @see: http://www.terathon.com/code/tangent.html
    @precondition: self.normals calculated
    @precondition: self.faces set and uv coordinates set on each face
    """
    
    tangents = [None]*segment.numVertices
    vtb = {}
    
    # Calculate the triangle face tangent and binormal.
    for face in segment.faces:
        (t,b) = generateFaceTangent(segment, face)
        # Accumulate the tangents and binormals.
        for i in face.indexes:
            try:
                vtb[i].append((t,b))
            except:
                vtb[i] = [(t,b)]
    
    # Orthogonalize and normalize the vertex tangents.
    for i in vtb.keys():
        tbs = vtb[i]
        ts, bs = zip(*tbs)
        
        # sum tangents and binormals
        tangent  = reduce( lambda x, y: x+y, ts )
        binormal = reduce( lambda x, y: x+y, bs )
        normal   = segment.normals.data[i]
        
        # Gram-Schmidt orthogonalize tangent with normal.
        nDotT = vdot( normal, tangent )
        tangent -= scalarCopy( normal, nDotT )
        tangent.normalize()
        
        """
        // Calculate the handedness of the local tangent space.
        // The bitangent vector is the cross product between the triangle face
        // normal vector and the calculated tangent vector. The resulting
        // bitangent vector should be the same as the bitangent vector
        // calculated from the set of linear equations above. If they point in
        // different directions then we need to invert the cross product
        // calculated bitangent vector. We store this scalar multiplier in the
        // tangent vector's 'w' component so that the correct bitangent vector
        // can be generated in the normal mapping shader's vertex shader.
        //
        // Normal maps have a left handed coordinate system with the origin
        // located at the top left of the normal map texture. The x coordinates
        // run horizontally from left to right. The y coordinates run
        // vertically from top to bottom. The z coordinates run out of the
        // normal map texture towards the viewer. Our handedness calculations
        // must take this fact into account as well so that the normal mapping
        // shader's vertex shader will generate the correct bitangent vectors.
        // Some normal map authoring tools such as Crazybump
        // (http://www.crazybump.com/) includes options to allow you to control
        // the orientation of the normal map normal's y-axis.
        """
        
        bDotB = normal.cross( tangent ).dot( binormal )
        if bDotB < 0.0:
            tangents[i] = array((tangent[0], tangent[1], tangent[2], 1.0))
        else:
            tangents[i] = array((tangent[0], tangent[1], tangent[2], -1.0))
    
    return tangentAttribute(tangents)


def genVertexTangentsUnplane(segment):
    # FIXME: TSPACE: each face could have multiple planes!
    # FIXME: TSPACE: face groups! will have problems with per face attributes
    return genVertexTangentsPlane(segment)
