import unittest

import sys, os
parentPath = os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
if not parentPath in sys.path:
    sys.path.insert(0, parentPath)

from utils import *

class TestUtils(unittest.TestCase):
    def testSpot(self):
        self.assertEqual((['b'], ['c', 'a']), spot(['b', 'c', 'a'], (lambda x: x!='c')))
        self.assertEqual(([], ['b', 'c', 'a']), spot(['b', 'c', 'a'], (lambda x: x=='z')))
        self.assertEqual((['b', 'c', 'a'], []), spot(['b', 'c', 'a'], (lambda x: x!='z')))
    
    def testSpotEq(self):
        self.assertEqual(([], ['b', 'c', 'a']), spot_eq(['b', 'c', 'a'], ['b']))
        self.assertEqual((['b'], ['c', 'a']), spot_eq(['b', 'c', 'a'], ['c']))
        self.assertEqual((['b', 'c'], ['a']), spot_eq(['b', 'c', 'a'], ['a']))
        self.assertEqual((['b', 'c', 'a'], []), spot_eq(['b', 'c', 'a'], ['z']))
        self.assertEqual(([], ['b', 'c', 'a']), spot_eq(['b', 'c', 'a'], ['c', 'b']))
    
    def testConcatList(self):
        self.assertEqual([], concatList([]))
        self.assertEqual([1], concatList([[1]]))
        self.assertEqual([1,2], concatList([[1],[2]]))
        self.assertEqual([1,3,5,2,4,6], concatList([[1,3,5],[2,4,6]]))
        self.assertEqual("aaabbb", concatList(["aaa","bbb"], ""))

if __name__ == '__main__':
    unittest.main()
