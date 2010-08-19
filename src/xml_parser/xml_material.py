# -*- coding: UTF-8 -*-
'''
Created on 01.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl

from xml_helper import xmlFloat, xmlFloatTuple, xmlBool, xmlStringList

from core.material import GLMaterial
from core.textures.texture import ImageTexture
from xml_parser.xml_state import xmlParseStateParam
from xml_parser.xml_states import xmlParseStateGroupParam

def _parseMaterialNode(name, node, xmlStateGroups):
    """
    create a GLMaterial instance from xml node.
    """
    
    params = {}
    textures = []
    
    for child in list(node):
        if child.tag == "state":
            xmlParseStateParam(child, params)
        
        elif child.tag == "stateGroup":
            xmlParseStateGroupParam(child, params, xmlStateGroups)
        
        elif child.tag == "texture":
            texName = child.get('image')
            tex = ImageTexture(texName)
            
            wrapMode = str(child.get('wrapping'))
            if wrapMode=="repeat":
                tex.wrapMode = gl.GL_REPEAT
            elif wrapMode=="clamp":
                tex.wrapMode = gl.GL_CLAMP
            
            tex.brightness = xmlFloat(child.get('brightness'), tex.brightness)
            tex.contrast = xmlFloat(child.get('contrast'), tex.contrast)
            tex.colfac = xmlFloat(child.get('colfac'), tex.colfac)
            tex.norfac = xmlFloat(child.get('norfac'), tex.norfac)
            tex.warpfac = xmlFloat(child.get('warpfac'), tex.warpfac)
            tex.dispfac = xmlFloat(child.get('dispfac'), tex.dispfac)
            tex.col = xmlFloatTuple(child.get('col'),
                                    default=tex.col)
            tex.rgbCol = xmlFloatTuple(child.get('rgbCol'),
                                       default=tex.rgbCol)
            tex.useMipMap = xmlBool(child.get('useMipMap'), tex.useMipMap)
            tex.noRGB = xmlBool(child.get('noRGB'), tex.noRGB)
            tex.stencil = xmlBool(child.get('stencil'), tex.stencil)
            tex.neg = xmlBool(child.get('neg'), tex.neg)
            tex.tangentSpace = xmlBool(child.get('tangentSpace'), tex.tangentSpace)
            tex.setBlendMode(child.get('blendMode'))
            tex.setMapInput(child.get('mapInput'))
            tex.setMapping(child.get('mapping'))
            tex.setMapTo(xmlStringList(child.get('mapTo'),
                                       default=['col']))
            
            if tex.useMipMap:
                # mipmapping filter mode
                tex.minFilterMode = gl.GL_LINEAR_MIPMAP_LINEAR
            
            textures.append(tex)
    
    params['textures'] = textures
    mat = GLMaterial(params)
    
    return mat


class XMLMaterials(object):
    """
    class managing material xml nodes.
    """
    def __init__(self, xmlStateGroups):
        self.xmlStateGroups = xmlStateGroups
        self.materialNodes = {}
        self.materialInstances = {}
    def loadMaterial(self, name):
        # try to get allready existing instance
        mat = self.materialInstances.get(name)
        if mat!=None: return mat
        
        # try to get xml node
        matNode = self.materialNodes.get(name)
        if matNode==None:
            print "WARNING: cannot load material '%s'. Loading default instead." % name
            return GLMaterial()
        
        # create a new instance
        mat = _parseMaterialNode(name, matNode, self.xmlStateGroups)
        self.materialInstances[name] = mat
        
        return mat
    def addMaterial(self, node):
        self.materialNodes[node.get('name')] = node
    def cleanup(self):
        for node in self.materialNodes.values():
            node.clear()
        self.materialNodes = {}
        self.materialInstances = {}
    def join(self, other):
        nodes = self.materialNodes.copy()
        for n in other.materialNodes.keys():
            nodes[n] = other.materialNodes[n]
        buf = XMLMaterials(self.xmlStateGroups)
        buf.materialNodes = nodes
        buf.materialInstances = {}
        return buf

def loadXMLMaterial(xmlMaterial, name):
    """
    creates a GLMaterial instance for a material with given name.
    """
    return xmlMaterial.loadMaterial(name)

def parseMaterialsNode(node, xmlStateGroups):
    """
    only material names are evaluated here
    """
    xmlMaterial = XMLMaterials(xmlStateGroups)
    for child in list(node):
        if child.tag != "material":
            continue
        xmlMaterial.addMaterial(child)
    return xmlMaterial

def cleanupMaterials(xmlMaterial):
    """
    remove references to all opened nodes.
    """
    xmlMaterial.cleanup()
