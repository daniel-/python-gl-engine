"""
----------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<daniel@orgizm.net> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Daniel Bessler
----------------------------------------------------------------------------
"""

from functional.utils import spot_eq

from __lexer__ import tokenize, isKeywordToken, isBraceToken, isNumToken,\
    isVarToken, isConstantToken
from __absy__ import Expr, Keyword, Number, Variable, Constant, Pow, Times,\
    Divide, Modulo, UMinus, Add, Sub, Operator

class ParseError(Exception):
    """
    Parse Error for invalid Syntax.
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "Invalid Syntax: " + repr(self.value)

### PUBLIC METHODS START ###

def parse(string):
    """
    Parses one string into the abstract syntax.
    @param string: The input string.
    @return: Parse result as Expr.
    @raise ParseError: Thrown if input does not match the language.
    """
    
    # get tokens
    tokens = tokenize(string)
    if len(tokens) == 0:
        # empty string is valid
        return Expr()
    else:
        # parse tokens
        return __pExpr__(tokens)

### PUBLIC METHODS STOP ###

### PRIVATE METHODS START ###

def __pBracesToggle__(parsed, state):
    """
    Set braces toggle state if input is a operator.
    """
    if isinstance(parsed, Operator):
        parsed.braces = state
    return parsed

def __pFactor__(tokens):
    """
    Parses a single token
    """
    l = len(tokens)
    if isKeywordToken(tokens[0]):
        if l != 2:
            raise ParseError("Wrong number of keyword arguments " + str(map(str,tokens)))
        elif not isBraceToken(tokens[1]):
            raise ParseError("Wrong keyword argument " + str(tokens[1]))
        else:
            return Keyword(tokens[0].keyword,\
                        __pExpr__(tokens[1].arg),\
                        tokens[0].getMethod(),
                        tokens[0].getAddFunc(),
                        tokens[0].getMulFunc())
    elif l != 1:
        raise ParseError("Cant parse " + str(map(str,tokens)))
    elif isNumToken(tokens[0]):
        return Number(tokens[0].num)
    elif isVarToken(tokens[0]):
        return Variable(tokens[0].name, tokens[0].num)
    elif isConstantToken(tokens[0]):
        return Constant(str(tokens[0]), tokens[0].getValue())
    elif isBraceToken(tokens[0]):
        return __pExpr__(tokens[0].arg)
    else:
        raise ParseError("Cant parse " + str(tokens[0]))

def __pPow__(tokens):
    """
    parses '^' operator.
    """
    
    (x,xs) = spot_eq(tokens, ["^"])
    if len(xs) != 0:
        return Pow(__pFactor__(x), __pPow__(xs[1:]))
    return __pFactor__(tokens)

def __pTerm__(tokens):
    """
    parses '*' and '/' operator.
    """
    
    (x,xs) = spot_eq(tokens, ["*", "/", "%"])
    if len(xs) != 0:
        if len(x) == 0:
            raise ParseError("No left argument for "+str(xs[0])+" operator in " + str(map(str,tokens)))
        if str(xs[0]) == "*":
            return Times(__pPow__(x), \
                         __pTerm__(xs[1:]))
        elif str(xs[0]) == "/":
            return Divide(__pPow__(x), \
                          __pTerm__(xs[1:]))
        else:
            return Modulo(__pPow__(x), \
                          __pTerm__(xs[1:]))
    return __pPow__(tokens)

def __pExpr__(tokens):
    """
    parses '+' and '-' operator.
    """
    
    # collect summands
    summandTokens = []
    currentSummand = []
    for token in tokens:
        if str(token) == "+" or str(token) == "-":
            if len(currentSummand) == 0:
                if token != tokens[0]:
                    raise ParseError("Cant parse tokens " + str(map(str, tokens)))
            else:
                summandTokens.append(currentSummand)
            summandTokens.append(token)
            currentSummand = []
        else:
            currentSummand.append(token)
    if len(currentSummand) != 0:
        summandTokens.append(currentSummand)
    
    if str(summandTokens[0]) == "-":
        lastExp = UMinus(__pTerm__(summandTokens[1]))
        summandTokens = summandTokens[2:]
    else:
        lastExp = __pTerm__(summandTokens[0])
        summandTokens = summandTokens[1:]
    for i in range(len(summandTokens)):
        if str(summandTokens[i]) == "+":
            lastExp = Add(lastExp, __pTerm__(summandTokens[i+1]))
        elif str(summandTokens[i]) == "-":
            lastExp = Sub(lastExp, __pTerm__(summandTokens[i+1]))
    
    return lastExp

### PRIVATE METHODS STOP ###
