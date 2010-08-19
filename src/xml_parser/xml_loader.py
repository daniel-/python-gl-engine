# -*- coding: UTF-8 -*-
'''
Created on 02.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from xml_parser.xml_helper import xmlGetRoot, xmlFindChild
from xml_parser.xml_material import parseMaterialsNode, XMLMaterials
from xml_parser.xml_segment import parseSegmentsNode, XMLSegments
from xml_parser.xml_model import parseModelsNode, XMLModels, loadXMLModel
from xml_parser.xml_light import loadXMLLight
from utils.util import unique
from xml_parser.xml_states import XMLStateGroups, parseStateGroupNode

class XMLLoader(object):
    """
    interface for loading models from xml.
    """
    
    def __init__(self, xmlFiles):
        self.xmlStateGroups = XMLStateGroups()
        self.xmlMaterials = XMLMaterials(self.xmlStateGroups)
        self.xmlSegments = XMLSegments(self.xmlStateGroups)
        self.lights = []
        
        self.xmlModels = XMLModels(self.lights,
                                   self.xmlSegments,
                                   self.xmlStateGroups,
                                   self.xmlMaterials)
        
        # join results from all files
        for f in xmlFiles:
            (stat, mat, seg, mod, lights) = _loadXMLModels(f)
            
            self.lights = unique( self.lights + lights)
            
            self.xmlStateGroups = self.xmlStateGroups.join(stat)
            
            self.xmlMaterials = self.xmlMaterials.join(mat)
            self.xmlMaterials.xmlStateGroups = self.xmlStateGroups
            
            self.xmlSegments = self.xmlSegments.join(seg)
            self.xmlSegments.xmlStateGroups = self.xmlStateGroups
            
            self.xmlModels = self.xmlModels.join(mod)
            self.xmlModels.xmlMaterials = self.xmlMaterials
            self.xmlModels.xmlSegments =self.xmlSegments
            self.xmlModels.xmlStateGroups = self.xmlStateGroups
            self.xmlModels.lights = self.lights
    
    def __del__(self):
        self.xmlStateGroups.cleanup()
        self.xmlMaterials.cleanup()
        self.xmlSegments.cleanup()
        self.xmlModels.cleanup()
    
    def getModel(self, modelName):
        """
        returns instance for model with given name.
        """
        return loadXMLModel(self.xmlModels, modelName)

def _findChild(root, name):
    """
    looks up node with specified tag in list of root nodes.
    """
    materialNode = xmlFindChild(root, name)
    if materialNode != None:
        return materialNode

def _loadXMLModelsRoot(root):
    """
    returns list of models found in xml root nodes.
    """
    # load material information
    node = _findChild(root, "stateGroups")
    if node != None:
        xmlStateGroups = parseStateGroupNode(node)
    else:
        xmlStateGroups = None
    
    # load material information
    node = _findChild(root, "materials")
    if node != None:
        xmlMaterials = parseMaterialsNode(node, xmlStateGroups)
    else:
        xmlMaterials = None
    
    # load segment data
    node = _findChild(root, "segments")
    if node != None:
        xmlSegments = parseSegmentsNode(node, xmlStateGroups)
    else:
        xmlSegments = None
        
    # load lights
    node = _findChild(root, "lights")
    if node != None:
        lights = loadXMLLight(node, xmlStateGroups)
    else:
        lights = []
                     
    # and the models
    node = _findChild(root, "models")
    if node != None:
        xmlModels = parseModelsNode(node, lights, xmlSegments, xmlStateGroups, xmlMaterials)
    else:
        xmlModels = None
    
    return (xmlStateGroups, xmlMaterials, xmlSegments, xmlModels, lights)
def _loadXMLModels(file):
    """
    returns list of models found in xml files.
    """
    return _loadXMLModelsRoot(xmlGetRoot(file))
