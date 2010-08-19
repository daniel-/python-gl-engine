"""
----------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<daniel@orgizm.net> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Daniel Bessler
----------------------------------------------------------------------------
"""

from math import sqrt

from functional.utils import concatList
from __absy__ import isExpr, to_pow, from_pow, isConstant, isNumber, isVariable,\
    isInverse, isOperator, isKeyword, Expr, from_uminus, add_nums, Number, mul_nums,\
    Times, Divide, isUFactor, parse_level, Add, equal_factors, UMinus, apply_uminus_add_level,\
    to_uminus, isUMinus, Sub, from_ufactor, isPow, Pow, UFactor, to_ufactor, Modulo,\
    Keyword, get_level, Inverse, isTimes, isAdd, isSub
    
def unique_seq(seq):
    # make sequence unique
    # .. not order preserving
    keys = {}
    for e in seq:
        keys[str(e)] = e
    return keys.values()

def list_combinations(l):
    # get all combinations of items in the second list level
    # for example [[0,1], [0]] -> [[0,0], [1,0]]
    return reduce(lambda a,b: [ i + [y]
                for y in b for i in a ], l, [[]])

class Simplifier(object):
    """
    Simplifier is able to simplify expressions, doing some common tasks
    to make a expression nicer to look at.
    The class does not always find the optimal solution, but does a good job ;)
    """
    
    ### HELPER START ###
    
    @staticmethod
    def multiplyBraces(parseResult):
        if isTimes(parseResult):
            timesLevel = parseResult.level()
            addArgs = filter(lambda x: isAdd(x) or isSub(x), timesLevel)
            if len(timesLevel) == len(addArgs):
                products = map(lambda x: [x], addArgs[0].level())
                addArgs = addArgs[1:]
            else:
                products = [filter(lambda x: not (isAdd(x) or isSub(x)), timesLevel)]
            for addArg in addArgs:
                addLevel = addArg.level()
                newProducts = []
                for product in products:
                    newProducts += map(lambda x: [x] + product, addLevel)
                products = newProducts
            
            multiplicated = parse_level(map(lambda y: parse_level(y,
                        Times, Divide, isUFactor), products),
                        Add, Sub, isUMinus)
            multiplicated = from_uminus(multiplicated)
            
            return multiplicated
        elif isOperator(parseResult):
            return parseResult.__class__(
                        Simplifier.multiplyBraces(parseResult.expr1),
                        Simplifier.multiplyBraces(parseResult.expr2))
        else:
            return parseResult
    
    @staticmethod
    def simplify(parseResult):
        """
        Simplifies a expression.
        @param parseResult: input expression.
        @return: simplified expression.
        TODO: stop after n seconds?
        """
        assert isExpr(parseResult)
        
        parseResult = to_pow(Simplifier.multiplyBraces(parseResult))
        
        simplifier = Simplifier()
        simple = Simplifier.chooseExpr( map(from_pow,
                    simplifier.doSimplify(parseResult)))
        del simplifier
        
        # return sorted/simplified result
        return simple.sort()
    
    @staticmethod
    def chooseExpr(exprs):
        """
        Choose simplest result.
        Where simple is defined by expression length and number of subexpressions.
        @param exprs: list of expressions.
        @return: simplest expression.
        """
        simplestResult = exprs[0]
        count = len(simplestResult)
        bestl = []
        
        for res in exprs[1:]:
            eCount = len(res)
            if eCount == count:
                # choose shorter result
                if len(str(res)) < len(str(simplestResult)):
                    eCount = count
                    simplestResult = res
                    bestl = res.level()
                elif len(str(res)) == len(str(simplestResult)):
                    # choose result with less expressions in the top layer
                    resl = res.level()
                    if len(resl)>len(bestl):
                        bestl = resl
                        eCount = count
                        simplestResult = res
            elif eCount < count:
                # choose result with less expressions
                count = eCount
                simplestResult = res
                bestl = res.level()
        
        return simplestResult
    
    ### HELPER STOP ###
    
    def __init__(self):
        self.simplifyCache = {}
        
        self.opSimplifier = {
              Add: self.__simplify_add__
            , Sub: self.__simplify_sub__
            , Times: self.__simplify_times__
            , Divide: self.__simplify_div__
            , Modulo: self.__simplify_modulo__
            , Pow: self.__simplify_pow__
        }
    
    def doSimplify(self, parseResult):
        """
        Main simplify methods, handles all simplifications
        @param parseResult: Parse result to simplify
        @return: List of all possible simplifications
        """
        
        parseResult = parseResult.sort()
        
        try:
            return self.simplifyCache[str(parseResult)]
        except:
            pass
        
        # add result to cache and return it
        def __do_simplify__(result):
            result = unique_seq(result)
            self.simplifyCache[str(parseResult)] = result
            return result
        
        if isNumber(parseResult) or isVariable(parseResult) or isConstant(parseResult):
            # can't simplify more
            return __do_simplify__([parseResult])
        elif isInverse(parseResult):
            # simplify without inverse
            return map(lambda x: Inverse.to_inverse(x, parseResult.__class__),
                          self.doSimplify(parseResult.expr))
        elif isOperator(parseResult):
            # simplify args and afterwards op
            return __do_simplify__(
                        self.opSimplifier[parseResult.__class__](parseResult))
        elif isKeyword(parseResult):
            # simplify keyword on result of simplified keyword arg
            return __do_simplify__(concatList(map(
                        lambda x: self.__simplify_keyword__(parseResult, x),
                        self.doSimplify(parseResult.expr)
                )))
        elif parseResult.__class__ == Expr:
            # eval empty expression
            return __do_simplify__([])
        else:
            # not a expression?
            raise Exception("Unknown datatype: " + str(parseResult.__class__))
    
    def __simplify_add_simple__(self, add_level):
        # simplify added numbers
        add_num = add_nums(add_level)
        
        # remove numbers from level, convert everything else to pow
        add_level = filter(lambda x: not isNumber(x), add_level)
        
        if len(add_level)==0:
            return (add_num, add_level, [add_num])
        # simplify args with same base/exponent
        max = len(add_level); i=0
        while i<max:
            argi   = Times(Number(1.0),add_level[i])
            leveli = argi.level()
            numi   = mul_nums(leveli)
            leveli = filter(lambda x: not isNumber(x), leveli)
            faci = parse_level(leveli, Times, Divide, isUFactor)
            j = i+1
            while j<max:
                argj   = Times(Number(1.0), add_level[j])
                levelj = argj.level()
                numj   = mul_nums(levelj)
                levelj = filter(lambda x: not isNumber(x), levelj)
                facj = parse_level(levelj, Times, Divide, isUFactor)
                
                if isTimes(argi) and Number(1.0) == argi.expr1 and\
                   isTimes(argj) and Number(1.0) == argj.expr1:
                    karg1 = argi.expr2
                    karg2 = argj.expr2
                    if isKeyword(karg1.expr1):
                        keyword_arg = karg1.expr1.add(karg1, karg2)
                    elif isKeyword(karg2.expr1):
                        keyword_arg = karg2.expr1.add(karg2, karg1)
                    else:
                        keyword_arg = None
                if keyword_arg==None:
                    if len(leveli)==0 and len(levelj)==0:
                        argi = Number(numi.num + numj.num)
                    elif len(leveli)==0 or len(levelj)==0:
                        j += 1
                        continue
                    elif faci.__eq__(facj):
                        # n*b + m*b = (n+m)*b
                        if numi.num + numj.num == 0.0:
                            argi = None
                        else:
                            numi = Number(numi.num + numj.num)
                            argi = Times(numi,
                                         parse_level(leveli, Times, Divide, isUFactor))
                    else:
                        j += 1
                        continue
                else: argi = keyword_arg
                # remove arg at i/j and add argi to pos i
                add_level.pop(i)
                add_level.insert(i, argi)
                add_level.pop(j)
                max -= 1
            i += 1
        add_level = filter(lambda x: x!=None, add_level)
        
        if len(add_level)==0:
            # simplified to number
            add_level = [Number(0.0)]
        if len(add_level)==1:
            # only one summand and number left
            args = add_level[0]
            if Number(0.0) == add_num:
                return (add_num, add_level, self.doSimplify(args))
            elif isNumber(args):
                return (add_num, add_level, [Number(add_num.num + args.num)])
            else:
                simple = self.doSimplify(args)
                nums = filter(isNumber, simple)
                if len(nums)==0:
                    return (add_num, add_level, map(lambda x: Add(add_num, x), simple))
                else:
                    return (add_num, add_level, [Number(add_num.num + nums[0].num)])
        return (add_num, add_level, None)
    def __simplify_add__(self, addArg):
        (add_num, add_level, simple) = self.__simplify_add_simple__(
                            map(from_uminus, (to_pow(addArg)).level()))
        if simple != None:
            simple_levels = map(lambda x: (Add(Number(0.0), x)).level(), simple)
            return map(lambda x: parse_level(map(to_uminus, x),
                                Add, Sub, isUMinus), simple_levels)
        
        # simplified return list
        ret = []
        # simplified summands
        times_exprs = map(lambda x: self.doSimplify(x), add_level)
        # level with head of simplified summands
        add_level = map(lambda e: e[0], times_exprs)
        combinations = list_combinations(map(lambda x: range(len(x)), times_exprs))
        # for all possible combinations of simplified summands
        for indexes in combinations:
            # add level containing simplified args
            (level_num, level, simple) = self.__simplify_add_simple__([add_num] +
                            map(lambda (i,e): e[i], zip(indexes, times_exprs)))
            
            if simple != None:
                simple_levels = map(lambda x: (Add(Number(0.0), x)).level(), simple)
                return map(lambda x: parse_level(map(to_uminus, x),
                                        Add, Sub, isUMinus), simple_levels)
            elif level_num.num != 0.0: level = [level_num] + level
            
            level_levels = map(lambda x: Times(Number(1.0), x).level(), level)
            
            # get equal factors in summands
            equal_factors_list = []
            for i in range(len(level)):
                time_level1 = level_levels[i]
                factors = [[]]*len(level)
                gcds = [0]*len(level)
                for j in range(i) + range(i+1, len(level)):
                    time_level2 = level_levels[j]
                    (factors[j], gcds[j]) = equal_factors(time_level1, time_level2)
                equal_factors_list.append((factors, gcds))
            
            # try excluding factors from each summand,
            # where the rest will be simplified again
            excluded_factors = {} # remember excluded factors
            for (l,gcds) in equal_factors_list:
                # break if something was simplified.... much faster
                # might break some simplifications, but tests are running ;)
                if len(ret) != 0: break
                # exclude factors from l
                for i in range(len(l)):
                    fac = l[i]
                    
                    if len(ret) != 0: break
                    if len(fac) == 0: continue
                    
                    fac_str = str(map(str, fac))
                    try:
                        excluded_factors[fac_str]
                        # factor excluded before
                        continue
                    except:
                        excluded_factors[fac_str] = None
                    
                    # expression that will be excluded
                    exclude_exp = parse_level(fac, Times, Divide, isUFactor)
                    if abs(gcds[i])==1.0 or gcds[i]==0.0:
                        exclude_exp_gcd = None
                    else:
                        exclude_exp_gcd = Times(Number(gcds[i]), exclude_exp)
                    # summands that will be multiplicated by the excluded expression
                    include_exps = []
                    # summands that can not be simplified with this step
                    unused_exps = []
                    
                    # for each simplified arg do
                    for summand in level:
                        summand_level = get_level(summand, Times)
                        match = False
                        # a exclude_factor must occur in the summand level
                        for exclude_factor in fac:
                            for j in range(len(summand_level)):
                                summand_factor = summand_level[j]
                                if isNumber(summand_factor):
                                    continue
                                elif not summand_factor.expr1.__eq__(exclude_factor.expr1):
                                    continue
                                else:
                                    if summand_factor.expr2.__eq__(exclude_factor.expr2):
                                        exponent = Number(0.0)
                                    elif isNumber(exclude_factor.expr2) and\
                                       isNumber(summand_factor.expr2):
                                        exponent = Number(summand_factor.expr2.num - exclude_factor.expr2.num)
                                    else:
                                        exponent = Add(summand_factor.expr2, UMinus(exclude_factor.expr2))
                                    if Number(0.0) == exponent:
                                        include = Number(1.0)
                                    elif Number(1.0) == exponent:
                                        include = exclude_factor.expr1
                                    else:
                                        include = Pow(exclude_factor.expr1, exponent)
                                    summand_level.pop(j)
                                    summand_level.insert(j, include)
                                    match = True
                                    break
                        if len(summand_level)==0:
                            summand_level = [Number(1.0)]
                        if match:
                            summand_num = mul_nums(summand_level)
                            summand_level = [summand_num] + filter(lambda x: not isNumber(x), summand_level)
                            include_exps.append(parse_level(summand_level, Times, Divide, isUFactor))
                        else:
                            unused_exps.append(summand)
                    
                    include_exps = map(to_uminus, include_exps)
                    simplify_data = [(exclude_exp, include_exps, unused_exps)]
                    # can exclude numerical factor ?
                    if exclude_exp_gcd != None:
                        # levels of included summands
                        include_levels = map(lambda x: x.level(), include_exps)
                        # included nums divided by gcd
                        include_nums = map(lambda x: Number(x.num/gcds[i]),
                                   map(mul_nums, include_levels))
                        # remove numbers from level
                        include_levels = map(lambda x: filter(
                                                lambda y: not isNumber(y), x), include_levels)
                        # and add calculated nums
                        for j in range(len(include_levels)):
                            include_level = include_levels.pop(j)
                            include_level_num = include_nums[j]
                            if include_level_num.num == 0.0:
                                include_levels.insert(j, include_level_num)
                            elif include_level_num.num == 1.0:
                                exp = parse_level(include_level,
                                            Times, Divide, isUFactor)
                                include_levels.insert(j, exp)
                            else:
                                include_level = [include_level_num] + include_level
                                exp = parse_level(include_level,
                                            Times, Divide, isUFactor)
                                include_levels.insert(j, exp)
                        simplify_data.append(
                            (exclude_exp_gcd, include_levels, unused_exps))
                    
                    for (exclude, include, unused) in simplify_data:
                        include_exp = parse_level(include, Add, Sub, isUMinus)
                        if len(unused)==0:
                            # exclude * include_exp and (-exclude) * (-include_exp)
                            ret += map(lambda x: Times(exclude, x),
                                       self.doSimplify(include_exp))
                            ret += map(lambda x: Times(UMinus(exclude), x),
                                       self.doSimplify(apply_uminus_add_level(include_exp)))
                        else:
                            # exclude * include_exp + unused_exp and
                            # (-exclude) * (-include_exp) + unused_exp
                            unused_exp = parse_level(unused, Add, Sub, isUMinus)
                            simple_excluded = map(lambda x: Times(exclude, x),
                                                  self.doSimplify(include_exp))
                            ret += concatList(map(lambda x:
                                        self.doSimplify(Add(x, unused_exp)),
                                        simple_excluded))
                            simple_excluded = map(lambda x: Times(UMinus(exclude), x),
                                                  self.doSimplify(apply_uminus_add_level(include_exp)))
                            ret += concatList(map(lambda x:
                                        self.doSimplify(Add(x, unused_exp)),
                                        simple_excluded))
            
            # get summands with only ^2 arguments and
            # a numerical value n with a 'nice' sqrt(n) value.
            pow_two_exprs = []
            num_pow_two = 0
            for l in level_levels:
                l_num = mul_nums(l)
                if l_num.num<=0.0:
                    pow_two_exprs.append([])
                elif (sqrt(l_num.num)*1000.0).is_integer():
                    l_exprs = filter(lambda e: not isNumber(e), l)
                    if len(filter(lambda e: not Number(2.0).__eq__(e.expr2), l_exprs)) > 0:
                        pow_two_exprs.append([])
                    else:
                        pow_two_exprs.append([l_num] + l_exprs)
                        num_pow_two += 1
                else:
                    pow_two_exprs.append([])
            
            # is there are at least 2 summands with power 2
            if num_pow_two>1:
                def to_sqrt(e):
                    if isNumber(e): return Number(sqrt(e.num))
                    else:           return Pow(e.expr1, Number(e.expr2.num/2.0))
                binom_expr = None
                max = len(pow_two_exprs)
                # do for all summands
                for i in range(max):
                    leveli = pow_two_exprs[i]
                    if len(leveli)==0:
                        continue
                    # summand with power 2
                    include_leveli = map(to_sqrt, leveli)
                    include_argi = parse_level(include_leveli, Times, Divide, isUFactor)
                    j = i+1
                    # do for following summands
                    while j<max:
                        levelj = pow_two_exprs[j]
                        j += 1
                        if len(levelj)==0:
                            continue
                        # summand with power 2
                        include_levelj = map(to_sqrt, levelj)
                        include_argj = parse_level(include_levelj, Times, Divide, isUFactor)
                        
                        (wanted_numk, wanted_levelk, wanted_argk) = \
                            self.__simplify_times_simple__([Number(2.0)] + include_leveli + include_levelj)
                        if wanted_argk==None:
                            wanted_argk = parse_level([wanted_numk] + wanted_levelk, Times, Divide, isUFactor)
                        
                        # try finding 2*sqrt(argi)*sqrt(argj)
                        for k in range(max):
                            if k==i or k==j-1: continue
                            levelk = level_levels[k]
                            argk = parse_level(levelk, Times, Divide, isUFactor)
                            
                            if isUMinus(to_uminus(argk)):
                                operator = Sub
                                rest = self.simplify(Add(argk, wanted_argk))
                            else:
                                operator = Add
                                rest = self.simplify(Sub(argk, wanted_argk))
                            if isSub(rest) or isAdd(rest):
                                continue
                            rest = from_uminus(to_pow(rest))
                            
                            binom = Pow(operator(include_argi, include_argj), Number(2.0))
                            binom_level = level[:]
                            ind_list = [i,j-1,k]; ind_list.sort(); ind_list.reverse()
                            for ind in ind_list:
                                binom_level.pop(ind)
                            binom_level.append(binom)
                            if rest != Number(0.0):
                                binom_level.append(rest)
                            binom_expr = parse_level(binom_level,
                                        Add, Sub, isUMinus)
                        
                        if binom_expr!=None: break
                    if binom_expr!=None: break
                if binom_expr!=None:
                    ret.append(binom_expr)
        
        # result without exclusion
        ret.append(parse_level(map(to_uminus, add_level), Add, Sub, isUMinus))
        # add number summand
        if add_num.num != 0.0:
            ret = map(lambda x: Add(x, add_num), ret)
        
        return ret
    def __simplify_sub__(self, subArg):
        # wrap to __simplify_add__
        return self.__simplify_add__(Add(subArg.expr1, UMinus(subArg.expr2)))
    
    def __simplify_times_simple__(self, times_level):
        times_num = mul_nums(times_level)
        times_level = filter(lambda x: not isNumber(x), times_level)
        
        if times_num.num == 0.0:
            return (times_num, times_level, [Number(0.0)])
        if len(times_level)==0:
            return (times_num, times_level, [times_num])
        
        # simplify args with same base
        max = len(times_level); i=0
        while i<max:
            argi = times_level[i]
            if not isPow(argi):
                i += 1
                continue
            j = i+1
            while j<max:
                argj = times_level[j]
                if not isPow(argj):
                    j += 1
                    continue
                
                if isKeyword(argi.expr1):
                    keyword_arg = argi.expr1.mul(argi, argj)
                elif isKeyword(argj.expr1):
                    keyword_arg = argj.expr1.mul(argj, argi)
                else:
                    keyword_arg = None
                
                if keyword_arg== None:
                    one_potencei = Number(1.0)==argi.expr2 or Number(-1.0)==argi.expr2
                    one_potencej = Number(1.0)==argj.expr2 or Number(-1.0)==argj.expr2
                    
                    if argi.expr1.__eq__(argj.expr1):
                        simple = self.doSimplify(Add(argi.expr2, argj.expr2))[0]
                        if Number(0.0) == simple:
                            times_level.pop(j)
                            times_level.pop(i)
                            max -= 2
                            i -= 1
                            break
                        else:
                            argi = Pow(argi.expr1, simple)
                    elif one_potencei and one_potencej:
                        j += 1
                        continue
                    elif argi.expr2.__eq__(argj.expr2):
                        argi = Pow(self.doSimplify(Times(argi.expr1, argj.expr1))[0],
                                   argi.expr2)
                    elif argi.expr2.__eq__(UMinus(argj.expr2)):
                        argi = Pow(Divide(argj.expr1, argi.expr1), argj.expr2)
                    elif argj.expr2.__eq__(UMinus(argi.expr2)):
                        argi = Pow(Divide(argi.expr1, argj.expr1), argi.expr2)
                    else:
                        j += 1
                        continue
                else:
                    argi = keyword_arg
                # simplify argi/argj
                times_level.pop(i)
                times_level.insert(i, argi)
                times_level.pop(j)
                max -= 1
            i += 1
        if len(times_level)==1:
            args = times_level[0]
            if Number(1.0) == times_num:
                return (times_num, times_level, self.doSimplify(args))
            elif isNumber(args):
                return (times_num, times_level, [Number(times_num.num * args.num)])
            else:
                simple = self.doSimplify(args)
                nums = filter(isNumber, simple)
                if len(nums)==0:
                    return (times_num, times_level, map(lambda x: Times(times_num, x), simple))
                else:
                    return (times_num, times_level, [Number(times_num.num * nums[0].num)])
        return (times_num, times_level, None)
    def __simplify_times__(self, timesArg):
        (times_num, times_level, simple) = self.__simplify_times_simple__(
                            map(from_ufactor, (to_pow(timesArg)).level()))
        if simple!=None: return simple
        
        # simplify factors
        ret = []
        add_exprs = map(lambda x: self.doSimplify(x), times_level)
        times_level = map(lambda e: e[0], add_exprs)
        combinations = list_combinations(map(lambda x: range(len(x)), add_exprs))
        for indexes in combinations:
            level = map(lambda (i,e): e[i], zip(indexes, add_exprs))
            # maybe now simple simplifiable?
            (simple_num, simple_level, simple) = self.__simplify_times_simple__(
                                            [times_num] + map(to_ufactor, level))
            if simple==None:
                ret.append(parse_level([simple_num] + simple_level, Times, Divide, isUFactor))
            else:
                return simple
        ret.append(parse_level([times_num] + map(to_ufactor, times_level),
                        Times, Divide, isUFactor))
        
        return ret
    def __simplify_div__(self, divArg):
        level2 = map(UFactor,
            get_level(divArg.expr2, Times))
        
        # wrap to __simplify_times__
        return self.__simplify_times__(Times(divArg.expr1,
                            parse_level(level2, Times, Divide, isUFactor)))

    
    def __simplify_modulo__(self, moduloArg):
        def getNum(exp):
            if isNumber(exp):
                num = float(exp.num)
                if not num.is_integer():
                    raise ValueError("mod needs int arguments: " + str(moduloArg))
            else:
                num = None
            return num
        
        # do for all combinations of mod argument simplifications
        simple = map(self.doSimplify, moduloArg.level())
        combinations = list_combinations(map(lambda x: range(len(x)), simple))
        for indexes in combinations:
            # get simplified level and parse moduloArg again
            level = map(lambda (i,e): e[i], zip(indexes, simple))
            moduloArg = parse_level(level, Modulo, None, lambda x: False)
            
            if moduloArg.expr1.__eq__(moduloArg.expr2):
                # e % e = 0
                return [Number(0.0)]
            
            # calc mod with int numbers
            num1 = getNum(moduloArg.expr1)
            num2 = getNum(moduloArg.expr2)
            if num1==None or num2==None:
                return [moduloArg]
            else:
                return [Number(int(num1) % int(num2))]
    
    def __simplify_pow__(self, powArg):
        ret = []
        # do for all combinations of pow argument simplifications
        simple = map(self.doSimplify, powArg.level())
        combinations = list_combinations(map(lambda x: range(len(x)), simple))
        for indexes in combinations:
            # get simplified level and parse powArg again
            level = map(lambda (i,e): e[i], zip(indexes, simple))
            powArg = parse_level(level, Pow, None, lambda x: False)
            
            if isPow(powArg.expr1):
                # (a^n)^m = a^(n*m)
                exps = self.doSimplify(Times(powArg.expr1.expr2, powArg.expr2))
                ret2 = []
                for exp in exps:
                    ret2 += self.doSimplify((Pow(powArg.expr1.expr1, exp)))
                if len(ret2) == 0:
                    ret.append(Pow(powArg.expr1.expr1,
                                   Times(powArg.expr1.expr2, powArg.expr2)))
                else: ret += ret2
            elif Number(0.0) == powArg.expr2:
                ret.append(Number(0.0))
            elif isNumber(powArg.expr1) and isNumber(powArg.expr2):
                ret.append(Number(powArg.expr1.num ** powArg.expr2.num))
            else:
                ret.append(powArg)
        return ret
    
    def __simplify_keyword__(self, keyword, expr):
        # keywords can be evaluated with a numerical value only
        if isNumber(expr):
            return [Number(keyword.method(float(expr.num)))]
        else:
            return [Keyword(keyword.keyword, expr,
                            keyword.method, keyword.add, keyword.mul)]
