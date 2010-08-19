from __future__ import division

import numpy as np
cimport numpy as np

DTYPE = np.float32
ctypedef np.float32_t DTYPE_t

cimport cython

#### cython only functions ####

@cython.profile(False)
@cython.boundscheck(False)
cdef inline np.ndarray[DTYPE_t, ndim=1] transformVec3(np.ndarray mat4x4,
                                                      np.ndarray v3):
    return np.dot( v3, mat4x4[:3,:3] ) + mat4x4[3,:3]

@cython.profile(False)
@cython.boundscheck(False)
cdef inline np.ndarray[DTYPE_t, ndim=1]\
crossVec3Float32Normalized(np.ndarray v, np.ndarray w):
    """ normalized cross product of 3-component vectors. """
    cdef np.ndarray[DTYPE_t, ndim=1] ret = np.zeros( 3, DTYPE )
    ret[0] = v[1]*w[2] - v[2]*w[1]
    ret[1] = v[2]*w[0] - v[0]*w[2]
    ret[2] = v[0]*w[1] - v[1]*w[0]
    ret /= np.linalg.norm( ret )
    return ret

cdef inline float maxFloat(float a, float b): return a if a >= b else b
cdef inline float minFloat(float a, float b): return a if a <= b else b

#### FRUSTUM STUFF ####

cdef class Frustum:
    cdef float nearPlaneWidth, nearPlaneHeight
    cdef float farPlaneWidth, farPlaneHeight
    cdef readonly float near, far, fov, aspect
    cdef readonly np.ndarray points
    
    def __cinit__(Frustum self):
        self.points = np.zeros( (8,3), DTYPE )
    
    @cython.profile(False)
    @cython.boundscheck(False)
    def setProjection(Frustum self,
                      float fov,
                      float aspect,
                      float near,
                      float far):
        self.near = near
        self.far = far
        self.fov = fov
        self.aspect = aspect
        
        # the 0.2 factor is important because we might get artifacts at
        # the screen borders.
        cdef float fovR = fov/57.2957795 + 0.2
        
        self.nearPlaneHeight = np.tan( fovR * 0.5) * near
        self.nearPlaneWidth  = self.nearPlaneHeight * aspect
        
        self.farPlaneHeight = np.tan( fovR * 0.5) * far
        self.farPlaneWidth  = self.farPlaneHeight * aspect

    @cython.profile(False)
    @cython.boundscheck(False)
    def calculatePoints (Frustum self,
                         np.ndarray[DTYPE_t, ndim=1] center,
                         np.ndarray[DTYPE_t, ndim=1] viewDir,
                         np.ndarray[DTYPE_t, ndim=1] up):
        cdef np.ndarray[DTYPE_t, ndim=1] right = crossVec3Float32Normalized( viewDir, up )
        cdef np.ndarray[DTYPE_t, ndim=1] fc = center + viewDir*self.far
        cdef np.ndarray[DTYPE_t, ndim=1] nc = center + viewDir*self.near
        cdef np.ndarray[DTYPE_t, ndim=1] rw, uh, u, buf1, buf2
        
        # up vector must be orthogonal to right/view
        u = crossVec3Float32Normalized( right, viewDir )
        
        rw = right*self.nearPlaneWidth
        uh = u*self.nearPlaneHeight
        buf1 = uh - rw
        buf2 = uh + rw
        self.points[0,] = nc - buf1
        self.points[1,] = nc + buf1
        self.points[2,] = nc + buf2
        self.points[3,] = nc - buf2
    
        rw = right*self.farPlaneWidth
        uh = u*self.farPlaneHeight
        buf1 = uh - rw
        buf2 = uh + rw
        self.points[4,] = fc - buf1
        self.points[5,] = fc + buf1
        self.points[6,] = fc + buf2
        self.points[7,] = fc - buf2


@cython.profile(False)
@cython.boundscheck(False)
def splitFrustum (Frustum frustum,
                  int nFrustas,
                  float splitWeight):
    cdef float fov = frustum.fov
    cdef float aspect = frustum.aspect
    cdef float nd = frustum.near
    cdef float fd = frustum.far
    cdef float ratio = fd/nd
    cdef float si, lastn, currf, currn
    cdef int i
    
    frustas = [Frustum()]
    
    lastn = nd
    for i in range(1,nFrustas):
        si = i / <float>nFrustas
        
        frustas.append(Frustum())
        currn = splitWeight*(nd*(ratio ** si)) + (1-splitWeight)*(nd + (fd - nd)*si)
        currf = currn * 1.005
        
        frustas[i-1].setProjection(fov, aspect, lastn, currf)
        
        lastn = currn
    frustas[nFrustas-1].setProjection(fov, aspect, lastn, fd)
    
    return frustas
    
