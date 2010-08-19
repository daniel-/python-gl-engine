# -*- coding: UTF-8 -*-
'''
Created on 20.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl
from OpenGL import GLU as glu

from xml_parser.xml_helper import xmlBool, xmlStringList, xmlStringTuple, \
    xmlFloatTupleList, xmlIntC, xmlBoolC, xmlFloatC, xmlFloatTupleC,\
    xmlIntTupleC, xmlFloatListC, xmlIntListC
from core.gl_state import GLState

glEnumMapping = {
    'GL_FLAT': gl.GL_FLAT,
    'GL_FILL': gl.GL_FILL,
    'GL_LINES': gl.GL_LINES,
    'GL_POINTS': gl.GL_POINTS,
    'GL_SMOOTH': gl.GL_SMOOTH,
    "GL_LINE": gl.GL_LINE,
    "GL_POINT": gl.GL_POINT,
    'GL_COLOR_MATERIAL': gl.GL_COLOR_MATERIAL,
    'GL_LINE_SMOOTH': gl.GL_LINE_SMOOTH,
    "GLU_FILL": glu.GLU_FILL,
    "GLU_OUTLINE_POLYGON": glu.GLU_OUTLINE_POLYGON,
    "GLU_OUTLINE_PATCH": glu.GLU_OUTLINE_PATCH
}

def xmlStateInt(val):
    try:
        return glEnumMapping[val]
    except:
        return xmlIntC(val)

# TODO: support more types
_typeMapping = {
    'int': xmlStateInt,
    'bool': xmlBoolC,
    'float': xmlFloatC,
    'stringList': xmlStringList,
    'intList': xmlIntListC,
    'floatList': xmlFloatListC,
    'intTuple': xmlIntTupleC,
    'floatTuple': xmlFloatTupleC,
    'stringTuple': xmlStringTuple,
    'floatTupleList': xmlFloatTupleList
}

def xmlParseState(node):
    """
    parses a state node and return an GLState instance.
    """
    stateType = node.get('type')
    return GLState( name    = node.get('name'),
                    value   = _typeMapping[stateType](node.get('val')),
                    dynamic = xmlBool(node.get('dynamic', False))
            )

def xmlParseStateParam(node, params):
    state = xmlParseState(node)
    try:
        params['states'].append(state)
    except KeyError:
        params['states'] = [state]

class GLVertexParam(object):
    def __init__(self, name, dynamic=False):
        self.name = name
        self.dynamic = dynamic

def xmlParseVertexParam( node, segmentParams ):
    name = node.get('name')
    param = GLVertexParam(name=name, dynamic=xmlBool(node.get('dynamic'), False))
    segmentParams[name] = param

