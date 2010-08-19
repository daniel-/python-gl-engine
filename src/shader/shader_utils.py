from ctypes import *
import sys

from pygame.locals import *
 
from utils.gl_config import importGL
OpenGL = importGL()

try:
    # For OpenGL-ctypes
    from OpenGL import platform
    gl = platform.OpenGL
except ImportError:
    try:
        # For PyOpenGL
        gl = cdll.LoadLibrary('libGL.so')
    except OSError:
        # Load for Mac
        from ctypes.util import find_library
        # finds the absolute path to the framework
        path = find_library('OpenGL')
        gl = cdll.LoadLibrary(path)
 
from OpenGL.GL import *

from utils.util import unique

"""
# TODO: include some more aspects of the fixed function pipeline
********* normal = normal * gl_NormalScale;
********* local viewer computation:
if (LocalViewer)
     eye = -normalize(ecPosition3);
else
     eye = vec3(0.0, 0.0, 1.0);
********* separate specular
if (SeparateSpecular)
     gl_FrontSecondaryColor = vec4(spec *
                                   gl_FrontMaterial.specular, 1.0);
else
     color += spec * gl_FrontMaterial.specular;
gl_FrontColor = color;
********* fog
if (UseFogCoordinate)
     gl_FogFragCoord = gl_FogCoord;
else
     gl_FogFragCoord = abs(ecPosition.z);
fog = (gl_Fog.end - gl_FogFragCoord)) * gl_Fog.scale; // GL_LINEAR
fog = exp(-gl_Fog.density * gl_FogFragCoord); // GL_EXP
fog = exp(-gl_Fog.density * gl_Fog.density *
           gl_FogFragCoord * gl_FogFragCoord); // GL_EXP2
fog = clamp(fog, 0.0, 1.0);
color = mix(vec3(gl_Fog.color), color, fog);
********* texture coord generation (GL_SPHERE_MAP, GL_REFLECTION_MAP, 
// Compute sphere map coordinates if needed
if (TexGenSphere)
    sphereMap = SphereMap(ecposition3, normal);
// Compute reflection map coordinates if needed
if (TexGenReflection)
    reflection = ReflectionMap(ecposition3, normal);
// Compute texture coordinate for each enabled texture unit
for (i = 0; i < NumEnabledTextureUnits; i++)
{
    if (TexGenObject)
    {
        gl_TexCoord[i].s = dot(gl_Vertex, gl_ObjectPlaneS[i]);
        gl_TexCoord[i].t = dot(gl_Vertex, gl_ObjectPlaneT[i]);
        gl_TexCoord[i].p = dot(gl_Vertex, gl_ObjectPlaneR[i]);
        gl_TexCoord[i].q = dot(gl_Vertex, gl_ObjectPlaneQ[i]);
    }
    if (TexGenEye)
    {
        gl_TexCoord[i].s  = dot(ecPosition, gl_EyePlaneS[i]);
        gl_TexCoord[i].t  = dot(ecPosition, gl_EyePlaneT[i]);
        gl_TexCoord[i].p  = dot(ecPosition, gl_EyePlaneR[i]);
        gl_TexCoord[i].q  = dot(ecPosition, gl_EyePlaneQ[i]);
    }
    if (TexGenSphere)
        gl_TexCoord[i] = vec4(sphereMap, 0.0, 1.0);
    if (TexGenReflection)
        gl_TexCoord[i] = vec4(reflection, 1.0);
    if (TexGenNormal)
        gl_TexCoord[i] = vec4(normal, 1.0);
}

"""


VERT_SHADER = 0
GEOM_SHADER = 1
FRAG_SHADER = 2


NORMAL_VARYING = "normalVarying"

def compileShader(source, shader_type):
    shader = glCreateShader(shader_type)
    source = c_char_p(source)
    length = c_int(-1)
    gl.glShaderSource(shader, 1, byref(source), byref(length))
    glCompileShader(shader)
    
    status = c_int()
    glGetShaderiv(shader, GL_COMPILE_STATUS, byref(status))
    if not status.value:
        glShaderLog(shader, shader_type, source)
        glDeleteShader(shader)
        raise ValueError, 'Shader compilation failed'
    return shader
 
def compileProgram(vertex_source, geometry_source, fragment_source):
    """ compiles shader sources and returns program handle """
    vertex_shader = None
    fragment_shader = None
    geometry_shader = None
    program = glCreateProgram()
    
    if vertex_source:
        vertex_shader = compileShader(vertex_source.code(), GL_VERTEX_SHADER)
        glAttachShader(program, vertex_shader)
    if geometry_source:
        geometry_shader = compileShader(geometry_source.code(), GL_GEOMETRY_SHADER)
        glAttachShader(program, geometry_shader)
    if fragment_source:
        fragment_shader = compileShader(fragment_source.code(), GL_FRAGMENT_SHADER)
        glAttachShader(program, fragment_shader)
 
    glLinkProgram(program)
 
    if geometry_shader:
        glDeleteShader(geometry_shader)
    if fragment_shader:
        glDeleteShader(fragment_shader)
    if fragment_shader:
        glDeleteShader(fragment_shader)
 
    return program


GL_GEOMETRY_INPUT_TYPE_EXT   = 0x8DDB
GL_GEOMETRY_OUTPUT_TYPE_EXT  = 0x8DDC
GL_GEOMETRY_VERTICES_OUT_EXT = 0x8DDA
def glProgramParameteri( program, pname, value  ):
    gl.glProgramParameteriARB( program, pname, value  )

 
def glShaderLog(shader, shaderType, shaderCode):
    length = c_int()
    glGetShaderiv(shader, GL_INFO_LOG_LENGTH, byref(length))
 
    if length.value > 0:
        _nameMapping = {
            GL_VERTEX_SHADER:   "Vertex",
            GL_GEOMETRY_SHADER: "Geometry",
            GL_FRAGMENT_SHADER: "Fragment"
        }
        
        codeLines = shaderCode.value.split("\n")
        code = ""
        for i in range(len(codeLines)):
            code += "%3d %s\n" % (i, codeLines[i])
        
        print >> sys.stderr, "%s Shader failed to compile!" % _nameMapping[shaderType]
        print >> sys.stderr, code
        print >> sys.stderr, glGetShaderInfoLog(shader)


class ShaderFunc(object):
    def __init__(self, name):
        self.name = name
        # user variables
        self.uniforms = []
        self.flexibleUniforms = {}
        # passes calculations from vertex to fragment shader
        self.varying = []
        # needed functions (tuple of name and code)
        self.deps = []
        # function parameters
        self.args = []
        # minimum gl version
        self.minVersion = 130
        
        self.enabledExtensions = []
        self.disabledExtensions = []
    
    def setMinVersion(self, version):
        self.minVersion = version
    
    def enableExtension(self, extensionName):
        if self.disabledExtensions.count(extensionName) != 0:
            print "WARNING: extension %s allready disabled." % extensionName
        self.enabledExtensions.append(extensionName)
    def disableExtension(self, extensionName):
        if self.enabledExtensions.count(extensionName) != 0:
            print "WARNING: extension %s allready enabled." % extensionName
        self.disabledExtensions.append(extensionName)
    
    def addUniform(self, type, name):
        """ adds a uniform var to the shader head """
        self.uniforms.append((type, name))
    
    def addConstant(self, type, name, val):
        """ adds a constant,
            constants can be easily used as uniforms self.constantToUniform() """
        self.flexibleUniforms[name] = (type, val)
    
    def constantToUniform(self, name):
        """ use a constant as uniform """
        (t, _) = self.flexibleUniforms[name]
        self.flexibleUniforms[name] = (t, None)
        
    
    def addDep(self, name, code):
        """ adds code as dependency for this function """
        self.deps.append((name, code))
    
    def addSuffix(self, expr):
        """ adds a expression to the end of main function """
        self.suffixes.append(expr)
    
    def addVarying(self, type, name):
        """ adds a varying variable """
        self.varying.append((type, name))
    
    def setArgs(self, args):
        """ set args used in function call """
        self.args = args
    
    def buildCall(self):
        """ build function call """
        if self.name==None:
            return ""
        if self.args==[] or self.args==None:
            return "%s()" % self.name
        args = self.args[0]
        for a in self.args[1:]:
            args += ", " + a
        return "%s( %s )" % (self.name, args)
    
    def code(self):
        """ returns glsl code as function. """
        raise NotImplementedError, "shader functions must implement self.code()!"

class VertShaderFunc(ShaderFunc):
    def __init__(self, name):
        ShaderFunc.__init__(self, name)
        # attributes are vertex shader only
        self.attributes = []
        self.addVarying(type="vec3", name=NORMAL_VARYING)
    
    def addAttribute(self, type, name):
        self.attributes.append((type, name))


class FragShaderFunc(ShaderFunc):
    def __init__(self, name):
        ShaderFunc.__init__(self, name)
        self.addVarying(type="vec3", name=NORMAL_VARYING)

class GeomShaderFunc(ShaderFunc):
    def __init__(self, name):
        ShaderFunc.__init__(self, name)
    


class MyShader(object):
    def __init__(self, funcs):
        funcNames = {}
        
        self.deps = []
        self.funcs = funcs
        self.suffixes = []
        self.localVars = []
        self.varyings = []
        self.uniforms = []
        self.exports = []
        self.constants = []
        self.enabledExtensions = []
        self.disabledExtensions = []
        self.minVersion = None
        
        for func in funcs:
            if func.name in funcNames:
                print "WARNING: shader function '%s' added multiple times!" % func.name
                continue
            funcNames[func.name] = 1
            
            self.enabledExtensions  += func.enabledExtensions
            self.disabledExtensions += func.disabledExtensions
            
            if self.minVersion==None and func.minVersion!=None:
                self.minVersion = int(func.minVersion)
            elif func.minVersion!=None and int(func.minVersion)>self.minVersion:
                self.minVersion = int(func.minVersion)
            
            self.deps = self.deps + func.deps
            self.varyings = self.varyings + func.varying
            self.uniforms = self.uniforms + func.uniforms
            for fUniName in func.flexibleUniforms.keys():
                (fUniType, fUniVal) = func.flexibleUniforms[fUniName]
                if fUniVal==None:
                    self.uniforms.append((fUniType, fUniName))
                else:
                    self.constants.append((fUniType, fUniName, fUniVal))
        
        self.suffixes = unique(self.suffixes)
        self.enabledExtensions = unique(self.enabledExtensions)
        self.disabledExtensions = unique(self.disabledExtensions)
        self.deps = unique(self.deps, lambda x: x[0])
        self.varyings = unique(self.varyings, lambda x: x[0]+x[1])
        self.uniforms = unique(self.uniforms, lambda x: x[0]+x[1])
        self.localVars = unique(self.localVars, lambda x: str(x[0])+str(x[1])+str(x[2]))
        self.constants = unique(self.constants, lambda x: str(x[0])+str(x[1])+str(x[2]))
    
    def __str__(self):
        shaderStr = ""
        
        for i in range(len(self.funcs)):
            shaderStr += str(self.funcs[i].name)
        
        varyings = map(lambda v: str(v[1]), self.varyings)
        varyings.sort()
        for i in range(len(varyings)):
            shaderStr += "_v:%s" % str(varyings[i])
        
        uniforms = map(lambda v: str(v[1]), self.uniforms)
        uniforms.sort()
        for i in range(len(uniforms)):
            shaderStr += "_u:%s" % str(uniforms[i])
        
        constants = map(lambda v: str(v[1])+"="+str(v[2]), self.constants)
        constants.sort()
        for i in range(len(constants)):
            shaderStr += "_c:%s" % constants[i]
        
        localVars = map(lambda v: str(v[1])+"="+str(v[2]), self.localVars)
        localVars.sort()
        for i in range(len(localVars)):
            shaderStr += "_l:%s" % localVars[i]
        
        exports = map(lambda v: str(v[0])+"="+str(v[1]), self.exports)
        exports.sort()
        for i in range(len(exports)):
            shaderStr += "_e:%s" % exports[i]
        
        return shaderStr
    
    def addLocalVar(self, type, name, val=None):
        """ adds a local var to the main function """
        self.localVars.append((type, name, val))
    
    def addExport(self, exp, val):
        self.exports.append((exp, val))
    
    def headerCode(self):
        code = ""
        if self.minVersion != None:
            code += "    #version %d\n" % self.minVersion
        for ext in self.enabledExtensions:
            code += "    #extension %s : enable\n" % ext
        for ext in self.disabledExtensions:
            code += "    #extension %s : disable\n" % ext
        code += "\n"
        
        for uni in self.uniforms:
            code += "    uniform %s %s;\n" % (uni[0], uni[1])
        
        for const in self.constants:
            code += "    const %s %s = %s;\n" % (const[0], const[1], str(const[2]))
        return code
    
    def depCode(self):
        code = ""
        for dep in self.deps:
            code += dep[1]
        return code
    
    def funcCode(self):
        code = ""
        for func in self.funcs:
            if func.name!=None:
                code += func.code()
        return code
    
    def mainHead(self):
        code = ""
        for (type, name, val) in self.localVars:
            if val==None:
                code += "        %s %s;\n" % (type, name)
            else:
                code += "        %s %s = %s;\n" % (type, name, val)
        return code
    
    def mainBody(self):
        code = ""
        for func in self.funcs:
            code += "        %s;\n" % (func.buildCall())
        return code
    
    def mainFoot(self):
        code = ""
        for (exp,val) in self.exports:
            code += "        %s = %s;\n" % (exp, val)
        for exp in self.suffixes:
            code += "        %s;\n" % exp
        return code
    
    def mainCode(self):
        return """
    void main()
    {
%s
%s
%s
    }
""" % (self.mainHead(), self.mainBody(), self.mainFoot())
    def code(self):
        return """
%s
%s
%s
%s
""" % (self.headerCode(), # varyings/uniforms/attributes/...
       self.depCode(),    # dependencies of functions
       self.funcCode(),   # shader functions
       self.mainCode())   # the main functions

class MyVertexShader(MyShader):
    def __init__(self, funcs):
        MyShader.__init__(self, funcs)
        
        self.attributes = []
        for func in funcs:
            self.attributes += func.attributes
        self.attributes = unique(self.attributes, lambda x: x[0]+x[1])
    
    def headerCode(self):
        code = MyShader.headerCode(self)
        for var in self.varyings:
            code += "    out %s %s;\n" % (var[0], var[1])
        for att in self.attributes:
            code += "    attribute %s %s;\n" % (att[0], att[1])
        return code
    
    def __str__(self):
        # prepend V ->  vertexshader
        shaderStr = "V:" + MyShader.__str__(self)
        # add vertex attributes
        attributes = map(lambda v: str(v[1]), self.attributes)
        attributes.sort()
        for i in range(len(self.attributes)):
            shaderStr += "_a:%s" % attributes[i]
        return shaderStr

class MyFragmentShader(MyShader):
    def __init__(self, funcs):
        MyShader.__init__(self, funcs)
    
    def headerCode(self):
        code = MyShader.headerCode(self)
        for var in self.varyings:
            code += "    in %s %s;\n" % (var[0], var[1])
        return code
    
    def __str__(self):
        return "F:" + MyShader.__str__(self)

class MyGeometryShader(MyShader):
    def __init__(self, funcs):
        MyShader.__init__(self, funcs)
    
    def __str__(self):
        return "G:" + MyShader.__str__(self)


class ShaderWrapper(object):
    def __init__(self, glHandle=None):
        self.glHandle = glHandle
    def __del__(self):
        if self.glHandle!=None:
            glDeleteProgram(self.glHandle)
    def setGLHandle(self, glHandle):
        self.glHandle = glHandle
    def enable(self):
        pass
    def disable(self):
        pass

class DepthShaderVert(object):
    @staticmethod
    def code():
        return """ attribute vec3 vertexPosition;
                   void main() {
                      gl_Position = gl_ModelViewProjectionMatrix * vec4(vertexPosition, 1.0);
                   } """
class DepthShaderFrag(object):
    @staticmethod
    def code():
        return """
    //uniform vec2 scale_offset;
    const vec2 scale_offset = vec2(1.0, 0.0);
    void main() {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    
        // Optimize depth precision.
        // Scale and offset depth values so that on-camera values map to {0, 1}.
        // This makes shadowers that are off camera have negative values, which
        // must be clamped to 0.0 so that they don't get clipped.
       gl_FragDepth = max(0.0f, (gl_FragCoord.z * scale_offset.x) + scale_offset.y);
    } """
class DepthShader(object):
    def __init__(self):
        self.program = compileProgram(DepthShaderVert, None, DepthShaderFrag)
    def enable(self):
        glUseProgram(self.program)
    def disable(self):
        glUseProgram(0)

def combineShader(vertShaderFuncs, geomShaderFuncs, fragShaderFuncs):
    if vertShaderFuncs==None or len(vertShaderFuncs)==0:
        vertShader = MyVertexShader([])
    else:
        vertShader = MyVertexShader(vertShaderFuncs)
    if geomShaderFuncs==None or len(geomShaderFuncs)==0:
        geomShader = None
    else:
        geomShader = MyGeometryShader(geomShaderFuncs)
    if fragShaderFuncs==None or len(fragShaderFuncs)==0:
        fragShader = MyFragmentShader([])
    else:
        fragShader = MyFragmentShader(fragShaderFuncs)
    return (vertShader, geomShader, fragShader)

class ShaderData(object):
    def __init__(self):
        self.localVars = {}
        self.exports = {}
        self.functions = []
