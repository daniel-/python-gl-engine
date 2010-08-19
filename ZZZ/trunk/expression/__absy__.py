"""
----------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<daniel@orgizm.net> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Daniel Bessler
----------------------------------------------------------------------------
"""

from sys import maxint
from fractions import gcd

### data types ###

class Expr(object):
    """
    Baseclass for math expressions.
    """
    def __str__(self):
        return ""
    def __eq__(self, other):
        """
        compares string representation.
        """
        return str(self) == str(other)
    def __len__(self):
        """
        counts number of expressions.
        default: count one for self.
        """
        return 1
    def level(self):
        """
        list of expressions in the level of this expression.
        default: list with self.
        """
        return [self]
    def degree(self):
        """
        maximal degree in the expression (for comparing).
        default: zero degree.
        """
        return 0
    def chars(self):
        """
        sum of all character of the expression (for comparing).
        default: zero character.
        """
        return 0
    def sort(self):
        """
        sorts a expression by comparing the level items.
        default: already sorted.
        """
        return self
def isExpr(exp):
    return isinstance(exp, Expr)

### VALUE CLASSES ####

class Number(Expr):
    """
    A numerical value.
    """
    def __init__(self, num):
        self.num = float(num)
    def __str__(self):
        if self.num.is_integer():
            return str(int(self.num))
        else:
            return str(self.num)
def isNumber(exp):
    return isinstance(exp, Number)

class Constant(Number):
    """
    Class for constants like pi.
    """
    def __init__(self, symbol, value):
        Number.__init__(self, value)
        self.symbol = symbol
    def __str__(self):
        return str(self.symbol)
def isConstant(exp):
    return isinstance(exp, Constant)

class Variable(Expr):
    """
    A variable value.
    """
    def __init__(self, name, index=""):
        self.name = name
        self.index = index
    def __str__(self):
        return str(self.name) + str(self.index)
    def degree(self):
        return 1
    def chars(self):
        return sum( map(ord, self.name) )
def isVariable(exp):
    return isinstance(exp, Variable)

### KEYWORDS ###
    
class Keyword(Expr):
    """
    Baseclass for keywords.
    """
    def __init__(self, keyword, expr, method, add, mul):
        self.keyword = keyword
        self.expr = expr
        self.method = method
        if add==None:
            self.add = lambda x,y: None
        else: self.add = add
        if mul==None:
            self.mul = lambda x,y: None
        else: self.mul = mul
    def __len__(self):
        return 1 + len(self.expr)
    def __str__(self):
        return self.keyword + "(" + str(self.expr) + ")"
    def degree(self):
        return self.expr.degree()
    def sort(self):
        return self.__class__(self.keyword, self.expr.sort(),
                              self.method, self.add, self.mul)
    def chars(self):
        return self.expr.chars()
def isKeyword(exp):
    return isinstance(exp, Keyword)

### ABSTRACT BASECLASSES ###

class Operator(Expr):
    """
    Baseclass for operators.
    """
    def __init__(self, expr1, expr2,
                 primaryClass, secondaryClass=None,
                 inverseClass=None):
        self.expr1 = expr1
        self.expr2 = expr2
        self.primaryClass = primaryClass
        self.secondaryClass = secondaryClass
        self.inverseClass = inverseClass
    def __len__(self):
        return 1 + len(self.expr1) + len(self.expr2)
    def degree(self):
        return max(self.expr1.degree(),
                   self.expr2.degree())
    def level(self):
        def arg_level(arg):
            if isOperator(arg):
                if isinstance(arg, self.primaryClass):
                    return arg_level(arg.expr1) + arg_level(arg.expr2)
                elif self.secondaryClass!=None and isinstance(arg, self.secondaryClass):
                    return arg_level(arg.expr1) +\
                            map(self.inverseClass, arg_level(arg.expr2))
                else:
                    return [arg]
            else:
                return [arg]
        return arg_level(self)
    def chars(self):
        return self.expr1.chars() + self.expr2.chars()
    @staticmethod
    def neutral_number():
        return None
def isOperator(exp):
    return isinstance(exp, Operator)

class Inverse(Expr):
    """
    Baseclass for the inverse operation.
    """
    def __init__(self, expr):
        self.expr = expr
    def __len__(self):
        return 1 + len(self.expr)
    def degree(self):
        return self.expr.degree()
    def sort(self):
        return self.__class__(self.expr.sort())
    def level(self):
        return map(self.__class__, self.expr.level())
    def chars(self):
        return self.expr.chars()
    @staticmethod
    def to_inverse(exp, inverseClass):
        if isNumber(exp):
            return Number(inverseClass.inverse_number(float(exp.num)))
        elif isinstance(exp, inverseClass):
            return exp.expr
        else:
            return inverseClass(exp)
def isInverse(exp):
    return isinstance(exp, Inverse)

### OPERATOR CLASSES ###

class Add(Operator):
    """
    '+' operator.
    """
    def __init__(self, expr1, expr2):
        Operator.__init__(self, expr1, expr2,
                 primaryClass=Add, secondaryClass=Sub,
                 inverseClass=UMinus)
    def __str__(self):
        if isUMinus(self.expr2):
            arg = "-" + str(self.expr2.expr)
        else:
            arg = "+" + str(self.expr2)
        return str(self.expr1) + arg
    def sort(self):
        args = map(lambda x: x.sort(), self.level())
        args.sort(compare_expressions)
        return parse_level(
            args,
            self.primaryClass,
            self.secondaryClass,
            isUMinus)
    @staticmethod
    def neutral_number():
        return Number(0.0)
def isAdd(exp):
    return isinstance(exp, Add)
 
class Sub(Operator):
    """
    '-' operator.
    """
    def __init__(self, expr1, expr2):
        Operator.__init__(self, expr1, expr2,
                 primaryClass=Add, secondaryClass=Sub,
                 inverseClass=UMinus)
    def __str__(self):
        return str(self.expr1) + "-" + str(self.expr2)
def isSub(exp):
    return isinstance(exp, Sub)

class Times(Operator):
    """
    '*' operator.
    """
    def __init__(self, expr1, expr2):
        Operator.__init__(self, expr1, expr2,
                 primaryClass=Times, secondaryClass=Divide,
                 inverseClass=UFactor)
    def __str__(self):
        def expr_str(expr):
            if isinstance(expr, Add) or isinstance(expr, Sub) or isinstance(expr, UMinus):
                return "(" + str(expr) + ")"
            else:
                return str(expr)
        return expr_str(self.expr1) + "*" + expr_str(self.expr2)
    def sort(self):
        args = map(lambda x: x.sort(), self.level())
        args.sort(compare_expressions)
        return parse_level(
            args,
            self.primaryClass,
            self.secondaryClass,
            isUFactor)
    @staticmethod
    def neutral_number():
        return Number(1.0)
def isTimes(exp):
    return isinstance(exp, Times)

class Divide(Operator):
    """
    '/' operator.
    """
    def __init__(self, expr1, expr2):
        Operator.__init__(self, expr1, expr2,
                 primaryClass=Times, secondaryClass=Divide,
                 inverseClass=UFactor)
    def __str__(self):
        def expr_str(expr):
            if isinstance(expr, Add) or isinstance(expr, Sub) or isinstance(expr, UMinus):
                return "(" + str(expr) + ")"
            else:
                return str(expr)
        return expr_str(self.expr1) + "/" + expr_str(self.expr2)
def isDivide(exp):
    return isinstance(exp, Divide)

class Modulo(Operator):
    """
    '%' operator.
    """
    def __init__(self, expr1, expr2):
        Operator.__init__(self, expr1, expr2,
                 primaryClass=Modulo, secondaryClass=None,
                 inverseClass=None)
    def __str__(self):
        def expr_str(expr):
            if ((isinstance(expr, Add) or isinstance(expr, Sub)) and not expr.braces) or isinstance(expr, UMinus):
                return "(" + str(expr) + ")"
            else:
                return str(expr)
        return expr_str(self.expr1) + "%" + expr_str(self.expr2)
def isModulo(exp):
    return isinstance(exp, Modulo)

class Pow(Operator):
    """
    '**' operator.
    """
    def __init__(self, expr1, expr2):
        Operator.__init__(self, expr1, expr2,
                 primaryClass=Pow, secondaryClass=None,
                 inverseClass=None)
    def __str__(self):
        def expr_str(expr):
            if isinstance(expr, Operator):
                return "(" + str(expr) + ")"
            else:
                return str(expr)
        return expr_str(self.expr1) + "^" + expr_str(self.expr2)
    def degree(self):
        if isNumber(self.expr2):
            return float(self.expr2.num)
        else:
            return float(maxint)
    def chars(self):
        return self.expr1.chars()
    @staticmethod
    def neutral_number():
        return None
def isPow(exp):
    return isinstance(exp, Pow)

### INVERSE ELEMENTS ###

class UMinus(Inverse):
    """
    Additive inverse.
    """
    def __init__(self, expr):
        Inverse.__init__(self, expr)
    def __str__(self):
        return "-" + str(self.expr)
    @staticmethod
    def inverse_number(num):
        return -num
    @staticmethod
    def neutral_number(num):
        return 0.0
def isUMinus(exp):
    return isinstance(exp, UMinus)

class UFactor(Inverse):
    """
    Multiplicative inverse.
    """
    def __init__(self, expr):
        Inverse.__init__(self, expr)
    def __str__(self):
        if isinstance(self.expr, Operator):
            return "1 / (" + str(self.expr) + ")"
        else:
            return "1 / " + str(self.expr)
    @staticmethod
    def inverse_number(num):
        return 1.0/num
    @staticmethod
    def neutral_number(num):
        return 1.0
def isUFactor(exp):
    return isinstance(exp, UFactor)


### operations on data types ###


# extract equal factors from two levels
def equal_factors(level1, level2):
    level2_u = filter(lambda x: not isNumber(x), level2)
    ret=[]
    for e1 in level1:
        if isNumber(e1): continue
        e1_minus = isUMinus(e1)
        if e1_minus: e1 = e1.expr
        for e2 in level2_u:
            e2_minus = isUMinus(e2)
            if e2_minus: e2 = e2.expr
            if e1.__eq__(e2):
                ret.append(e1)
            elif e1.expr1.__eq__(e2.expr1):
                if isNumber(e1.expr2):
                    if isNumber(e2.expr2):
                        ret.append(Pow(e1.expr1, Number(
                                min(e1.expr2.num, e2.expr2.num))))
                    else:
                        ret.append(Pow(e1.expr1, Add(e2.expr2,
                                Number(-e1.expr2.num))))
                elif isNumber(e2.expr2):
                    ret.append(Pow(e1.expr1, Add(e1.expr2,
                            Number(-e2.expr2.num))))
                else:
                    ret.append(Pow(e1.expr1, Add(e1.expr2,
                            UMinus(e2.expr2))))
    
    # return equal factor with gcd
    return (ret, round(gcd(mul_nums(level1).num,
                           mul_nums(level2).num), 3))

# extract number from +/* level
def add_nums(level):
    return reduce(
            lambda x,y: Number(x.num+y.num),
            filter(isNumber, level), Number(0.0))
def mul_nums(level):
    return reduce(
            lambda x,y: Number(x.num*y.num),
            filter(isNumber, level), Number(1.0))

# compare for sorting
def compare_expressions(e1, e2):
    (deg1, deg2) = (e1.degree(), e2.degree())
    if deg1!=deg2:
        return cmp(deg1,deg2)
    else:
        return cmp(e1.chars(),e2.chars())

# get level of e, force level of type c.primaryClass
def get_level(e, c):
    if isOperator(e) and e.primaryClass == c:
        return e.level()
    else:
        return [e]
def parse_level(args, primaryClass, secondaryClass, checkInverse):
    if len(args) == 0:
        return Number(0)
    
    lastExp = args[0]
    i = 1
    while i<len(args):
        n = primaryClass.neutral_number()
        if n != None and args[i].__eq__(n):
            i+=1
            continue
        elif n != None and lastExp.__eq__(n):
            lastExp = args[i]
        elif checkInverse(args[i]):
            # inverseClass -> secondaryClass
            lastExp = secondaryClass(lastExp, args[i].expr)
        elif secondaryClass!=None and isNumber(args[i]) and float(args[i].num) < 0:
            # x+(-n) -> x-n
            lastExp = secondaryClass(lastExp, Number(-float(args[i].num)))
        else:
            lastExp = primaryClass(lastExp, args[i])
        i+=1
    return lastExp

# recursively convert vars/keywords to pow and vice versa
def to_pow(x):
    if isPow(x) or isNumber(x):
        return x
    elif isOperator(x):
        return x.__class__(to_pow(x.expr1), to_pow(x.expr2))
    elif isInverse(x):
        return x.__class__(to_pow(x.expr))
    elif isKeyword(x):
        return Pow(x.__class__(x.keyword, to_pow(x.expr),
                               x.method, x.add, x.mul), Number(1.0))
    else:
        return Pow(x, Number(1.0))
def from_pow(x):
    if isPow(x):
        if Number(1.0) == x.expr2:
            return from_pow(x.expr1)
        elif Number(0.0) == x.expr2:
            return Number(1.0)
        else:
            return Pow(from_pow(x.expr1), from_pow(x.expr2))
    elif isOperator(x):
        return x.__class__(from_pow(x.expr1), from_pow(x.expr2))
    elif isInverse(x):
        return x.__class__(from_pow(x.expr))
    elif isKeyword(x):
        return x.__class__(x.keyword, from_pow(x.expr),
                           x.method, x.add, x.mul)
    return x

# convert expression from/to UFactor
def from_ufactor(e):
    if isUFactor(e):
        if isUFactor(e.expr):
            return e.expr.expr
        elif isPow(e.expr):
            return Pow(e.expr.expr1, Inverse.to_inverse(e.expr.expr2, UMinus))
        elif isNumber(e.expr):
            return Number(1.0/e.expr.num)
        else:
            return Pow(e.expr, Number(-1.0))
    else:
        return e
def to_ufactor(e):
    if isPow(e):
        if isNumber(e.expr2):
            if e.expr2.num == -1.0:
                return UFactor(e.expr1)
            elif e.expr2.num < 0.0:
                return UFactor(Pow(e.expr1, Number(-e.expr2.num)))
            else:
                return e
        elif isUMinus(e.expr2):
            return UFactor(Pow(e.expr1, e.expr2.expr))
        else:
            return e
    else:
        return e

# convert expression to not use/use UMinus
def from_uminus(e):
    if isUMinus(e):
        if isUMinus(e.expr):
            return from_uminus(e.expr.expr)
        else:
            return Times(Number(-1.0), e.expr)
    elif isOperator(e):
        return e.__class__(from_uminus(e.expr1), from_uminus(e.expr2))
    else:
        return e
def to_uminus(e):
    if isTimes(e):
        level = e.level()
        new_level = []
        new_num = Number(1.0)
        for arg in level:
            if isNumber(arg):
                new_num = Number(new_num.num * arg.num)
            elif isUMinus(arg):
                new_num = Number(-new_num.num)
                new_level.append(arg.expr)
            else:
                new_level.append(arg)
        if new_num.num == -1.0:
            return UMinus(parse_level(new_level, Times, Divide, isUFactor))
        elif new_num.num == 1.0:
            return parse_level(new_level, Times, Divide, isUFactor)
        elif new_num.num == 0.0:
            return Number(0.0)
        elif new_num.num < 0.0:
            return UMinus(parse_level([Number(-new_num.num)] + new_level, Times, Divide, isUFactor))
        else:
            return parse_level([new_num] + new_level, Times, Divide, isUFactor)
    else:
        return e

# apply UMinus to an expression
def apply_uminus_add_level(e):
    return parse_level(map(lambda x: Inverse.to_inverse(x, UMinus),
                get_level(e, Add)), Add, Sub, isUMinus)

