import unittest

from __parser__ import parse
from __simplifier__ import Simplifier

def simplify(p):
    return Simplifier.simplify(p)

class TestSimplifier(unittest.TestCase):
    def testSum(self):
        self.assertEqual("3*a", str(simplify(parse("a+a+a"))))
        self.assertEqual("0", str(simplify(parse("a-a"))))
        self.assertEqual("3", str(simplify(parse("1+2"))))
        self.assertEqual("0", str(simplify(parse("2-2"))))
        self.assertEqual("b", str(simplify(parse("a+b-a"))))
        self.assertEqual("x*(3+y)", str(simplify(parse("x*y + 3*x"))))
        self.assertEqual("3*a+b", str(simplify(parse("a+b+a+a"))))
        self.assertEqual("-4", str(simplify(parse("-2-2"))))
        self.assertEqual("-70-33*a", str(simplify(parse("-67-3-a-32*a"))))
    
    def testProduct(self):
        self.assertEqual("a^3", str(simplify(parse("a*a*a"))))
        self.assertEqual("2", str(simplify(parse("1*2"))))
        self.assertEqual("6", str(simplify(parse("1*2*3"))))
        self.assertEqual("1", str(simplify(parse("2/2"))))
        self.assertEqual("b", str(simplify(parse("a*b/a"))))
        self.assertEqual("b", str(simplify(parse("a*b*c/a*c"))))
        self.assertEqual("b*(a-c)", str(simplify(parse("a*b - c*b"))))
        self.assertEqual("(a+b)*(c+d)", \
            str(simplify(parse("a*c + a*d + b*c + b*d"))))
        self.assertEqual("(a-b)*(c+d)", \
            str(simplify(parse("a*c + a*d - b*c - b*d"))))
        self.assertEqual("(a+b)*(c-d)", \
            str(simplify(parse("a*c - a*d + b*c - b*d"))))
        self.assertEqual("(a-b)*(c-d)", \
            str(simplify(parse("a*c - a*d - b*c + b*d"))))
    
    def testPow(self):
        self.assertEqual("(a*b)^m", str(simplify(parse("a^m * b^m"))))
        self.assertEqual("a^(m+n)", str(simplify(parse("a^m * a^n"))))
        self.assertEqual("a^(m-n)", str(simplify(parse("a^m / a^n"))))
        self.assertEqual("a^(m*n)", str(simplify(parse("(a^m)^n"))))
        self.assertEqual("(a/b)^m", str(simplify(parse("a^m / b^m"))))
    
    def testMod(self):
        self.assertEqual("2", str(simplify(parse("56 % 6"))))
        self.assertEqual("a%6", str(simplify(parse("a % 6"))))
        self.assertEqual("0", str(simplify(parse("(a*b) % (b*a)"))))
        self.assertRaises(ValueError, simplify, parse("fac(a % 1.5)"))
        
    def testBinom(self):
        self.assertEqual("(a+b)^2", str(simplify(parse("a^2 + 2*a*b + b^2"))))
        self.assertEqual("(3*a+2*b)^2", str(simplify(parse("9*a^2 + 12*a*b + 4*b^2"))))
        self.assertEqual("(a-b)^2", str(simplify(parse("a^2 - 2*a*b + b^2"))))
        self.assertEqual("(1.5*a-1.5*b)^2", str(simplify(parse("2.25*a^2 - 4.5*a*b + 2.25*b^2"))))
        self.assertEqual("a*b+(a+b)^2", str(simplify(parse("a^2 + 3*a*b + b^2"))))
        self.assertEqual("a^2-b^2", str(simplify(parse("(a+b)*(a-b)"))))
        
    def testKeyword(self):
        self.assertEqual("6", str(simplify(parse("fac(3)"))))
        self.assertEqual("fac(a)", str(simplify(parse("fac(a)"))))
        self.assertRaises(ValueError, simplify, parse("fac(3.5)"))
        self.assertEqual("sin(x)", str(simplify(parse("sin(x)"))))
        self.assertEqual("0", str(simplify(parse("sin(0)"))))
        self.assertEqual("978", str(simplify(parse("abs(978)"))))
        self.assertEqual("1", str(simplify(parse("abs(-1)"))))
        self.assertEqual("2", str(simplify(parse("sin(90) + sin(90)"))))
        self.assertEqual("6+fac(a)", str(simplify(parse("fac(3)+fac(a)"))))
        self.assertEqual("tan(x)", str(simplify(parse("sin(x)/cos(x)"))))
        self.assertEqual("1", str(simplify(parse("sin(x)^2 + cos(x)^2"))))
    
    def testNested(self):
        self.assertEqual("4*c", str(simplify(parse("4*(abs(-2) - 1)*c"))))
        self.assertEqual("6+c", str(simplify(parse("4 + (abs(-2) * 1) + c"))))

if __name__ == '__main__':
    unittest.main()
