# -*- coding: UTF-8 -*-
'''
Created on 01.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL.GL import GL_TEXTURE_2D, GL_TEXTURE_2D_ARRAY

from shader.shader_utils import combineShader,\
                                compileProgram,\
                                ShaderWrapper, \
                                NORMAL_VARYING, VertShaderFunc, ShaderData,\
    FRAG_SHADER, VERT_SHADER, GEOM_SHADER

from shader.blending_shader import Brightness,\
                                   Invert,\
                                   Contrast,\
                                   BLEND_SHADER

from core.textures.texture import Texture2D
from core.segments.segment_shader import SegmentShader
from core.gl_object import GLObject
from core.reflections.planar_reflections import createPlaneReflectionHandler
from core.light.pixel_light import PixelLightFrag,PixelLightVert
from core.light.normal_mapping import BumpMapFrag


class ModelSegment(GLObject):
    """
    baseclass for model segments.
    segments have a shader associated to them
    and support generating some shader functions by looking at attributes
    on creation (self.create()).
    
    segments can be moved and rotated relative to the model.
    they can have a material associated to it,
    and a set of lights.
    """
    
    segmentShaders = {}
    
    def __init__(self, name, params):
        GLObject.__init__(self, params)
        
        # segment name
        self.segmentID = name
        
        self.shaderProgram = -1
        self.shader = None
        
        # texture for base coloring
        self.baseImage = None
        
        # segments needs material
        self.material = params.get('material')
        
        # get some default attributes
        self.isPlanar = self.getAttr("isPlane", False)
        if self.isPlanar:
            self.createReflectionHandler = createPlaneReflectionHandler
        else:
            pass
        self.reflectionHandler = None
        
        self.vertexPositionName = "vec4(vertexPosition, 1.0)"
        self.vertexNormalName = "vertexNormal"
        self.vertexColorName = "vertexColor"
        self.vertexUVName = "vertexUV"
    
    def create(self, app, lights):
        """
        call after configuration.
        currently only once callable because some vertex data
        calculations cannot get undone (face groups).
        """
        self.app = app
        self.enabledLights = range(len(lights))
        self.lights = lights
        
        self.hidden = False
        
        GLObject.create(self, app, lights)
        
        # material needs to get gl resources for textures
        if self.material != None:
            self.material.createGuard(app, lights)
        
        # splits up creation
        self.createResources()
        self.createResourcesPost()
        self.createShader()
        self.createDrawFunction()
        self.postCreate()
    
    def createResources(self):
        """
        create gl resources and vertex data.
        """
        pass
    def createResourcesPost(self):
        """
        do calculations depending on gl resources or complete vertex data.
        """
        pass
    
    def createBaseShaders(self, textures):
        """
        creates some basic shaders.
        the function is supposed to create a shader that
        will set the initial color and export some default stuff.
        """
        data = [ShaderData(), ShaderData(), ShaderData()]
        if self.baseImage != None:
            # add the base texture to the list
            texUnit = self.nextTexID; self.nextTexID += 1
            textures.append((self.baseImage.glID,
                             GL_TEXTURE_2D,
                             "sampler2D",
                             "BaseImage", texUnit))
            # we load the base image texel into base color var
            data[FRAG_SHADER].localVars["col"] = ("vec4", "texture2D( BaseImage, gl_TexCoord[0].xy )")
            # need uv coordinate
            data[VERT_SHADER].exports["gl_TexCoord[0].xy"] = self.vertexUVName
        else:
            # export per vertex color
            if self.hasCol():
                data[VERT_SHADER].exports["gl_FrontColor"] = self.vertexColorName
            else:
                data[VERT_SHADER].exports["gl_FrontColor"] = "gl_Color"
            
            # adds a local color var 'col'
            data[FRAG_SHADER].localVars["col"] = ("vec4", "gl_Color")
        
        # let gl_FragData[0] = col
        data[FRAG_SHADER].exports["gl_FragData[0]"] = "col"
        #data[FRAG_SHADER].exports["gl_FragData[0]"] = "vec4(0.0, 0.0, 0.0, 1.0)"
        
        # export default vertex position
        data[VERT_SHADER].exports["gl_Position"] =\
            "gl_ModelViewProjectionMatrix * %s" % self.vertexPositionName
        # export vertex position in eye space, will be interpolated for fragment shader
        data[VERT_SHADER].localVars["v"] = ("vec4",
            " gl_ModelViewMatrix * %s " % self.vertexPositionName)
        # clipping works only with this export.
        # TODO: only if need clipping
        data[VERT_SHADER].exports["gl_ClipVertex"] = "v"
        
        return data
    
    def createLightShaders(self, textures, matTextures):
        """
        creates shader that does the lighting calculations.
        lighting calculations are done last in the fragment shader
        and first in the vertex shader.
        """
        data = [ShaderData(), ShaderData(), ShaderData()]
        
        # create light shaders
        pLightVert = PixelLightVert(self.app, lights=self.lights)
        pLightVert.setArgs(["v"])
        data[VERT_SHADER].functions.append(pLightVert)
        
        plightFrag = PixelLightFrag(self.app, lights=self.lights)
        plightFrag.setArgs(["col", "n", "col"])
        data[FRAG_SHADER].functions.append(plightFrag)
        
        # light shader requires interpolated normal
        data[VERT_SHADER].exports[NORMAL_VARYING] = "normalize( gl_NormalMatrix * %s )" % self.vertexNormalName
        data[FRAG_SHADER].localVars["n"] = ("vec3", "normalize( %s )" % NORMAL_VARYING)
        
        return data
    
    def createNorShaders(self, textures, matTextures):
        """
        create normal mapping aka bump mapping shader.
        """
        data = [ShaderData(), ShaderData(), ShaderData()]
        
        norTexData = matTextures.get(Texture2D.MAP_TO_NOR, [])
        for (tex, texData) in norTexData:
            tex, _, _, i = texData
            if tex.tangentSpace: continue
            
            # create eye space normal mapping shader,
            # tangent space cannot be calculated by all segments.
            bumpFrag = BumpMapFrag(enabledLights=self.enabledLights)
            bumpFrag.setArgs(["texel%d" % i, "uv", "n"])
            data[FRAG_SHADER].functions.append(bumpFrag)
        
        return data
    
    def createColorShaders(self, textures, matTextures):
        """
        color shader are supposed to do color manipulation
        in the fragment shader (blending)
        """
        data = [ShaderData(), ShaderData(), ShaderData()]
        
        colTexData = matTextures.get(Texture2D.MAP_TO_COL, [])
        # iterate over textures mapped to color
        for (tex, texData) in colTexData:
            _, _, _, _, i = texData
            
            # blend texel with existing color
            shader = BLEND_SHADER[tex.blendMode]()
            shader.setArgs(["texel%d" % i, "col"])
            shader.addConstant(type="float", name=shader.facVar, val=tex.colfac)
            
            data[FRAG_SHADER].functions.append(shader)
            data[FRAG_SHADER].localVars["texel%d" % i] = \
                ("vec4", "texture2D( Texture%d, gl_TexCoord[0].xy )" % i)
            # need uv coordinate
            data[VERT_SHADER].exports["gl_TexCoord[0].xy"] = self.vertexUVName
            
            if tex.brightness!=1.0:
                shader = Brightness()
                shader.setArgs(["col"])
                shader.addConstant(type="float", name=shader.facVar, val=tex.brightness)
                data[FRAG_SHADER].functions.append(shader)
            if tex.contrast!=1.0:
                shader = Contrast()
                shader.setArgs(["col"])
                shader.addConstant(type="float", name=shader.facVar, val=tex.contrast)
                data[FRAG_SHADER].functions.append(shader)
            if tex.neg:
                shader = Invert()
                shader.setArgs(["col"])
                data[FRAG_SHADER].functions.append(shader)
        
        return data
    
    def createUVShaders(self, textures, matTextures):
        # FIXME: fragment shader should load texels after uv transformation!
        return [ShaderData(), ShaderData(), ShaderData()]
    
    def createVertexShaders(self, textures, matTextures):
        return [ShaderData(), ShaderData(), ShaderData()]
    
    def _addShaders(self, shaderData, shaderDataRet):
        for k in shaderData.exports.keys():
            shaderDataRet.exports[k] = shaderData.exports[k]
        for k in shaderData.localVars.keys():
            shaderDataRet.localVars[k] = shaderData.localVars[k]
        for f in shaderData.functions:
            shaderDataRet.functions.append(f)
    
    def createShader(self):
        """
        creates shader for this segment.
        first the combination of used shaders is generated.
        this result has a string representation.
        if a shader with the same string representation was generated before,
        then the allready compiled shader is used, else a new one created.
        """
        
        vertData = ShaderData(); geomData = ShaderData(); fragData = ShaderData()
        
        # texture counter
        self.nextTexID = self.app.textureCounter
        # texture list
        textures = []
        # material texture colors maybe mapped to multiple targets,
        # we dont wanna iterate over the material textures in the create function,
        # so the relation will be saved in this table.
        matTextures = {}
        
        baseShaders = self.createBaseShaders(textures)
        
        # add material textures
        for i in range(len(self.material.textures)):
            tex = self.material.textures[i]
            texUnit = self.nextTexID; self.nextTexID += 1
            texData = (tex.glID, GL_TEXTURE_2D, "sampler2D", "Texture%d" % texUnit, texUnit)
            textures.append(texData)
            
            for mapTo in tex.mapTo:
                try:
                    matTextures[mapTo].append((tex, texData))
                except:
                    matTextures[mapTo] = [(tex, texData)]
        # add shadow map textures
        i = 0
        for light in self.lights:
            shadowMapArray = light.shadowMapArray
            if shadowMapArray!=None:
                texUnit = self.nextTexID; self.nextTexID += 1
                texData = (shadowMapArray.texture.glID,
                           GL_TEXTURE_2D_ARRAY,
                           shadowMapArray.textureType,
                           "shadowMap%d" % i,
                           texUnit)
                
                textures.append(texData)
                i += 1
        
        hasLight = bool(self.enabledLights)
        if hasLight:
            # uv and light shaders make only sense when light is enabled
            lightShaders = self.createLightShaders(textures, matTextures)
            norShaders = self.createNorShaders(textures, matTextures)
        uvShaders = self.createUVShaders(textures, matTextures)
        vertexShaders = self.createVertexShaders(textures, matTextures)
        colorShaders = self.createColorShaders(textures, matTextures)
        
        if self.isReflecting():
            self.reflectionHandler = self.createReflectionHandler(self.app, self,
                                                                  colorShaders, textures)
        
        # get multiple vertex shader functions
        self._addShaders(baseShaders[VERT_SHADER], vertData)
        self._addShaders(vertexShaders[VERT_SHADER], vertData)
        if hasLight:
            self._addShaders(lightShaders[VERT_SHADER], vertData)
            self._addShaders(norShaders[VERT_SHADER], vertData)
        self._addShaders(uvShaders[VERT_SHADER], vertData)
        self._addShaders(colorShaders[VERT_SHADER], vertData)
        
        # get multiple geometry shader functions
        self._addShaders(baseShaders[GEOM_SHADER], geomData)
        self._addShaders(vertexShaders[GEOM_SHADER], geomData)
        
        # get multiple fragment shader functions
        self._addShaders(uvShaders[FRAG_SHADER], fragData)
        self._addShaders(baseShaders[FRAG_SHADER], fragData)
        self._addShaders(vertexShaders[FRAG_SHADER], fragData)
        self._addShaders(colorShaders[FRAG_SHADER], fragData)
        if hasLight:
            self._addShaders(norShaders[FRAG_SHADER], fragData)
            self._addShaders(lightShaders[FRAG_SHADER], fragData)
        
        # add texture sampler as uniform
        for (_, _, type, name, _) in textures:
            fragData.functions[0].addUniform(type=type, name=name)
        
        if vertData.functions == []:
            vertData.functions.append(VertShaderFunc(name=None))
        self.addShaderAttributes(vertData.functions[0])
        
        # combine all shaders into one
        (vertShader, geomShader, fragShader) = \
                combineShader(vertData.functions,
                              geomData.functions,
                              fragData.functions)
        
        # setup main function
        if fragShader!=None:
            for var in fragData.localVars.keys():
                (type, val) = fragData.localVars[var]
                fragShader.addLocalVar(type, var, val)
            for exp in fragData.exports.keys():
                fragShader.addExport(exp, fragData.exports[exp])
        if geomShader!=None:
            for var in geomData.localVars.keys():
                (type, val) = geomData.localVars[var]
                geomShader.addLocalVar(type, var, val)
            for exp in geomData.exports.keys():
                geomShader.addExport(exp, geomData.exports[exp])
        if vertShader!=None:
            for var in vertData.localVars.keys():
                (type, val) = vertData.localVars[var]
                vertShader.addLocalVar(type, var, val)
            for exp in vertData.exports.keys():
                vertShader.addExport(exp, vertData.exports[exp])
        
        # get shader string representation
        shaderStr = ""
        for shader in [vertShader, geomShader, fragShader]:
            if shader==None:
                continue
            print shader.code()
            shaderStr += str(shader) + "\n"
        
        try: # try to use allready compiled shader
            (self.shaderProgram, self.shader) = self.segmentShaders[shaderStr]
            return
        except: pass
        
        if fragShader==None and geomShader==None and vertShader==None:
            self.shaderProgram = -1
            # self.shader handles enabling/disabling the shader
            self.shader = ShaderWrapper()
        else:
            # ready to compile...
            self.shaderProgram = compileProgram(
                        vertShader, geomShader, fragShader)
            
            # self.shader handles enabling/disabling the shader
            self.shader = SegmentShader(self,
                                        self.shaderProgram,
                                        textures)
        
        self.segmentShaders[shaderStr] = (self.shaderProgram, self.shader)
    
    def addShaderAttributes(self, shaderFunc):
        """
        adds a per vertex shader attribute.
        """
        shaderFunc.addAttribute(type="vec3", name="vertexPosition")
        if bool(self.enabledLights):
            shaderFunc.addAttribute(type="vec3", name="vertexNormal")
    
    def createDrawFunction(self):
        """
        generate the function used for drawing.
        """
        GLObject.createDrawFunction(self)
        if self.material!=None:
            # let material create the draw function and
            # include the material state setter/unsetter
            self.material.createDrawFunction()
            
            self.joinStaticStates(enable=self.material.enableStaticStates,
                                  disable=self.material.disableStaticStates)
            self.joinDynamicStates(enable=self.material.enableDynamicStates,
                                   disable=self.material.disableDynamicStates)
    
    def drawSegment(self):
        """
        upload geometry information of segment to opengl
        using glVertex, glDrawElements, an evaluator or similar.
        """
        raise NotImplementedError
    
    def hasCol(self):
        # returns if a color array should be used
        return False
    
    def isReflecting(self):
        return self.material.matReflection!=0.0
    
    def usesProjectiveTexture(self):
        return self.isReflecting()
    
    def setBaseImage(self, imgName):
        """
        sets base image of segment.
        @postcondition: base image will be used by create()
        """
        self.baseImage = imgName

