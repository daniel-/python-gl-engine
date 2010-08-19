from __future__ import division

import numpy as np
cimport numpy as np

DTYPE = np.float32
ctypedef np.float32_t DTYPE_t

cimport cython

identity4 = np.zeros( 4 )
identity3 = np.zeros( 3 )
identity2 = np.zeros( 2 )
identity1 = np.zeros( 1 )

@cython.profile(False)
@cython.boundscheck(False)
def almostEqual(np.ndarray[DTYPE_t, ndim=1] v,
                np.ndarray[DTYPE_t, ndim=1] w,
                float delta=1e-6):
    if v==None:   return w==None
    elif w==None: return False
    return np.allclose(v, w, delta)

@cython.profile(False)
@cython.boundscheck(False)
def normalize(np.ndarray[DTYPE_t, ndim=1] vec):
    vec /= np.linalg.norm( vec )
@cython.profile(False)
@cython.boundscheck(False)
def normalizeCopy(np.ndarray[DTYPE_t, ndim=1] vec):
    return vec / np.linalg.norm( vec )

@cython.profile(False)
@cython.boundscheck(False)
def scalar(np.ndarray[DTYPE_t, ndim=1] vec, float scalar):
    vec *= scalar
@cython.profile(False)
@cython.boundscheck(False)
def scalarCopy(np.ndarray[DTYPE_t, ndim=1] vec, float scalar):
    return vec * scalar

@cython.profile(False)
@cython.boundscheck(False)
def toVec4(np.ndarray[DTYPE_t, ndim=1] vec3):
    return np.array( [ vec3[0], vec3[1], vec3[2], 1.0 ], DTYPE )


@cython.profile(False)
@cython.boundscheck(False)
def crossVec2(np.ndarray[DTYPE_t, ndim=1] v,
              np.ndarray[DTYPE_t, ndim=1] w):
    cdef float x =  v[1]*w[2]
    cdef float y = -v[0]*w[2]
    cdef float z =  v[0]*w[1] - v[1]*w[0]
    return np.array( [x,y,z], DTYPE )

@cython.profile(False)
@cython.boundscheck(False)
def crossVec3Float32(np.ndarray[DTYPE_t, ndim=1] v,
                     np.ndarray[DTYPE_t, ndim=1] w):
    """ cross product of 3-component vectors. """
    cdef np.ndarray[DTYPE_t, ndim=1] ret = np.zeros( 3, DTYPE )
    ret[0] = v[1]*w[2] - v[2]*w[1]
    ret[1] = v[2]*w[0] - v[0]*w[2]
    ret[2] = v[0]*w[1] - v[1]*w[0]
    return ret

@cython.profile(False)
@cython.boundscheck(False)
def crossVec3Float32Normalized(np.ndarray[DTYPE_t, ndim=1] v,
                                  np.ndarray[DTYPE_t, ndim=1] w):
    """ normalized cross product of 3-component vectors. """
    cdef np.ndarray[DTYPE_t, ndim=1] ret = np.zeros( 3, DTYPE )
    ret[0] = v[1]*w[2] - v[2]*w[1]
    ret[1] = v[2]*w[0] - v[0]*w[2]
    ret[2] = v[0]*w[1] - v[1]*w[0]
    ret /= np.linalg.norm( ret )
    return ret


@cython.profile(False)
@cython.boundscheck(False)
def rotateView(np.ndarray[DTYPE_t, ndim=1] view,
               float angle,
               float x,
               float y,
               float z):
    cdef float c = np.cos(angle)
    cdef float s = np.sin(angle)
    cdef float newX, newY, newZ
    
    newX  = (x*x*(1-c) + c)   * view[0]
    newX += (x*y*(1-c) - z*s) * view[1]
    newX += (x*z*(1-c) + y*s) * view[2]
    
    newY  = (y*x*(1-c) + z*s) * view[0]
    newY += (y*y*(1-c) + c)   * view[1]
    newY += (y*z*(1-c) - x*s) * view[2]
    
    newZ  = (x*z*(1-c) - y*s) * view[0]
    newZ += (y*z*(1-c) + x*s) * view[1]
    newZ += (z*z*(1-c) + c)   * view[2]
    
    view[0] = newX
    view[1] = newY
    view[2] = newZ
    view /= np.linalg.norm( view )

