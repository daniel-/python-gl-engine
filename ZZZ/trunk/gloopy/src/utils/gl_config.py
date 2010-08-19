# -*- coding: UTF-8 -*-
'''
Created on 27.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.package_config import RELEASE_VERSION

def importGL():
    import OpenGL
    """
    if True, attempt to use the OpenGL_accelerate
    package to provide Cython-coded accelerators for core wrapping
    operations.
    Default: True
    """
    OpenGL.USE_ACCELERATE = True
    
    """
    if set to a False value before
    importing any OpenGL.* libraries will completely
    disable error-checking.  This can dramatically
    improve performance, but makes debugging far harder.
    
    This is intended to be turned off *only* in a
    production environment where you *know* that
    your code is entirely free of situations where you
    use exception-handling to handle error conditions,
    i.e. where you are explicitly checking for errors
    everywhere they can occur in your code.
    
    Default: True 
    """
    OpenGL.ERROR_CHECKING = not RELEASE_VERSION
    OpenGL.ARRAY_SIZE_CHECKING = not RELEASE_VERSION
    """
    if set to True, PyOpenGL will wrap
    *every* GL and GLU call with a check to see if there
    is a valid context.  If there is no valid context
    then will throw OpenGL.errors.NoContext.  This is an
    *extremely* slow check and is not enabled by default,
    intended to be enabled in order to track down (wrong)
    code that uses GL/GLU entry points before the context
    has been initialized (something later Linux GLs are
    very picky about).
    """
    OpenGL.CONTEXT_CHECKING = not RELEASE_VERSION
    """
    if set to a True value before
    importing the numpy/lists support modules, will
    cause array operations to raise
    OpenGL.error.CopyError if the operation
    would cause a data-copy in order to make the
    passed data-type match the target data-type.
    
    This effectively disables all list/tuple array
    support, as they are inherently copy-based.
    
    This feature allows for optimisation of your
    application.  It should only be enabled during
    testing stages to prevent raising errors on
    recoverable conditions at run-time. 
    
    Note: this feature does not currently work with numarray or Numeric arrays.
    Default: False
    """
    OpenGL.ERROR_ON_COPY = True
    
    """
    If True, then wrap array-handler
    functions with  error-logging operations so that all exceptions
    will be reported to log objects in OpenGL.logs, note that
    this means you will get lots of error logging whenever you
    have code that tests by trying something and catching an
    error, this is intended to be turned on only during
    development so that you can see why something is failing.
    
    Errors are normally logged to the OpenGL.errors logger.
    Only triggers if ERROR_CHECKING is True
    Default: False
    """
    OpenGL.ERROR_LOGGING = not RELEASE_VERSION
    """
    If True, then wrap functions with
    logging operations which reports each call along with its
    arguments to  the OpenGL.calltrace logger at the INFO
    level.  This is *extremely* slow.  You should *not* enable
    this in production code!
    
    You will need to have a  logging configuration (e.g. logging.basicConfig())
    call  in your top-level script to see the results of the
    logging.
    #Default: False
    """
    OpenGL.FULL_LOGGING = False
    """
    if True, we will wrap
    all GLint/GLfloat calls conversions with wrappers
    that allow for passing numpy scalar values.
    Note that this is experimental, *not* reliable, and very slow!
    Note that byte/char types are not wrapped.
    Default: False
    """
    OpenGL.ALLOW_NUMPY_SCALARS = False
    """
    only include OpenGL 3.1 compatible
    entry points.  Note that this will generally break most
    PyOpenGL code that hasn't been explicitly made "legacy free"
    via a significant rewrite.
    Default: False
    """
    OpenGL.FORWARD_COMPATIBLE_ONLY = not RELEASE_VERSION
    """
    if True, unpack size-1 arrays to be
    scalar values, as done in PyOpenGL 1.5 -> 3.0.0, that is,
    if a glGenList( 1 ) is done, return a uint rather than
    an array of uints.
    Default: True
    """
    OpenGL.SIZE_1_ARRAY_UNPACK = True
    """
    set to True, PyOpenGL array operations
    will attempt to store references to pointers which are
    being passed in order to prevent memory-access failures
    if the pointed-to-object goes out of scope.  This
    behaviour is primarily intended to allow temporary arrays
    to be created without causing memory errors, thus it is
    trading off performance for safety.

    To use this flag effectively, you will want to first set
    ERROR_ON_COPY to True and eliminate all cases where you
    are copying arrays.  Copied arrays *will* segfault your
    application deep within the GL if you disable this feature!
    
    Once you have eliminated all copying of arrays in your
    application, you will further need to be sure that all
    arrays which are passed to the GL are stored for at least
    the time period for which they are active in the GL.  That
    is, you must be sure that your array objects live at least
    until they are no longer bound in the GL.  This is something
    you need to confirm by thinking about your application's
    structure.
    
    When you are sure your arrays won't cause seg-faults, you
    can set STORE_POINTERS=False in your application and enjoy
    a (slight) speed up.

    Note: this flag is *only* observed when ERROR_ON_COPY == True,
        as a safety measure to prevent pointless segfaults

    Default: True
    """
    OpenGL.STORE_POINTERS = False
    """
    if True, we will return
    GL_UNSIGNED_BYTE image-data as strings, instead of arrays
    for glReadPixels and glGetTexImage
    Default: True
    """
    OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = True
    """
    If True, generates logging-module warn-level events when a FormatHandler
    plugin is not loadable (with traceback).
    Default: False
    """
    OpenGL.WARN_ON_FORMAT_UNAVAILABLE = not RELEASE_VERSION
    
    return OpenGL

OpenGL = importGL()
from OpenGL import GL as gl

def printGLInfo():
    print "********"
    print "GL_VERSION:                       ", gl.glGetString( gl.GL_VERSION )
    print "GL_RENDERER:                      ", gl.glGetString( gl.GL_RENDERER )
    print "GL_MAX_CLIP_PLANES:               ", gl.glGetInteger( gl.GL_MAX_CLIP_PLANES )
    print "GL_MAX_LIGHTS:                    ", gl.glGetInteger( gl.GL_MAX_LIGHTS )
    print "GL_MAX_TEXTURE_UNITS:             ", gl.glGetInteger( gl.GL_MAX_TEXTURE_UNITS )
    print "GL_MAX_TEXTURE_COORDS:            ", gl.glGetInteger( gl.GL_MAX_TEXTURE_COORDS )
    print "GL_MAX_TEXTURE_SIZE:              ", gl.glGetInteger( gl.GL_MAX_TEXTURE_SIZE )
    print "GL_MAX_DRAW_BUFFERS:              ", gl.glGetInteger( gl.GL_MAX_DRAW_BUFFERS )
    print "GL_MAX_LIST_NESTING:              ", gl.glGetInteger( gl.GL_MAX_LIST_NESTING )
    print "GL_MAX_ELEMENTS_VERTICES:         ", gl.glGetInteger( gl.GL_MAX_ELEMENTS_VERTICES )
    print "GL_MAX_ELEMENTS_INDICES:          ", gl.glGetInteger( gl.GL_MAX_ELEMENTS_INDICES )
    print "GL_MAX_VARYING_COMPONENTS:        ", gl.glGetInteger( gl.GL_MAX_VARYING_COMPONENTS )
    print "GL_MAX_VARYING_FLOATS:            ", gl.glGetInteger( gl.GL_MAX_VARYING_FLOATS )
    print "GL_MAX_VERTEX_ATTRIBS:            ", gl.glGetInteger( gl.GL_MAX_VERTEX_ATTRIBS )
    print "GL_MAX_VERTEX_UNIFORM_COMPONENTS: ", gl.glGetInteger( gl.GL_MAX_VERTEX_UNIFORM_COMPONENTS )
    print "********"
