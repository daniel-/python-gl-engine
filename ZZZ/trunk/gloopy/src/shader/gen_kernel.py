# -*- coding: UTF-8 -*-
'''
Created on 02.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

def buildKernel(x, y):
    ret = []
    for i in range(x):
        i += 0.5*float(1-x)
        
        for j in range(y):
            j += 0.5*float(1-y)
            
            ret.append((float(i), float(j)))
    return ret

def printKernel(kernel, x, y):
    k = 0
    buf = ""
    for _ in range(x):
        for _ in range(y):
            buf += str(kernel[k]) + ","
            k += 1
        buf += "\n"
    print buf
