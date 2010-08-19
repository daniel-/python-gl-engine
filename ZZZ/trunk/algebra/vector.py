"""
----------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<daniel@orgizm.net> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Daniel Bessler
----------------------------------------------------------------------------
"""

from math import sqrt

class Vector(list):
    def __str__(self):
        """
        string representation.
        """
        return "(" + reduce(lambda x, y: str(x) + "," + str(y), self) + ")"
    
    def __add__(self, other):
        """
        add operator.
        @other: another Vector instance.
        """
        return Vector(map(lambda (x, y): x+y, zip(self, other)))
    
    def __sub__(self, other):
        """
        subtraction operator.
        @other: another Vector instance.
        """
        return Vector(map(lambda (x, y): x-y, zip(self, other)))
    
    def __mul__(self, other): # * operator
        """
        multiplication operator
        @other: another Vector instance or a scalar (int,float,..).
        """
        if issubclass(type(other), Vector):
            return map(lambda (x,y): x*y, zip(self, other))
        else:
            return map(lambda x: x*other, self)
    
    def __div__(self, other): # / operator
        """
        division operator.
        @other: another Vector instance or a scalar (int,float,..).
        """
        if issubclass(type(other), Vector):
            return map(lambda (x,y): x/y, zip(self, other))
        else:
            return map(lambda x: x/other, self)
    
    def scalar (self, other):
        """
        returns the scalar product of two vectors.
        @other: another Vector instance.
        """
        return sum(map(lambda (x, y): x*y, zip(self,other)))
    
    def norm (self):
        """
        returns the vector norm.
        """
        return sqrt(self.scalar(self))
    
    @staticmethod
    def orthonormal(vektoren):
        """
        procedure of Schmidt
        """
        
        orthonormalisiert = [vektoren[0]/vektoren[0].norm()]
        orthogonalisiert = [None]
        for i in range(1,len(vektoren)):
            orthogonalisiert.append(vektoren[i])
            for normal in orthonormalisiert:
                orthogonalisiert[i] -= normal*vektoren[i].skalar(normal)
            orthonormalisiert.append(orthogonalisiert[i]/orthogonalisiert[i].norm())
        return orthonormalisiert
