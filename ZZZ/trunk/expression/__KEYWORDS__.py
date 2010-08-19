"""
----------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<daniel@orgizm.net> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Daniel Bessler
----------------------------------------------------------------------------
"""

from operator import mul
from math import sin, cos, tan, fabs, radians, log, hypot, trunc
from __absy__ import isKeyword, UMinus, Keyword, Pow, Number

def factorial(n):
    if isinstance(n, float):
        if n.is_integer():
            n = int(n)
    if not isinstance(n, int):
        raise ValueError("factorial needs int argument")
    return reduce(mul, range(1, n+1), 1)

# sine simplifications, both args expected to be pows
def add_sine(e1, e2):
    if isKeyword(e1.expr1) and isKeyword(e2.expr1):
        keyword1 = e1.expr1.keyword
        keyword2 = e2.expr1.keyword
        if keyword1=="sin" and keyword2=="cos" and\
           e1.expr1.expr.__eq__(e2.expr1.expr) and\
           Number(2.0)==e2.expr2==e1.expr2:
            # sin^2(x) + cos^2(x) = 1
            return Number(1.0)
def mul_sine(e1, e2):
    if isKeyword(e1.expr1) and isKeyword(e2.expr1):
        keyword1 = e1.expr1.keyword
        keyword2 = e2.expr1.keyword
        if keyword1=="sin" and keyword2=="cos" and\
           e1.expr1.expr.__eq__(e2.expr1.expr) and\
           e2.expr2.__eq__(UMinus(e1.expr2)):
            # sin/cos = tan
            return Pow(Keyword("tan", e1.expr1.expr,
                           e1.expr1.method, e1.expr1.add, e1.expr1.mul), e1.expr2)

# language keywords
KEYWORDS={
    "sin":     (lambda x : sin(radians(x)), add_sine, mul_sine),
    "cos":     (lambda x : cos(radians(x)), add_sine, mul_sine),
    "tan":     (lambda x : tan(radians(x)), add_sine, mul_sine),
    "int":     (int, None, None),
    "float":   (float, None, None),
    "abs":     (fabs, None, None),
    "log":     (log, None, None),
    "hypot":   (hypot, None, None),
    "fac":     (factorial, None, None),
    "round":   (round, None, None),
    "trunc":   (trunc, None, None)
}
