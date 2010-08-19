# -*- coding: UTF-8 -*-
'''
Created on 01.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl

from xml_parser.xml_helper import xmlFloatTuple, xmlFloat, xmlInt,\
    xmlIntList, xmlFloatTupleList, xmlFloatList, xmlFloatListC, xmlFloatTupleC,\
    xmlIntListC, xmlFloatTupleListC
from core.segments.lines import LineSegment
from core.segments.points import PointSegment
from core.segments.triangles import TriangleSegment
from core.segments.quads import QuadSegment
from core.segments.polygon import PolygonSegment
from core.segments.face import VArrayFace
from core.evaluators import CurveEvaluator, EvalParam, PatchEvaluator,\
    NURBCurveEvaluator, NURBPatchEvaluator
from core.segments.evaluator_segment import EvaluatorSegment
from xml_parser.xml_state import xmlParseStateParam, xmlParseVertexParam
from core.gl_vertex_attribute import GLVertexAttribute
from xml_parser.xml_states import xmlParseStateGroupParam

from numpy import array as NumpyArray


def _parseSegmentVertices(node, segmentParams):
    cos = []
    nos = []
    cols = []
    uvcos = []
    tangents = []
    
    for vNode in list(node):
        if vNode.tag != "v": continue
        
        # vertex coordinates must be specified
        co = xmlFloatTupleC(vNode.get('co'))
        if co==None:
            print "WARNING: skipping vertex node without co tag."
            continue
        cos.append(co)
            
        if nos!=None:
            no = xmlFloatTupleC(vNode.get('no'))
            if no==None: nos=None
            else: nos.append(no)
            
        if cols!=None:
            col = xmlFloatTupleC(vNode.get('col'))
            if col==None: cols=None
            else: cols.append(col)
            
        if uvcos!=None:
            uvco = xmlFloatTupleC(vNode.get('uvco'))
            if uvco==None: uvcos=None
            else: uvcos.append(col)
            
        if tangents!=None:
            tangent = xmlFloatTupleC(vNode.get('tangents'))
            if tangent==None: tangents=None
            else: tangents.append(tangent)
    
    # TODO: support other formats
    segmentParams['cos'] = GLVertexAttribute(name="vertexPosition",
                                    data=cos,
                                    elementSize=3*4,              # 3 (x/y/z) times 4 byte (sizeof float)
                                    normalize=False,
                                    dataType=gl.GL_FLOAT)
    if uvcos!=None:
        segmentParams['uvcos'] = GLVertexAttribute(name="vertexUV",
                                            data=uvcos,
                                            elementSize=2*4,      # 2 (u/v) times 4 byte (sizeof float)
                                            normalize=False,
                                            dataType=gl.GL_FLOAT)
    if nos!=None:
        segmentParams['nos'] = GLVertexAttribute(name="vertexNormal",
                                            data=nos,
                                            elementSize=3*4,      # 2 (u/v) times 4 byte (sizeof float)
                                            normalize=False,
                                            dataType=gl.GL_FLOAT)
    if cols!=None:
        segmentParams['col'] = GLVertexAttribute(name="vertexColor",
                                            data=cols,
                                            elementSize=4*4,      # 4 (r/g/b/a) times 4 byte (sizeof float)
                                            normalize=False,
                                            dataType=gl.GL_FLOAT)
    if tangents!=None:
        segmentParams['tangents'] = GLVertexAttribute(name="vertexTangent",
                                            data=tangents,
                                            elementSize=4*4,      # 4 (x/y/z/w) times 4 byte (sizeof float)
                                            normalize=False,
                                            dataType=gl.GL_FLOAT)

def _parseSegmentFaces(node, segmentParams, xmlStateGroups):
    segmentTypes = { 'Points':        (PointSegment, gl.GL_POINTS, 1)
                   , 'Lines':         (LineSegment, gl.GL_LINES, 2)
                   , 'LineStrip':     (LineSegment, gl.GL_LINE_STRIP, 2)
                   , 'LineLoop':      (LineSegment, gl.GL_LINE_LOOP, 2)
                   , 'Triangles':     (TriangleSegment, gl.GL_TRIANGLES, 3)
                   , 'TriangleStrip': (TriangleSegment, gl.GL_TRIANGLE_STRIP, 3)
                   , 'TriangleFan':   (TriangleSegment, gl.GL_TRIANGLE_FAN, 3)
                   , 'Quads':         (QuadSegment, gl.GL_QUADS, 4)
                   , 'QuadStrip':     (QuadSegment, gl.GL_QUAD_STRIP, 4)
                   , 'Polygon':       (PolygonSegment, gl.GL_POLYGON, -1)
                     }
    
    try:
        segmentCls, primitive, faceVertices = segmentTypes[node.get('primitive')]
    except:
        print "WARNING: unknown faces type '%s'" % node.get('primitive')
        return
    segmentParams['cls'] = segmentCls
    segmentParams['primitive'] = primitive
    
    faces = []
    indexes = []
    numIndexes = 0
    for fNode in list(node):
        if fNode.tag != "face": continue
        
        faceParams = {}
        
        for iNode in list(fNode):
            if iNode.tag == "i":
                if faceVertices==1 or faceVertices==2:
                    i = xmlIntList(iNode.get('val'))
                    if i!=None:
                        indexes += i
                        numIndexes += len(i)
                else:
                    faceParams['i'] = xmlIntListC(iNode.get('val'))
                    numIndexes += faceVertices
            elif iNode.tag == "state":
                if faceVertices==1 or faceVertices==2:
                    xmlParseStateParam( iNode, segmentParams )
                else:
                    xmlParseStateParam( iNode, faceParams )
            elif iNode.tag == "stateGroup":
                if faceVertices==1 or faceVertices==2:
                    xmlParseStateGroupParam( iNode, segmentParams, xmlStateGroups )
                else:
                    xmlParseStateGroupParam( iNode, faceParams, xmlStateGroups )
            elif iNode.tag == "uv":
                faceParams['uv'] = xmlFloatTupleListC(iNode.get('val'))
            elif iNode.tag == "col":
                faceParams['col'] = xmlFloatTupleListC(iNode.get('val'))
            elif iNode.tag == "nor":
                faceParams['nor'] = xmlFloatTupleListC(iNode.get('val'))
        
        if not (faceVertices==1 or faceVertices==2):
            faces.append(VArrayFace(faceParams))
        
    if faceVertices==1 or faceVertices==2:
        segmentParams['indexes'] = indexes
    segmentParams['numIndexes'] = numIndexes
    segmentParams['faces'] = (faces, primitive, faceVertices)

def _curveTargets():
    return {
                "vertex": gl.GL_MAP1_VERTEX_3,
                "vertex4": gl.GL_MAP1_VERTEX_4,
                "normal": gl.GL_MAP1_NORMAL,
                "index": gl.GL_MAP1_INDEX,
                "color": gl.GL_MAP1_COLOR_4,
                "texture": gl.GL_MAP1_TEXTURE_COORD_2,
                "texture3": gl.GL_MAP1_TEXTURE_COORD_3,
                "texture4": gl.GL_MAP1_TEXTURE_COORD_4,
                "texture1": gl.GL_MAP1_TEXTURE_COORD_1
            }
def _patchTargets():
    return {
                "vertex": gl.GL_MAP2_VERTEX_3,
                "vertex4": gl.GL_MAP2_VERTEX_4,
                "normal": gl.GL_MAP2_NORMAL,
                "index": gl.GL_MAP2_INDEX,
                "color": gl.GL_MAP2_COLOR_4,
                "texture": gl.GL_MAP2_TEXTURE_COORD_2,
                "texture3": gl.GL_MAP2_TEXTURE_COORD_3,
                "texture4": gl.GL_MAP2_TEXTURE_COORD_4,
                "texture1": gl.GL_MAP2_TEXTURE_COORD_1
            }
def _parseSegmentEvaluators(node, segmentParams, xmlStateGroups):
    evaluators = []
    
    def _readParam(n, name, param):
        param.min = xmlFloat(n.get('min'), 0.0)
        param.max = xmlFloat(n.get('max'), 1.0)
        param.steps = xmlInt(n.get('steps'), 20)
    
    vertexEvaluator = None
    normalEvaluator = None
    needsNormals = False
    
    for child in list(node):
        if child.tag != "evaluator":
            continue
        
        segmentParams['cls'] = EvaluatorSegment
        evalParams = {}
        
        target = child.get('target', 'vertex')
        u = EvalParam("u")
        v = EvalParam("v")
        
        for n in list(child):
            if n.tag == "u":
                _readParam(n, n.tag, u)
            elif n.tag == "v":
                _readParam(n, n.tag, v)
            elif n.tag == "ctrls":
                evalParams['ctrls'] = _parseEvaluatorCtrls(n)
            elif n.tag == "state":
                xmlParseStateParam(n, evalParams)
            elif child.tag == "stateGroup":
                xmlParseStateGroupParam(n, evalParams, xmlStateGroups)
            elif n.tag == "vertexParam":
                xmlParseVertexParam( n, evalParams , xmlStateGroups)
        
        try:
            evalParams['ctrls'][0][0][0]
            isCurve = False
        except:
            isCurve = True
        
        if isCurve:
            evalParams['target'] = _curveTargets()[target]
            evalParams['params'] = [u]
            evaluatorCls = CurveEvaluator
        else:
            evalParams['target'] = _patchTargets()[target]
            evalParams['params'] = [u, v]
            evaluatorCls = PatchEvaluator
        
        evaluator = evaluatorCls(evalParams)
        
        if target=="vertex" or target=="vertex4":
            vertexEvaluator = evaluator
            # curves dont need normals
            needsNormals = not isCurve
        if target=="normal":
            normalEvaluator = evaluator
        
        evaluators.append(evaluator)
    
    if needsNormals and normalEvaluator==None and vertexEvaluator!=None:
        vertexEvaluator.generateNormals = True
    
    segmentParams['evaluators'] = evaluators
def _parseSegmentNurbs(node, segmentParams, xmlStateGroups):
    evaluators = []
    
    vertexEvaluator = None
    normalEvaluator = None
    needsNormals = False
        
    segmentParams['cls'] = EvaluatorSegment
    
    for child in list(node):
        if child.tag != "nurb":
            continue
        
        target = child.get('target', 'vertex')
        uKnot = [0.0]*4 + [1.0]*4
        vKnot = [0.0]*4 + [1.0]*4
        
        params = {}
        
        for n in list(child):
            if n.tag == "u":
                uKnot = xmlFloatListC(n.get('knot'), uKnot)
            elif n.tag == "v":
                vKnot = xmlFloatListC(n.get('knot'), vKnot)
            elif n.tag == "ctrls":
                params['ctrls'] = _parseEvaluatorCtrls(n)
            elif n.tag == "state":
                xmlParseStateParam(n, params)
            elif child.tag == "stateGroup":
                xmlParseStateGroupParam(n, params, xmlStateGroups)
            elif n.tag == "vertexParam":
                xmlParseVertexParam( n, params , xmlStateGroups)
        
        try:
            params['ctrls'][0][0][0]
            isCurve = False
        except:
            isCurve = True
        
        params['tolerance'] = xmlFloat(child.get('tolerance'), 25.0)
        
        if isCurve:
            params['target'] = _curveTargets()[target]
            params['knots'] = [uKnot]
            nurbCls = NURBCurveEvaluator
        else:
            params['target'] = _patchTargets()[target]
            params['knots'] = [uKnot, vKnot]
            nurbCls = NURBPatchEvaluator
        
        evaluator = nurbCls(params)
        
        if target=="vertex" or target=="vertex4":
            vertexEvaluator = evaluator
            # curves dont need normals
            needsNormals = not isCurve
        if target=="normal":
            normalEvaluator = evaluator
        
        evaluators.append(evaluator)
    
    if needsNormals and normalEvaluator==None and vertexEvaluator!=None:
        vertexEvaluator.generateNormals = True
    
    segmentParams['evaluators'] = evaluators


def _parseSegmentNode(name, node, xmlStateGroups):
    """
    parses a segment node and creates a segment instance.
    """
    
    segmentParams = {}
    
    for child in list(node):
        # parse vertices
        if child.tag == "vertices":
            _parseSegmentVertices(child, segmentParams)
        # parse faces
        elif child.tag == "faces":
            _parseSegmentFaces(child, segmentParams, xmlStateGroups)
        # parse evaluators
        elif child.tag == "evaluators":
            _parseSegmentEvaluators(child, segmentParams, xmlStateGroups)
        # parse nurbs
        elif child.tag == "nurbs":
            _parseSegmentNurbs(child, segmentParams, xmlStateGroups)
        elif child.tag == "state":
            xmlParseStateParam( child, segmentParams )
        elif child.tag == "stateGroup":
            xmlParseStateGroupParam(child, segmentParams, xmlStateGroups)
        elif child.tag == "vertexParam":
            xmlParseVertexParam( child, segmentParams , xmlStateGroups)
        else:
            print "WARNING: XML: unknown tag '%s'" % child.tag
    
    try:
        segmentCls = segmentParams['cls']
    except:
        print "WARNING: no segment class sepecified!"
        return None
    
    return (name, segmentParams, segmentCls)


### some utility parsers ####

def _parseEvaluatorCtrls(node, level=0):
    """
    builds (multi)dimensional float-tuple list.
    """
    if level>1:
        print "WARNING: something messed up with evaluator section of xml."
        return []
    
    ret = []
    for child in list(node):
        if child.tag == "ctrls":
            ret.append( _parseEvaluatorCtrls(child, level+1) )
        elif child.tag == "p":
            ret.append( xmlFloatTuple(child.get('val'),
                                      default=(0.0, 0.0, 0.0) ))
        else:
            continue
    if level==0:
        return NumpyArray(ret, "float32")
    else:
        return ret

### ###


class XMLSegments(object):
    """
    class managing segment xml nodes.
    """
    def __init__(self, xmlStateGroups):
        self.xmlStateGroups = xmlStateGroups
        self.segmentNodes = {}
    def loadSegment(self, name):
        try:
            segmentNode = self.segmentNodes[name]
        except:
            print "WARNING: cannot load segment '%s'" % name
            return
        return _parseSegmentNode(name, segmentNode, self.xmlStateGroups)
    def addSegment(self, node):
        self.segmentNodes[node.get('name')] = node
    def cleanup(self):
        for node in self.segmentNodes.values():
            node.clear()
        self.segmentNodes = {}
    def join(self, other):
        nodes = self.segmentNodes.copy()
        for n in other.segmentNodes.keys():
            nodes[n] = other.segmentNodes[n]
        buf = XMLSegments(self.xmlStateGroups)
        buf.segmentNodes = nodes
        return buf

def loadXMLSegment(xmlSegments, name):
    """
    creates a segment instance for a segment with given name.
    """
    return xmlSegments.loadSegment(name)

def parseSegmentsNode(node, xmlStateGroups):
    """
    only segment names are evaluated here
    """
    xmlSegments = XMLSegments(xmlStateGroups)
    for child in list(node):
        if child.tag != "segment":
            continue
        xmlSegments.addSegment(child)
    return xmlSegments

def cleanupSegments(xmlSegments):
    """
    remove references to all opened nodes.
    """
    xmlSegments.cleanup()
