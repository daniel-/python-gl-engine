# -*- coding: UTF-8 -*-
'''
Created on 02.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from core.light.light import Light
from xml_parser.xml_state import xmlParseStateParam
from xml_parser.xml_states import xmlParseStateGroupParam

def _parseLightNode(node, xmlStateGroups):
    """
    parses a light node and creates a model instance.
    """
    
    params = { 'name': node.get('name') }
    
    for child in list(node):
        if child.tag == "state":
            xmlParseStateParam(child, params)
        elif child.tag == "stateGroup":
            xmlParseStateGroupParam(child, params, xmlStateGroups)
        else:
            print "WARNING: unknown light tag '%s'." % child.tag
    
    return Light(params)

def loadXMLLight(node, xmlStateGroups):
    """
    only model names are evaluated here
    """
    glLights = []
    for child in list(node):
        if child.tag != "light":
            continue
        glLights.append(_parseLightNode(child, xmlStateGroups))
    return glLights

