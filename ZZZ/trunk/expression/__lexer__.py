"""
----------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<daniel@orgizm.net> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Daniel Bessler
----------------------------------------------------------------------------
"""

from operator import add
from itertools import dropwhile

from functional.utils import spot

from __CONSTANTS__ import CONSTANTS
from __KEYWORDS__ import KEYWORDS

### TOKEN TYPES START ###

# baseclass for tokens
class Token(object):
    def __eq__(self, other):
        return str(self) == str(other)

# token containing a character
class TokChar(Token):
    def __init__(self, c):
        self.c = c
    def __str__(self):
        return str(self.c)

# value tokens
class TokNum(Token):
    def __init__(self, num):
        self.num = num
    def __str__(self):
        return str(self.num)
class TokVar(Token):
    def __init__(self, name, num=""):
        self.name = name
        self.num = num
    def __str__(self):
        return str(self.name) + str(self.num)

# keyword token
class TokKeyword(Token):
    def __init__(self, keyword):
        self.keyword = keyword
    def __str__(self):
        return self.keyword
    def getMethod(self):
        return KEYWORDS[self.keyword][0]
    def getAddFunc(self):
        return KEYWORDS[self.keyword][1]
    def getMulFunc(self):
        return KEYWORDS[self.keyword][2]
class TokBrace(Token):
    def __init__(self, arg):
        self.arg = arg
    def __str__(self):
        return "(" + str(map(str,self.arg)) + ")"

# constant token
class TokConstant(Token):
    def __init__(self, symbol):
        self.symbol = symbol
    def __str__(self):
        return self.symbol
    def getValue(self):
        return CONSTANTS[self.symbol]

### TOKEN TYPES STOP ###

def tokenize(string=""):
    """
    tokenizes a string, this never fails
    @param string: the input string
    @return: list of tokens
    """
    
    # nothing to tokenize
    if len(string) == 0:
        return []
    
    (x,xs) = (string[0], string[1:])
    if __isSpace__(x):
        # remove spaces
        return tokenize(list(dropwhile(__isSpace__, xs)))
    elif __isDigit__(x):
        # the first char is a digit, must be a number
        (inum, irest) = spot(xs, __isDigit__)
        (fnum, frest) = spot(irest[1:], __isDigit__)
        if len(irest) > 0 and irest[0] == '.':
            (num, rest) = (inum + ['.'] + fnum, frest)
        else:
            (num, rest) = (inum, irest)
        return [TokNum (reduce(add, [x]+num))] + tokenize(rest)
    elif x == "(":
        opened = 1
        rest = xs
        arg = [x]
        while opened != 0 and len(rest) != 0:
            (y,rest) = (rest[0], rest[1:])
            arg.append(y)
            if y == "(":
                opened += 1
            elif y == ")":
                opened -= 1
        if opened != 0:
            return [TokChar(x)] + tokenize(xs)
        else:
            return [TokBrace(tokenize(arg[1:-1]))] + tokenize(rest)
            
    elif __isAlpha__(x):
        # the first char is a alpha, must be a var or keyword
        (id, nrest) = spot(xs, __isAlpha__)
        tokenText = reduce(add, [x]+id)
        try:
            # try finding a matching keyword
            KEYWORDS[tokenText]
        except KeyError:
            try:
                # try finding a matching constant
                CONSTANTS[tokenText]
            except KeyError:
                # must be a var
                (num, rest) = spot(nrest, __isDigit__)
                if (len(num) == 0):
                    # without index
                    return [TokVar(reduce(add, [x]+id), "")]+tokenize(nrest)
                else:
                    # with index
                    return [TokVar(reduce(add, [x]+id), reduce(add, num))] + tokenize(rest)
            return [TokConstant(tokenText)] + tokenize(nrest)
        return [TokKeyword(tokenText)] + tokenize(nrest)
    else:
        # just tokenize a character
        return [TokChar(x)] + tokenize(xs)


# token checker for the parser
def isVarToken(token):
    return isinstance(token, TokVar)
def isNumToken(token):
    return isinstance(token, TokNum)
def isConstantToken(token):
    return isinstance(token, TokConstant)
def isKeywordToken(token):
    return isinstance(token, TokKeyword)
def isBraceToken(token):
    return isinstance(token, TokBrace)


# string checker for the lexer
def __isSpace__(s):
    return s.isspace();
def __isDigit__(s):
    return s.isdigit()
def __isAlpha__(s):
    return s.isalpha()
