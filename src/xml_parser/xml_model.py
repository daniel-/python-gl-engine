# -*- coding: UTF-8 -*-
'''
Created on 08.05.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from core.model import Model

from xml_parser.xml_segment import loadXMLSegment
from xml_material import loadXMLMaterial
from core.material import GLMaterial
from utils.util import unique
from xml_parser.xml_state import xmlParseStateParam, xmlParseVertexParam


def _parseModelSegmentNode(xmlMaterials, lights, (segmentName, segmentParams, segmentCls), node):
    """
    parse segment configuration specified by model.
    """
    
    baseImage = None
    
    for child in list(node):
        if child.tag == "state":
            xmlParseStateParam( child, segmentParams )
        elif child.tag == "vertexParam":
            xmlParseVertexParam( child, segmentParams )
        elif child.tag == "image":
            baseImage = str(child.get('val'))
        elif child.tag == "material":
            material = loadXMLMaterial(xmlMaterials, str(child.get('name')))
        else:
            print "WARNING: unknown model segment tag '%s'" % child.tag
    
    if material == None:
        # segment needs material
        material = GLMaterial()
    
    segmentParams['material'] = material
    
    segment = segmentCls(name=segmentName, params=segmentParams)
    if baseImage!=None:
        segment.setBaseImage(baseImage)
    
    return segment
    

def _parseModelNode(xmlSegments, xmlMaterials, lights, name, node):
    """
    parses a model node and creates a model instance.
    """
    
    params = {}
    
    segments = []
    sLights = []
    for child in list(node):
        if child.tag == "segment":
            segmentName = child.get('name')
            
            segment = loadXMLSegment(xmlSegments, segmentName)
            # load additional attributes into the datatype (rotation,translation,..)
            segment = _parseModelSegmentNode(xmlMaterials, lights, segment, child)
            segments.append(segment)
                
        elif child.tag == "state":
            xmlParseStateParam(child, params)
        
        elif child.tag == "light":
            name = child.get('name')
            for l in lights:
                if l.name==name:
                    sLights.append(l)
                    break
        else:
            print "WARNING: unknown model tag '%s'" % child.tag
    
    m = Model(segments=segments, params=params)
    m.setLights(sLights)
    
    return m

class XMLModels(object):
    """
    class managing model xml nodes.
    """
    def __init__(self, lights, xmlSegments, xmlStateGroups, xmlMaterials):
        self.xmlSegments = xmlSegments
        self.xmlStateGroups = xmlStateGroups
        self.xmlMaterials = xmlMaterials
        self.lights = lights
        self.modelNodes = {}
    def loadModel(self, name):
        try:
            modelNode = self.modelNodes[name]
        except KeyError:
            print "WARNING: cannot load model '%s'" % name
            return
        modelIter = modelNode.getiterator()
        modelNode = modelIter.next()
        return _parseModelNode(self.xmlSegments, self.xmlMaterials, self.lights, name, modelNode)
    def addModel(self, node):
        self.modelNodes[node.get('name')] = node
    def cleanup(self):
        for node in self.modelNodes.values():
            node.clear()
        self.modelNodes = {}
    def join(self, other):
        xmlStateGroups  = self.xmlStateGroups.join(other.xmlStateGroups)
        xmlSegments  = self.xmlSegments.join(other.xmlSegments)
        xmlMaterials = self.xmlMaterials.join(other.xmlMaterials)
        lights = unique( self.lights + other.lights )
        buf = XMLModels(lights, xmlSegments, xmlStateGroups, xmlMaterials)
        nodes = self.modelNodes.copy()
        for n in other.modelNodes.keys():
            nodes[n] = other.modelNodes[n]
        buf.modelNodes = nodes
        return buf

def loadXMLModel(xmlModels, name):
    """
    creates a model instance for a model with given name.
    """
    return xmlModels.loadModel(name)

def parseModelsNode(node, lights, xmlSegments, xmlStateGroups, xmlMaterials):
    """
    only model names are evaluated here
    """
    xmlModels = XMLModels(lights, xmlSegments, xmlStateGroups, xmlMaterials)
    for child in list(node):
        if child.tag != "model":
            continue
        xmlModels.addModel(child)
    return xmlModels

def cleanupModels(xmlModels):
    """
    remove references to all opened nodes.
    """
    xmlModels.cleanup()
