"""
----------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<daniel@orgizm.net> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Daniel Bessler
----------------------------------------------------------------------------
"""

from itertools import takewhile

def spot(l, func):
    """
    Splits a list into two parts where func returns True.
    @param l: Input list
    @param func: Function that takes one list element and returns a boolean
    """
    match = list(takewhile(func, l))
    return (match, l[len(match):])

def spot_eq(l, needles):
    """
    Splits a list into two parts at first needle occurance.
    @param l: Input list
    @param needle: needle to search for
    """
    match = list(takewhile(lambda x: str(x) not in needles, l))
    return (match, l[len(match):])

def concatList(l, startValue=[]):
    """
    concatenates elements of a list.
    @param l: Input list
    @param startValue: Startvalue of reduction, default empty list.
    @return: concatenated list
    """
    return reduce(lambda x,y: x + y, l, startValue)
