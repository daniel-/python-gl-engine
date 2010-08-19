"""
----------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<daniel@orgizm.net> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Daniel Bessler
----------------------------------------------------------------------------
"""

"""
Calculates the best approximation of measure points with
the approximate function given by mathematical terms.
"""

from sys import path as spath
from os import path as opath
parentPath = opath.split(opath.split(opath.abspath(__file__))[0])[0]
print parentPath
if not parentPath in spath:
    spath.insert(0, parentPath)

from expression.expression import Expression
from vector import Vector
from matrix import Matrix

# import evaluatable terms
from math import * #@UnusedWildImport

class Term():
    """
    a mathematical term.
    """
    
    def __init__(self, term, xvector, yvector):
        """
        Constructs a Term instance.
        @param term A Term string, musst be evaluatable.
        @param xvector Vector with x-coordinates of the measure points.
        @param yvector Vector with y-coordinates of the measure points.
        """
        assert len(xvector) == len(yvector)
        self.xvector = xvector
        self.yvector = yvector
        self.term = term
    
    def __mul__(self, other):
        """
        * operator.
        @param other another Term.
        """
        value = 0.0
        # calculating the gauss sum
        for i in range(len(self.xvector)):
            value += self.val(i)*other.val(i)
        return value

    def val(self, i):
        """
        Returns value of term related to vector dimension i.
        @param i the vector dimension.
        """
        if self.term == "const":
            return 1
        elif self.term == "y":
            return self.yvector[i]
        else:
            return eval(self.term.replace("x", str(self.xvector[i])))

def approximate(terms, mesurePoints):
    """
    Calculates the best approximation of mesurePoints with
    the approximate function given by terms.
    @param terms List of Terms (can be every method defined in math (sqrt(x), pow(x,2),...)),
                 there can only be one variable and it must be x.
    @param mesurePoints List of measure points ((x,y) values).
    """
    print terms
    print mesurePoints
    
    # measure vectors
    xpoints, ypoints = zip(*mesurePoints)
    xv, yv = (Vector(xpoints), Vector(ypoints))
    
    # creating a matrix containing gauss sums
    matrix=[]
    lastRow=[]
    dimension=len(terms)
    terms+=["y"]
    for i in range(dimension):
        for j in range(dimension+1):
            lastRow.append(Expression(str( \
                Term(terms[i], xv, yv)* \
                Term(terms[j], xv, yv))))
        matrix.append(lastRow)
        lastRow = []
    terms.remove("y")
    
    # the last col of matrix is the picture
    picture = [m[-1] for m in matrix]
    # split the pic
    matrix = [m[:-1] for m in matrix]
    
    # returning the coefficients in float format
    return [float(str(b)) for b in Matrix(matrix).solve(picture)]

def approximatedFunction(terms, coefficients):
    """
    Return the approximated function as string.
    """
    
    approximation = ""
    for i in range(coefficients):
        if terms[i] != "const":
            approximation += "%s*%s + " % (str(coefficients[i]), terms[i])
        else:
            approximation += "%s + " % (str(coefficients[i]))
    return approximation[:-2]

""" stdin parsing """

def printApproximation(terms, measurePoints, matrix):
    dimension=len(terms)
    print "Approximationfunction:"
    approx = "f(x) = "
    for i in range(dimension):
        if terms[i] != "const":
            approx += "c%i*%s + " % (i, terms[i])
        else:
            approx += "c%i + " % (i)
    print approx[:-2]
    
    print "Measurements:"
    for p in measurePoints:
        print str(p)
    
    print "Coefficients:"
    for i in range(dimension):
        print "c%i = %s" % (i, str(matrix[i]))#[dimension]))
    
    print "Approximation:"
    approx = "f(x) = "
    for i in range(dimension):
        #if matrix[i][dimension].value[0] < 0 and i>0:
        #    approx = approx[:-2]
        if terms[i] != "const":
            approx += "%s*%s + " % (str(matrix[i]), terms[i])#[dimension]), terms[i])
        else:
            approx += "%s + " % (str(matrix[i]))#[dimension]))
    print approx[:-2]

def parseStdin():
    from sys import stdin
    
    def getRows(string):
        rows = string.split("\n")
        for i in range(len(rows)):
            rows[i] = rows[i].split(" ")
        return [row for row in rows if len(rows)>0]
    rows = getRows(stdin.read())
    terms = rows[0]
    
    mesurePoints = []
    for row in rows[1:]:
        mesurePoints.append((float(row[0]), float(row[1])))
    m = approximate(terms, mesurePoints)
    printApproximation(terms, mesurePoints, m)

if __name__ == "__main__":
    parseStdin()

