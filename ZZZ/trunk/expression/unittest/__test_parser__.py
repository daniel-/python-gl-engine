import unittest

from __parser__ import parse, ParseError

class TestParser(unittest.TestCase):
    ### SIMPLE TESTS ###
    def testEmptyInput(self):
        self.assertEqual("", str(parse("")))
        self.assertEqual("", str(parse("  ")))
    def testNumber(self):
        self.assertEqual("2", str(parse("2")))
    def testFloat(self):
        self.assertEqual("2.03", str(parse("2.03")))
    def testVar(self):
        self.assertEqual("a2", str(parse("a2")))
    def testAdd(self):
        self.assertEqual("a+a+a", str(parse("a + a + a")))
        self.assertEqual("2+3", str(parse("2 + 3")))
    def testSub(self):
        self.assertEqual("2-3", str(parse("2 - 3")))
    def testTimes(self):
        self.assertEqual("2*3", str(parse("2 * 3")))
        self.assertEqual("2*3*4", str(parse("2 * 3 * 4")))
        self.assertEqual("sin(a^2+2*a*b+b^2)*c^2", str(parse("sin(a^2+2*a*b+b^2)*c^2")))
        self.assertEqual("sin(a^2+2*a*b+b^2)^2", str(parse("sin(a^2+2*a*b+b^2)^2")))
    def testDiv(self):
        self.assertEqual("2/3", str(parse("2 / 3")))
    def testModulo(self):
        self.assertEqual("2%3", str(parse("2 % 3")))
        self.assertEqual("a%3", str(parse("a % 3")))
        self.assertEqual("2%3+2", str(parse("2 % 3+2")))
        self.assertEqual("2%(3+2)", str(parse("2 % (3+2)")))
    def testPow(self):
        self.assertEqual("2^3", str(parse("2 ^ 3")))
    def testFactorial(self):
        self.assertEqual("fac(3)", str(parse("fac(3)")))
        self.assertEqual("fac(a)+b", str(parse("fac(a)+b")))
    def testConstants(self):
        self.assertEqual("pi", str(parse("pi")))
        self.assertEqual("e", str(parse("e")))
        self.assertEqual("gold", str(parse("gold")))
    def testSin(self):
        self.assertEqual("sin(a0)", str(parse("sin(a0)")))
    def testCos(self):
        self.assertEqual("cos(a0)", str(parse("cos(a0)")))
    def testTan(self):
        self.assertEqual("tan(a0)", str(parse("tan(a0)")))
    def testUMinus(self):
        self.assertEqual("-(2+3)-5", str(parse("-(2+3)-5")))
        self.assertEqual("-2-3", str(parse("-2 - 3")))
    ### COMPLEX TESTS ###
    def testOp(self):
        self.assertEqual("a+b+a", str(parse("a + b + a")))
        self.assertEqual("a*b+d", str(parse("a * b + d")))
        self.assertEqual("a^b+d", str(parse("a ^ b + d")))
        self.assertEqual("a^b*d", str(parse("a ^ b * d")))
        self.assertEqual("a*b*c/a*c", str(parse("a*b*c/a*c")))
    def testBraces(self):
        self.assertEqual("a*(b+a)", str(parse("a * (b + a)")))
        self.assertEqual("(b+a)*a", str(parse("(b + a) * a")))
        self.assertEqual("b+a", str(parse("(b + a)")))
        self.assertEqual("3+8*8+2", str(parse("3+((8*((((((8))))))))+2")))
        self.assertEqual("(b+a)*(b-a)", str(parse("(b + a) * (b - a)")))
        self.assertEqual("(a^m)^n", str(parse("(a^m)^n")))
    def testKeywords(self):
        self.assertEqual("pi*a+b", str(parse("pi * a + b")))
        self.assertEqual("sin(b+a)", str(parse("sin(b + a)")))
        self.assertEqual("tan(b*a)", str(parse("tan(b * a)")))
        self.assertEqual("a*sin(b+a)+c", str(parse("a*sin(b + a)+c")))
        self.assertEqual("abs(x)^2+2*abs(x)*abs(y)+abs(y)^2", \
                str(parse("abs(x)^2 + 2*abs(x)*abs(y) + abs(y)^2")))
    def testFails(self):
        self.assertRaises(ParseError, parse, "x0x")
        self.assertRaises(ParseError, parse, "&")
        self.assertRaises(ParseError, parse, "#")
        self.assertRaises(ParseError, parse, "1++1")
        self.assertRaises(ParseError, parse, "*1-1")
        self.assertRaises(ParseError, parse, "(1+1")

if __name__ == '__main__':
    unittest.main()
