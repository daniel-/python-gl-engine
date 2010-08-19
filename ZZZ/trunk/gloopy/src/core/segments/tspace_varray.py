# -*- coding: UTF-8 -*-
'''
Created on 18.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from core.segments.segment import ShaderData, FRAG_SHADER, VERT_SHADER
from core.light.normal_mapping import BumpMapFrag, BumpMapVert
from core.textures.texture import Texture2D
from core.segments.face_varray import FaceVArray
from shader.shader_utils import NORMAL_VARYING
from core.gl_vertex_attribute import GLVertexAttribute

class TSpaceSegment(FaceVArray):
    """
    a segment that declares some stuff for tangent space calculation.
    the actual generation of tangents must take place in subclasses.
    """
    
    def __init__(self, name, params):
        self.tangents = params.get('vertexTangent')
        
        conf = params.get('tangentsConf')
        if conf!=None and conf.dynamic:
            self.dynamicTangents = True
        else:
            self.dynamicTangents = False
        
        FaceVArray.__init__(self, name, params)
    
    def createResources(self):
        FaceVArray.createResources(self)
        if self.needTangents():
            self.tangents = self.generateTangents()
    
    def isDynamicAttribute(self, attribute):
        if self.tangents==attribute:
            return self.dynamicTangents
        else:
            return FaceVArray.isDynamicAttribute(self, attribute)
    
    def createVBOs(self):
        """
        add tangent attribute before creating the vbos.
        """
        self.addAttribute(self.tangents)
        FaceVArray.createVBOs(self)
    
    def postCreate(self):
        FaceVArray.postCreate(self)
        del self.tangents
    
    def createNorShaders(self, textures, matTextures):
        """
        handle normal mapping shader depending on
        tangent space calculations.
        """
        
        data = [ShaderData(), ShaderData(), ShaderData()]
        
        norTexData = matTextures.get(Texture2D.MAP_TO_NOR, [])
        for (tex, texData) in norTexData:
            _, _, _, i = texData
            
            bumpFrag = BumpMapFrag(enabledLights=self.enabledLights)
            bumpFrag.setArgs(["texel%d" % i, "n"])
            data[FRAG_SHADER].functions.append(bumpFrag)
            
            data[FRAG_SHADER].localVars["texel%d" % i] = \
                    ("vec4", "texture2D( Texture%d, gl_TexCoord[0].xy )" % i)
            # need uv coordinate
            data[VERT_SHADER].exports["gl_TexCoord[0].xy"] = "vertexUV"
            
            if tex.tangentSpace:
                # need to convert some vectors to tangent space
                bumpVert = BumpMapVert(enabledLights=self.enabledLights)
                bumpVert.setArgs(["n"])
                data[VERT_SHADER].functions.append(bumpVert)
        
        data[VERT_SHADER].localVars["n"] = ("vec3", "normalize( gl_NormalMatrix * vertexNormal )")
        data[VERT_SHADER].exports[NORMAL_VARYING] = "n"
        
        return data
    
    def addShaderAttributes(self, shaderFunc):
        """
        adds a per vertex shader attribute.
        """
        FaceVArray.addShaderAttributes(self, shaderFunc)
        if self.hasTangents():
            shaderFunc.addAttribute(type="vec4", name="vertexTangent")
    
    def duplicatePerVertexAttribute(self, index):
        FaceVArray.duplicatePerVertexAttribute(self, index)
        if self.hasTangents():
            # FIXME: TSPACE: for different per face uv tangents cant be duplicated like this,
            #                    because their calculation depends on the uv values
            self.tangents.data.append(self.tangents.data[index])
    
    # abstract generation methods
    def generateTangents(self):
        raise NotImplementedError
    
    def hasTangents(self):
        return bool(self.tangents)
    def needTangents(self):
        for tex in self.material.textures:
            if tex.tangentSpace:
                return True
        return False
