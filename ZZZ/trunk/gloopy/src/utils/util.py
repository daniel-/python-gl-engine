

def doNothing():
    pass


def listGet(list, index):
    try:
        return list[index]
    except:
        return None

def joinFunctions(func1, func2):
    if func1==doNothing: return func2
    if func2==doNothing: return func1
    def joinFuncs():
        func1()
        func2()
    return joinFuncs

def format_number(n, accuracy=6):
    """Formats a number in a friendly manner (removes trailing zeros and unneccesary point."""
    
    fs = "%."+str(accuracy)+"f"
    str_n = fs%float(n)
    if '.' in str_n:
        str_n = str_n.rstrip('0').rstrip('.')
    if str_n == "-0":
        str_n = "0"
    #str_n = str_n.replace("-0", "0")
    return str_n
    

def lerp(a, b, i):
    """Linear interpolate from a to b."""
    return a+(b-a)*i

def unique(seq, idfun=None): 
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

### blender math funcs

"""
from math import sqrt

def normalise(v):
    (x, y, z) = tuple(v)        
    l = sqrt(x*x + y*y + z*z)
    v[0] = x/l
    v[1] = y/l
    v[2] = z/l
    return v   

def newV3(val=0.0):
    return [val, val, val]

def normal_quad_v3(v1, v2, v3, v4):
    n = newV3()
    
    # real cross!
    n1 = newV3()
    n2 = newV3()

    n1[0]= v1[0]-v3[0]
    n1[1]= v1[1]-v3[1]
    n1[2]= v1[2]-v3[2]

    n2[0]= v2[0]-v4[0]
    n2[1]= v2[1]-v4[1]
    n2[2]= v2[2]-v4[2]

    n[0]= n1[1]*n2[2]-n1[2]*n2[1]
    n[1]= n1[2]*n2[0]-n1[0]*n2[2]
    n[2]= n1[0]*n2[1]-n1[1]*n2[0]

    return normalise(n)

def normal_tri_v3(n, v1, v2, v3):
    n1 = [0.0, 0.0, 0.0]
    n2 = [0.0, 0.0, 0.0]

    n1[0]= v1[0]-v2[0]
    n2[0]= v2[0]-v3[0]
    n1[1]= v1[1]-v2[1]
    n2[1]= v2[1]-v3[1]
    n1[2]= v1[2]-v2[2]
    n2[2]= v2[2]-v3[2]
    n[0]= n1[1]*n2[2]-n1[2]*n2[1]
    n[1]= n1[2]*n2[0]-n1[0]*n2[2]
    n[2]= n1[0]*n2[1]-n1[1]*n2[0]
    
    return normalise(n)

def sub_v3_v3v3(r, a, b):
    r[0]= a[0] - b[0]
    r[1]= a[1] - b[1]
    r[2]= a[2] - b[2]

def cross_v3_v3v3(r, a, b):
    r[0]= a[1]*b[2] - a[2]*b[1]
    r[1]= a[2]*b[0] - a[0]*b[2]
    r[2]= a[0]*b[1] - a[1]*b[0]

def add_v3_v3v3(r, a, b):
    r[0]= a[0] + b[0]
    r[1]= a[1] + b[1]
    r[2]= a[2] + b[2]

# TODO: TSPACE: tangent function !?!?
def tangent_from_uv(uv1, uv2, uv3, co1, co2, co3, n):
    tang = newV3()
    
    s1= uv2[0] - uv1[0]
    s2= uv3[0] - uv1[0]
    t1= uv2[1] - uv1[1]
    t2= uv3[1] - uv1[1]

    if(s1 and s2 and t1 and t2): # otherwise 'tang' becomes nan
        tangv = newV3()
        ct = newV3()
        e1 = newV3()
        e2 = newV3()
        det = newV3()
        det= 1.0 / (s1 * t2 - s2 * t1)

        # normals in render are inversed...
        
        sub_v3_v3v3(e1, co1, co2);
        sub_v3_v3v3(e2, co1, co3);
        tang[0] = (t2*e1[0] - t1*e2[0])*det;
        tang[1] = (t2*e1[1] - t1*e2[1])*det;
        tang[2] = (t2*e1[2] - t1*e2[2])*det;
        tangv[0] = (s1*e2[0] - s2*e1[0])*det;
        tangv[1] = (s1*e2[1] - s2*e1[1])*det;
        tangv[2] = (s1*e2[2] - s2*e1[2])*det;
        cross_v3_v3v3(ct, tang, tangv);
    
        # check flip
        if ((ct[0]*n[0] + ct[1]*n[1] + ct[2]*n[2]) < 0.0):
            tang = map(lambda x: -x, tang)
    else:
        tang[0]= 0.0
        tang[1]= 0.0
        tang[2]= 0.0
    return tang
"""
