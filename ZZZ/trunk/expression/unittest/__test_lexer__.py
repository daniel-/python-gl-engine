import unittest

from __lexer__ import tokenize

class TestLexer(unittest.TestCase):
    def testEmptyInput(self):
        self.assertEqual([],
                map(str, tokenize("")))
        self.assertEqual([],
                map(str, tokenize("  ")))
    def testNumber(self):
        self.assertEqual(["2"],
                map(str, tokenize("2")))
    def testFloat(self):
        self.assertEqual(["2.03"],
                map(str, tokenize("2.03")))
    def testVar(self):
        self.assertEqual(["a2"],
                map(str, tokenize("a2")))
    def testAdd(self):
        self.assertEqual(["2", "+", "3"],
                map(str, tokenize("2 + 3")))
    def testSub(self):
        self.assertEqual(["2", "-", "3"],
                map(str, tokenize("2 - 3")))
    def testTimes(self):
        self.assertEqual(["2", "*", "3"],
                map(str, tokenize("2 * 3")))
    def testDiv(self):
        self.assertEqual(["2", "/", "3"],
                map(str, tokenize("2 / 3")))
    def testConstants(self):
        self.assertEqual(["2", "^", "3"],
                map(str, tokenize("2 ^ 3")))
        self.assertEqual(["pi"],
                map(str, tokenize("pi")))
        self.assertEqual(["e"],
                map(str, tokenize("e")))
    def testGoldenRatio(self):
        self.assertEqual(["gold"],
                map(str, tokenize("gold")))
    def testSin(self):
        self.assertEqual(["sin", "(['a'])"],
                map(str, tokenize("sin(a)")))
    def testCos(self):
        self.assertEqual(["cos", "(['a'])"],
                map(str, tokenize("cos(a)")))
    def testTan(self):
        self.assertEqual(["tan", "(['a'])"],
                map(str, tokenize("tan(a)")))
    def testSqrt(self):
        self.assertEqual(["sqrt", "(['a'])"],
                map(str, tokenize("sqrt(a)")))

if __name__ == '__main__':
    unittest.main()
