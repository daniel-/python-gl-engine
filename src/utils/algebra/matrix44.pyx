from __future__ import division

import numpy as np
cimport numpy as np

from scipy.special import cotdg

DTYPE = np.float32
ctypedef np.float32_t DTYPE_t

cimport cython

#### cython only functions ####

@cython.profile(False)
@cython.boundscheck(False)
cdef inline np.ndarray[DTYPE_t, ndim=1] toVec4C(np.ndarray vec3):
    return np.array( [ vec3[0], vec3[1], vec3[2], 1.0 ], DTYPE )
#    cdef np.ndarray[DTYPE_t, ndim=1] ret = np.zeros( 4, DTYPE )
#    ret[:3] = vec3
#    return ret

@cython.profile(False)
@cython.boundscheck(False)
cdef inline np.ndarray[DTYPE_t, ndim=1]\
crossVec3Float32C(np.ndarray v, np.ndarray w):
    """ cross product of 3-component vectors. """
    cdef np.ndarray[DTYPE_t, ndim=1] ret = np.zeros( 3, DTYPE )
    ret[0] = v[1]*w[2] - v[2]*w[1]
    ret[1] = v[2]*w[0] - v[0]*w[2]
    ret[2] = v[0]*w[1] - v[1]*w[0]
    return ret

@cython.profile(False)
@cython.boundscheck(False)
cdef inline np.ndarray[DTYPE_t, ndim=1]\
crossVec3Float32NormalizedC(np.ndarray v, np.ndarray w):
    """ normalized cross product of 3-component vectors. """
    cdef np.ndarray[DTYPE_t, ndim=1] ret = np.zeros( 3, DTYPE )
    ret[0] = v[1]*w[2] - v[2]*w[1]
    ret[1] = v[2]*w[0] - v[0]*w[2]
    ret[2] = v[0]*w[1] - v[1]*w[0]
    ret /= np.linalg.norm( ret )
    return ret

@cython.profile(False)
@cython.boundscheck(False)
cdef inline np.ndarray[DTYPE_t, ndim=1] transformVec4C(\
                  np.ndarray mat4x4,
                  np.ndarray v4):
    return np.dot( v4, mat4x4 )
@cython.profile(False)
@cython.boundscheck(False)
cdef inline np.ndarray[DTYPE_t, ndim=1] transformVec3C(\
                  np.ndarray mat4x4,
                  np.ndarray v3):
    return np.dot( v3, mat4x4[:3,:3] ) + mat4x4[3,:3]

@cython.profile(False)
@cython.boundscheck(False)
cdef inline np.ndarray[DTYPE_t, ndim=2] getCropMatrixC(\
                               float minX,
                               float maxX,
                               float minY,
                               float maxY):
    """
    updates the crop matrix.
    this matrix translates and scales the projection so that
    it will captures the bounding box of the current frustum slice.
    @param minX: minimum x value in light space
    @param maxX: maximum x value in light space
    @param minY: minimum y value in light space
    @param maxY: maximum y value in light space
    """
    
    cdef float scaleX = 2.0 / (maxX - minX)
    cdef float scaleY = 2.0 / (maxY - minY)
    
    crop = np.identity( 4, DTYPE )
    crop[0,0] = scaleX
    crop[1,1] = scaleY
    crop[3,0] = -0.5 * (maxX + minX) * scaleX # offsetX
    crop[3,1] = -0.5 * (maxY + minY) * scaleY # offsetY
    
    return crop

@cython.profile(False)
@cython.boundscheck(False)
cdef inline np.ndarray[DTYPE_t, ndim=2] getOrthogonalProjectionMatrixC(
                                   float l,
                                   float r,
                                   float b,
                                   float t,
                                   float n,
                                   float f):
    """
    calculates same matrix as glOrtho()
    """
    cdef np.ndarray[DTYPE_t, ndim=2] ret = np.identity(4, DTYPE)
    
    ret[0,0] =  2.0 / (r-l)
    ret[1,1] =  2.0 / (t-b)
    ret[2,2] = -2.0 / (f-n)
    ret[3,0] = -(r+l)/(r-l)
    ret[3,1] = -(t+b)/(t-b)
    ret[3,2] = -(f+n)/(f-n)
    
    return ret

#### SOME DEFAULT MATRIX UTILITIES ####

@cython.profile(False)
@cython.boundscheck(False)
def getRow0(np.ndarray[DTYPE_t, ndim=2] mat4x4): return mat4x4[0,:3]
@cython.profile(False)
@cython.boundscheck(False)
def getRow1(np.ndarray[DTYPE_t, ndim=2] mat4x4): return mat4x4[1,:3]
@cython.profile(False)
@cython.boundscheck(False)
def getRow2(np.ndarray[DTYPE_t, ndim=2] mat4x4): return mat4x4[2,:3]
@cython.profile(False)
@cython.boundscheck(False)
def getRow3(np.ndarray[DTYPE_t, ndim=2] mat4x4): return mat4x4[3,:3]
# some other names
getXAxis     = getRow0
getRight     = getRow0
getYAxis     = getRow1
getUp        = getRow1
getZAxis     = getRow2
getForward   = getRow2
getTranslate = getRow3

@cython.profile(False)
@cython.boundscheck(False)
def setTranslation(np.ndarray[DTYPE_t, ndim=2] mat4x4,
                   np.ndarray[DTYPE_t, ndim=1] vec3):
    mat4x4[3,:3] = vec3
@cython.profile(False)
@cython.boundscheck(False)
def setForward(np.ndarray[DTYPE_t, ndim=2] mat4x4,
               np.ndarray[DTYPE_t, ndim=1] vec3):
    mat4x4[2,:3] = vec3
@cython.profile(False)
@cython.boundscheck(False)
def setUp(np.ndarray[DTYPE_t, ndim=2] mat4x4,
          np.ndarray[DTYPE_t, ndim=1] vec3):
    mat4x4[1,:3] = vec3
@cython.profile(False)
@cython.boundscheck(False)
def setRight(np.ndarray[DTYPE_t, ndim=2] mat4x4,
             np.ndarray[DTYPE_t, ndim=1] vec3):
    mat4x4[0,:3] = vec3

@cython.profile(False)
@cython.boundscheck(False)
def inverseCContiguous(np.ndarray[DTYPE_t, ndim=2] mat4x4):
    return np.ascontiguousarray( np.linalg.inv( mat4x4 ) )

# Note: we are using numpy row vectors,
#  therfore the vector needs to be on the left side
#  for matrix multiplication.
@cython.profile(False)
@cython.boundscheck(False)
def rotateVec3(np.ndarray[DTYPE_t, ndim=2] mat4x4,
               np.ndarray[DTYPE_t, ndim=1] v3):
    return np.dot( v3, mat4x4[:3,:3] )
@cython.profile(False)
@cython.boundscheck(False)
def transformVec3(np.ndarray[DTYPE_t, ndim=2] mat4x4,
                  np.ndarray[DTYPE_t, ndim=1] v3):
    return np.dot( v3, mat4x4[:3,:3] ) + mat4x4[3,:3]
@cython.profile(False)
@cython.boundscheck(False)
def transformVec4(np.ndarray[DTYPE_t, ndim=2] mat4x4,
                  np.ndarray[DTYPE_t, ndim=1] v4):
    return np.dot( v4, mat4x4 )

#### SPECIAL MATRIX CREATION ####

@cython.profile(False)
@cython.boundscheck(False)
def getOrthogonalProjectionMatrix(float l,
                                  float r,
                                  float b,
                                  float t,
                                  float n,
                                  float f):
    """
    calculates same matrix as glOrtho()
    """
    cdef np.ndarray[DTYPE_t, ndim=2] ret = np.identity(4, DTYPE)
    
    ret[0,0] =  2.0 / (r-l)
    ret[1,1] =  2.0 / (t-b)
    ret[2,2] = -2.0 / (f-n)
    ret[3,0] = -(r+l)/(r-l)
    ret[3,1] = -(t+b)/(t-b)
    ret[3,2] = -(f+n)/(f-n)
    
    return ret

@cython.profile(False)
@cython.boundscheck(False)
def getProjectionMatrix(float fov,
                        float aspect,
                        float near,
                        float far):
    """
    calculates same matrix as gluPerspective()
    """
    cdef np.ndarray[DTYPE_t, ndim=2] ret = np.identity(4, DTYPE)
    cdef float f = cotdg(fov/2)

    ret[0,0] = f/aspect
    ret[1,1] = f
    ret[2,2] = (far+near)/(near-far)
    ret[3,3] = 0.0
    ret[2,3] = -1.0
    ret[3,2] = 2.0*far*near/(near-far)

    return ret

@cython.profile(False)
@cython.boundscheck(False)
def getLookAtMatrix(np.ndarray[DTYPE_t, ndim=1] position,
                    np.ndarray[DTYPE_t, ndim=1] direction,
                    np.ndarray[DTYPE_t, ndim=1] up):
    """
    calculates same matrix as gluLookAt()
    @note: up vector must be normalized
    FIXME: this is slower then using glGet* and gluLookAt.
    """
    cdef np.ndarray[DTYPE_t, ndim=1] t = -position
    cdef np.ndarray[DTYPE_t, ndim=1] f = direction-position
    f /= np.linalg.norm( f ) # normalize
    cdef np.ndarray[DTYPE_t, ndim=1] s = crossVec3Float32NormalizedC( f, up )
    cdef np.ndarray[DTYPE_t, ndim=1] u = crossVec3Float32C( s, f )
    f *= -1.0;
    return np.array([
        [s[0],        u[0],        f[0],        0.0],
        [s[1],        u[1],        f[1],        0.0],
        [s[2],        u[2],        f[2],        0.0],
        [np.dot(s,t), np.dot(u,t), np.dot(f,t), 1.0]
    ], DTYPE)

@cython.profile(False)
@cython.boundscheck(False)
def translationMatrix(np.ndarray[DTYPE_t, ndim=1] translation):
    cdef np.ndarray[DTYPE_t, ndim=2] mat = np.identity( 4, DTYPE )
    mat[3,:3] = translation
    return mat

@cython.profile(False)
@cython.boundscheck(False)
def xyzRotationMatrix(float x,
                      float y,
                      float z):
    """
    creates a new rotation matrix that rotates x/y/z axes.
    """
    cdef np.ndarray[DTYPE_t, ndim=2] mat = np.identity( 4, DTYPE )
    cdef float cx = np.cos(x), sx = np.sin(x)
    cdef float cy = np.cos(y), sy = np.sin(y)
    cdef float cz = np.cos(z), sz = np.sin(z)
    cdef float sxsy = sx*sy        
    cdef float cxsy = cx*sy
    
    mat[0,0] = cy*cz
    mat[0,1] = sxsy*cz+cx*sz
    mat[0,2] = -cxsy*cz+sx*sz
    mat[1,0] = -cy*sz
    mat[1,1] = -sxsy*sz+cx*cz
    mat[1,2] = cxsy*sz+sx*cz
    mat[2,0] = sy
    mat[2,1] = -sx*cy
    mat[2,2] = cx*cy
    
    return mat

@cython.profile(False)
@cython.boundscheck(False)
def lookAtCameraInverse(np.ndarray[DTYPE_t, ndim=2] src):
    cdef np.ndarray[DTYPE_t, ndim=2] inv = np.identity(4, np.float32)
    
    inv[0,0] = src[0,0]
    inv[0,1] = src[1,0]
    inv[0,2] = src[2,0]
    inv[0,3] = 0.0
    inv[1,0] = src[0,1]
    inv[1,1] = src[1,1]
    inv[1,2]  = src[2,1]
    inv[1,3] = 0.0
    inv[2,0] = src[0,2]
    inv[2,1] = src[1,2]
    inv[2,2] = src[2,2]
    inv[2,3] = 0.0
    inv[3,0] = -(src[3,0] * src[0,0]) - (src[3,1] * src[0,1]) - (src[3,2] * src[0,2])
    inv[3,1] = -(src[3,0] * src[1,0]) - (src[3,1] * src[1,1]) - (src[3,2] * src[1,2])
    inv[3,2] = -(src[3,0] * src[2,0]) - (src[3,1] * src[2,1]) - (src[3,2] * src[2,2])
    inv[3,3] = 1.0
    
    return inv

@cython.profile(False)
@cython.boundscheck(False)
def getDirectionalShadowMapMatrices(np.ndarray[DTYPE_t, ndim=2] shadModelview,
                                    np.ndarray[DTYPE_t, ndim=2] frustumPoints,
                                    np.ndarray[DTYPE_t, ndim=2] sceneBoundPoints,
                                    float sceneBoundRadius):
    cdef np.ndarray[DTYPE_t, ndim=2] projectionCropMatrix 
    cdef np.ndarray[DTYPE_t, ndim=2] modelViewProjectionCropMatrix
    cdef np.ndarray[DTYPE_t, ndim=2] shadProj
    cdef np.ndarray[DTYPE_t, ndim=2] shadMvp
    cdef np.ndarray[DTYPE_t, ndim=1] transf
    cdef np.ndarray[DTYPE_t, ndim=1] v4 = np.ones( 4, DTYPE )
    cdef float maxX, minX, maxY, minY, maxZ, minZ, _maxZ, buf
    cdef int i
    
    maxX = maxY = -1000.0
    minX = minY =  1000.0
    
    # note that only the z-component is need and thus
    # the multiplication can be simplified
    buf = shadModelview[0,2] * frustumPoints[0][0] +\
          shadModelview[1,2] * frustumPoints[0][1] +\
          shadModelview[2,2] * frustumPoints[0][2] +\
          shadModelview[3,2]
    minZ = maxZ = buf
    for i in range(1, 8):
        buf = shadModelview[0,2] * frustumPoints[i][0] +\
              shadModelview[1,2] * frustumPoints[i][1] +\
              shadModelview[2,2] * frustumPoints[i][2] +\
              shadModelview[3,2]
        if buf > maxZ: maxZ = buf
        if buf < minZ: minZ = buf
    
    # make sure all relevant shadow casters are included
    for i in range(4):
        transf = transformVec4C(shadModelview, sceneBoundPoints[i])
        
        _maxZ = transf[2] + sceneBoundRadius
        if _maxZ > maxZ: maxZ = _maxZ
        #_minZ = transf[2] - radius
        #if _minZ < minZ: minZ = _minZ
    
    # get the projection matrix with the new z-bounds
    # note the inversion because the light looks at the neg. z axis
    # gluPerspective(LIGHT_FOV, 1.0, maxZ, minZ); // for point lights
    shadProj = getOrthogonalProjectionMatrixC(-1.0, 1.0, -1.0, 1.0, -maxZ, -minZ)
    # shadow model view projection matrix
    shadMvp = np.dot( shadModelview, shadProj )
    
    # find the extends of the frustum slice as projected in light's homogeneous coordinates
    for i in range(8):
        v4[:3] = frustumPoints[i]
        transf = transformVec4C(shadMvp, v4 )
        transf[0] /= transf[3]
        transf[1] /= transf[3]

        if transf[0] > maxX: maxX = transf[0]
        if transf[0] < minX: minX = transf[0]
        if transf[1] > maxY: maxY = transf[1]
        if transf[1] < minY: minY = transf[1]
    
    # calculate needed matrices
    projectionCropMatrix = np.dot( shadProj,
        getCropMatrixC(minX, maxX, minY, maxY) )
    modelViewProjectionCropMatrix = np.dot(
        shadModelview, projectionCropMatrix )
    
    return (projectionCropMatrix, modelViewProjectionCropMatrix)

