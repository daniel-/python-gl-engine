# -*- coding: UTF-8 -*-
'''
Created on 24.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from xml_parser.xml_state import xmlParseStateParam
from core.state_group import GLStateGroup
from xml_parser.xml_helper import xmlBool

def xmlParseStateGroupParam(node, params, xmlStateGroups):
    stateGroup = xmlStateGroups.loadStateGroup(node.get('name'))
    try:
        params['stateGroups'].append(stateGroup)
    except:
        params['stateGroups'] = [stateGroup]

def xmlParseStateGroup(node):
    params = {}
    
    name = node.get('name')
    dynamic = xmlBool(node.get('dynamic'), False)
    
    for child in list(node):
        if child.tag!="state": continue
        xmlParseStateParam(child, params)
    
    return GLStateGroup(params, name, dynamic)


class XMLStateGroups(object):
    """
    class managing material xml nodes.
    """
    def __init__(self):
        self.stateGroupNodes = {}
        self.stateGroupInstances = {}
    def loadStateGroup(self, name):
        # try to get allready existing instance
        stateGroup = self.stateGroupInstances.get(name)
        if stateGroup!=None: return stateGroup
        
        # try to get xml node
        stateGroupNode = self.stateGroupNodes.get(name)
        if stateGroupNode==None:
            print "Error: cannot load state group '%s'." % name
            return None
        
        # create a new instance
        stateGroup = xmlParseStateGroup(stateGroupNode)
        self.stateGroupInstances[name] = stateGroup
        
        return stateGroup
    def addStateGroup(self, node):
        self.stateGroupNodes[node.get('name')] = node
    def cleanup(self):
        for node in self.stateGroupNodes.values():
            node.clear()
        self.stateGroupNodes = {}
        self.stateGroupInstances = {}
    def join(self, other):
        if self==None: return other
        elif other==None: return self
        nodes = self.stateGroupNodes.copy()
        for n in other.stateGroupNodes.keys():
            nodes[n] = other.stateGroupNodes[n]
        buf = XMLStateGroups()
        buf.stateGroupNodes = nodes
        buf.stateGroupInstances = {}
        return buf

def loadXMLState(xmlStateGroups, name):
    return xmlStateGroups.loadStateGroup(name)

def parseStateGroupNode(node):
    xmlStateGroups = XMLStateGroups()
    for child in list(node):
        if child.tag != "group":
            continue
        xmlStateGroups.addStateGroup(child)
    return xmlStateGroups

def cleanupStates(xmlStateGroups):
    xmlStateGroups.cleanup()
