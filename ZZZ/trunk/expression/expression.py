"""
----------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<daniel@orgizm.net> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Daniel Bessler
----------------------------------------------------------------------------
"""

from math import fabs

from __simplifier__ import Simplifier
from __absy__ import Expr, Number, Pow, Add, Sub, Times, Divide, UMinus, Modulo,\
    Keyword
from __parser__ import parse

def simplify(p):
    return Simplifier.simplify(p)

class Expression(object):
    """
    Class for handling math expressions from input strings.
    The input can contain simple numbers ( "1", "1.23", ..),
    variables ("a", "bc", ..) and some common operations
    with numbers and vars ("a + 2", "4.3 * b", "v ** r", "sin(v / r)", ..).
    The expressions can also be simplified with this class.
    """
    
    def __init__(self, inputString=None, parseResult=None, solve=True):
        """
        Creates an Expression object, optionally with input string
        or parse result.
        @param inputString: The input string, must be an math expression.
        @param parseResult: Parse result in absy.
        @param simplify: Should the expression get simplified?
        @raise ParseException: If the inputString does not match the Language.
        """
        
        """
        contains the current parse
        @note: not None
        """
        
        if parseResult!=None:
            # set parse result
            self.setParseResult(parseResult)
            if solve:
                self.solve()
        elif inputString!=None:
            # parse and set result
            self.setInputString(inputString)
            if solve:
                self.solve()
        else:
            self.parseResult = Expr()
    
    ### PUBLIC METHODS START ###
    
    def setInputString(self, inputString):
        """
        Sets the input String.
        @param inputString: The string, must be a math expression.
        @raise ParseException: If the inputString does not match the Language.
        """
        self.setParseResult(parse(inputString))
    
    def setParseResult(self, parseResult):
        """
        Sets the parse of the expression.
        @param parseResult: The parse result.
        """
        assert (parseResult != None)
        
        self.parseResult = parseResult
    
    def getParseResult(self):
        """
        Returns the parse result.
        @return: The parse result.
        """
        return self.parseResult
    
    def solve(self):
        """
        Simplifies the current parse result.
        """
        self.parseResult = simplify(self.parseResult)
    
    ### PUBLIC METHODS STOP ###
    
    ### PRIVATE METHODS START ###
    
    def __op__(self, other, op):
        ret = Expression()
        if isinstance(other, Expression):
            ret.setParseResult(op(self.getParseResult(), other.getParseResult()))
        elif isinstance(other, Expr):
            ret.setParseResult(op(self.getParseResult(), other))
        elif isinstance(other, int):
            ret.setParseResult(op(self.getParseResult(), Number(other)))
        elif isinstance(other, float):
            ret.setParseResult(op(self.getParseResult(), Number(other)))
        else:
            ret.setParseResult(op(self.getParseResult(), parse(str(other))))
        ret.solve()
        return ret
    
    ### PRIVATE METHODS STOP ###
    
    ### 'object' IMPLEMENTATIONS ###
    
    def __copy__(self):
        ret = Expression()
        ret.setInput(self.getParseResult())
        return ret
    
    def __str__(self):
        return str(self.getParseResult())
    
    ### MATH OPERATOR IMPLEMENTATIONS ###
    
    def __pow__(self, other):
        """
        implements '**' operator.
        """
        return self.__op__(other, Pow)
    
    def __add__(self, other):
        """
        implements '+' operator.
        """
        return self.__op__(other, Add)
    
    def __sub__(self, other):
        """
        implements '-' operator.
        """
        return self.__op__(other, Sub)
    
    def __mul__(self, other):
        """
        implements '*' operator.
        """
        return self.__op__(other, Times)
    
    def __div__(self, other):
        """
        implements '/' operator.
        """
        return self.__op__(other, Divide)
    
    def __mod__(self, other):
        """
        implements '%' operator.
        """
        return self.__op__(other, Modulo)
    
    def __abs__(self):
        """
        Return the absolute value of the Expression.
        """
        return Expression(inputString=None, \
            parseResult=Keyword("abs", self.getParseResult(), fabs, None, None), \
            solve=False)
    
    def __neg__(self):
        """
        Negates Expression.
        """
        ret = Expression()
        ret.setInput(UMinus(self.getParseResult()))
        return ret
    
    ### COMPARISON OPERATOR IMPLEMENTATIONS ###
    
    def __eq__(self, other):
        """
        implements '==' operator.
        """
        if isinstance(other, Expression):
            return self.parseResult.__eq__(other.parseResult)
        else:
            return False
    
    def __ne__(self, other):
        """
        implements '!=' operator.
        """
        return not (self == other)
