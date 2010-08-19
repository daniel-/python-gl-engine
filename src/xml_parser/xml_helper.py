# -*- coding: UTF-8 -*-
'''
Created on 01.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from ctypes import c_int, c_byte, c_float

from numpy import array as NumpyArray

from xml.etree.cElementTree import iterparse

def xmlInt(intStr, default=None):
    """
    xml string to python list.
    """
    try:
        return int(intStr)
    except ValueError: pass
    except TypeError:  pass
    
    try:
        # Try hex int
        return int(intStr, 16)
    except ValueError: pass
    except TypeError:  pass
    
    return default
def xmlIntC(intStr, default=None):
    return c_int(xmlInt(intStr, default))

def xmlBool(boolStr, default=None):
    """
    xml string to python list.
    """
    if boolStr=="True" or boolStr=="true" or boolStr=="1":
        return 1
    elif boolStr=="False" or boolStr=="false" or boolStr=="0":
        return 0
    else:
        return default
def xmlBoolC(boolStr, default=None):
    return c_byte(xmlBool(boolStr, default))

def xmlFloat(floatStr, default=None):
    """
    xml string to python float.
    """
    try:
        return float(floatStr)
    except ValueError: pass
    except TypeError:  pass
    
    return default
def xmlFloatC(floatStr, default=None):
    return c_float(xmlFloat(floatStr, default))

def _xmlIterable(iterStr, xmlElem):
    opened = 0
    elems = []
    elem = ""
    
    if iterStr==None:
        raise ValueError, "cannot iterate None"
    
    for s in list(iterStr):
        if s==" ": continue
        
        if s in ['[', '(']:
            opened += 1
            continue
        elif s in [']', ')']:
            opened -= 1
            continue
        elif elems==[] and elem=="" and opened==0:
            opened += 1
        
        if opened==1:
            if s==",": # end of elem
                elems.append(elem)
                elem = ""
            else:
                elem += s
        else:
            elem += s
    
    if elem!="":
        elems.append(elem)
    elems = map(lambda e: xmlElem(e, None), elems)
    
    return elems
            

def xmlList(listStr, getXMLElem, default=None):
    """
    xml string to python list.
    """
    try:
        return list(_xmlIterable(listStr,
                                 getXMLElem))
    except ValueError:
        return default
def xmlFloatList(listStr, default=None):
    return xmlList(listStr, xmlFloat, default)
def xmlIntList(listStr, default=None):
    return xmlList(listStr, xmlInt, default)
def xmlStringList(listStr, default=None):
    def doNothing(e, _):
        return e
    return xmlList(listStr, doNothing, default)
def xmlFloatTupleList(listStr):
    return xmlList(listStr, xmlFloatTuple, default=None)


# create numpy array for some states
def xmlIntListC(xmlStr, default=None):
    p = xmlIntList(xmlStr, default)
    if p==None: return None
    return NumpyArray(p, "int32")
def xmlFloatListC(xmlStr, default=None):
    p = xmlFloatList(xmlStr, default)
    if p==None: return None
    return NumpyArray(p, "float32")
def xmlIntTupleC(xmlStr, default=None):
    p = xmlIntTuple(xmlStr, default)
    if p==None: return None
    return NumpyArray(p, "int32")
def xmlFloatTupleC(xmlStr, default=None):
    p = xmlFloatTuple(xmlStr, default)
    if p==None: return None
    return NumpyArray(p, "float32")
def xmlFloatTupleListC(listStr):
    return xmlList(listStr, xmlFloatTupleC, default=None)


def xmlTuple(tupleStr, getXMLElem, default=None):
    """
    xml string to python tuple.
    """
    try:
        return tuple(_xmlIterable(tupleStr,
                                  getXMLElem))
    except ValueError:
        return default
def xmlFloatTuple(tupleStr, default=None):
    return xmlTuple(tupleStr, xmlFloat, default)
def xmlIntTuple(tupleStr, default=None):
    return xmlTuple(tupleStr, xmlInt, default)
def xmlStringTuple(tupleStr, default=None):
    def doNothing(e, _):
        return e
    return xmlTuple(tupleStr, doNothing, default)

def xmlGetRoot(file):
    # get an iterable
    context = iterparse(file, events=("start", "end"))
    # turn it into an iterator
    context = iter(context)
    # get the root element
    _, root = context.next()
    
    # TODO: without this parser does not work like expected..
    #       investigate and find out why.
    for _, _ in context:
        pass
    
    return root

def xmlFindChild(node, name):
    """
    looks up a node with specified tag in the level below @node.
    if @node has this tag, then @node is returned.
    """
    if node.tag == name:
        return node
    for child in list(node):
        if child.tag == name:
            return child
    return None
