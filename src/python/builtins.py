from basetype import SimpleTypeFunc, CustomTypeFunc, BuiltinTypeClass, LibClass, LibFunc, makeFuncSpec, makeFuncProto
import operator
import ast
import logging
import parser

class IntegerTimesFunc(LibFunc):
    def __init__(self, cls):
        argtype = makeFuncSpec(ast.makePrimitiveType('void'), [cls.createType()])
        super(IntegerTimesFunc, self).__init__(cls, makeFuncProto('times', ast.makePrimitiveType('void'), [argtype]))
    def evaluateCall(self, visitor, callinfo):
        # visitor.logger.debug('IntegerTimesFunc.evaluateCall entry start', (self, callinfo))
        callinfo.args[0].evaluateParam(visitor)
        callerval = callinfo.caller.object.visit(visitor)
        assert len(callinfo.args) == 1, (callinfo.args, callinfo.caller)
        visitor.implicit_args_stack.insert(0, [])
        for i in range(callerval):
            visitor.pushScope()
            visitor.implicit_args_stack[0] = [i]
            # visitor.logger.debug('IntegerTimesFunc.evaluateCall item', i)
            callinfo.args[0].visit(visitor)
            visitor.popScope()
        # visitor.logger.debug('IntegerTimesFunc.evaluateCall entry end', (self, callinfo))
        del visitor.implicit_args_stack[0]
        return None


class IntegerParse(LibFunc):
    def __init__(self, cls):
        protostr = 'parse(string, %s) => %s' % (cls.name, cls.name)
        LibFunc.__init__(self, cls, protostr)

class IntegerToString(LibFunc):
    def __init__(self, cls):
        LibFunc.__init__(self, cls, 'toString() => string')

class IntegerClass(BuiltinTypeClass):
    def __init__(self, name):
        BuiltinTypeClass.__init__(self)
        self.name = name
        self.addDef(IntegerParse(self))
        self.addDef(IntegerToString(self))
        self.addDef(IntegerTimesFunc(self))
        self.ops = {'==' : operator.eq, '>':operator.gt, '!=':operator.ne,
        '<':operator.lt, '>=':operator.ge, '<=':operator.le, 
        '+':operator.add,'-':operator.sub,'*':operator.mul,'/':operator.div,'%':operator.mod}
    def getType(self):
        return self
    def getTarget(self):
        return self
    def createType(self):
        return ast.makePrimitiveType(self.name)
    def evaluateNil(self, visitor):
        return 0
    def evaluateBinaryOp(self, visitor, opstr, left, right):
        left = left.visit(visitor)
        right = right.visit(visitor)
        # visitor.logger.debug('IntegerClass.evaluateBinaryOp', opstr, left, right)
        op = self.ops[opstr]
        return op(left, right)
    def evaluateUnaryOp(self, visitor, opstr, left):
        # visitor.logger.debug('IntegerClass.evaluateUnaryOp', opstr, left)
        assert opstr == '-'
        return operator.neg(left)
    def eval_parse(self, caller, s, defval):
        # assert caller is None, (self, caller, s, defval)
        # print('eval_parse', caller, s, defval)
        return int(s)

class FloatingClass(BuiltinTypeClass):
    def __init__(self, name):
        super(FloatingClass, self).__init__()
        self.name = name
        self.ops = {'==' : operator.eq, '>':operator.gt, '!=':operator.ne,
        '<':operator.lt, '>=':operator.ge, '<=':operator.le, 
        '+':operator.add,'-':operator.sub,'*':operator.mul,'/':operator.div,'%':operator.mod}
    def evaluateNil(self, visitor):
        return 0.0
    def evaluateBinaryOp(self, visitor, opstr, left, right):
        left = left.visit(visitor)
        right = right.visit(visitor)
        # visitor.logger.debug('FloatingClass.evaluateBinaryOp', opstr, left, right)
        op = self.ops[opstr]
        return op(left, right)
    def evaluateUnaryOp(self, visitor, opstr, left):
        # visitor.logger.debug('FloatingClass.evaluateUnaryOp', opstr, left)
        assert opstr == '-'
        return operator.neg(left)

class SimpleTypeClass(BuiltinTypeClass):
    def __init__(self, name):
        BuiltinTypeClass.__init__(self)
        self.name = name

class CharClass(SimpleTypeClass):
    def __init__(self):
        SimpleTypeClass.__init__(self, 'char')
        self.addDef(CustomTypeFunc(self, 'upper() => char'))
        self.addDef(CustomTypeFunc(self, 'lower() => char'))
        self.addDef(CustomTypeFunc(self, 'isUpper() => bool'))
        self.addDef(CustomTypeFunc(self, 'isLower() => bool'))
        self.ops = {'==' : operator.eq, '>':operator.gt, '!=':operator.ne,
        '<':operator.lt, '>=':operator.ge, '<=':operator.le, 
        '+':operator.add,'-':operator.sub,'*':operator.mul,'/':operator.div,'%':operator.mod}
    def evaluateBinaryOp(self, visitor, opstr, left, right):
        # visitor.logger.debug('CharClass.evaluateBinaryOp', opstr, left, right)
        left = left.visit(visitor)
        right = right.visit(visitor)
        op = self.ops[opstr]
        return op(left, right)
    def eval_upper(self, ch):
        return ch.upper()
    def eval_lower(self, ch):
        return ch.lower()
    def eval_isUpper(self, ch):
        return ch.isupper()
    def eval_isLower(self, ch):
        return ch.islower()
    def evaluateNil(self, visitor):
        return 0

class BoolClass(SimpleTypeClass):
    def __init__(self):
        SimpleTypeClass.__init__(self, 'bool')
        self.ops = {'and':operator.and_, 'or':operator.or_}
    def evaluateUnaryOp(self, visitor, opstr, left):
        # visitor.logger.debug('BoolClass.evaluateUnaryOp', opstr, left)
        assert opstr == 'not'
        return not left
    def evaluateBinaryOp(self, visitor, opstr, left, right):
        # visitor.logger.debug('BoolClass.evaluateBinaryOp', opstr, left, right)
        assert opstr in ['and', 'or']
        left = left.visit(visitor)
        op = self.ops[opstr]
        if opstr == 'and':
            if not left:
                return False
            return op(left, right.visit(visitor))
        if left:
            return True
        return op(left, right.visit(visitor))
    def evaluateNil(self, visitor):
        return False

class VoidClass(SimpleTypeClass):
    def __init__(self):
        SimpleTypeClass.__init__(self, 'void')
        self.name = 'void'

class NilClass(SimpleTypeClass):
    def __init__(self):
        SimpleTypeClass.__init__(self, 'nil')
        self.name = 'nil'

class ClassInfo(BuiltinTypeClass):
    def __init__(self):
        super(ClassInfo, self).__init__()
        self.name = 'Class'
        self.addDef(CustomTypeFunc(self, 'getName() => string'))


class GenericDictEachFunc(LibFunc):
    def __init__(self, cls):
        argtype = makeFuncSpec(ast.makePrimitiveType('void'), [cls.createKeyType(), cls.createValueType()])
        super(GenericDictEachFunc, self).__init__(cls, makeFuncProto('each', ast.makePrimitiveType('void'), [argtype]))
    def evaluateCall(self, visitor, callinfo):
        # visitor.logger.debug('DictEachFunc.evaluateCall entry start', self, callinfo)
        assert len(callinfo.args) == 1, (callinfo.caller.object, callinfo.args)
        assert isinstance(callinfo.args[0], ast.Closure), (callinfo, callinfo.getOwnerFunc())
        callinfo.args[0].evaluateParam(visitor)
        coll = callinfo.caller.object.visit(visitor)
        # visitor.logger.debug('DictEachFunc.evaluateCall coll', self, callinfo, coll, coll.keys())
        visitor.implicit_args_stack.insert(0, [])
        for key, val in coll.iteritems():
            visitor.pushScope()
            visitor.implicit_args_stack[0] = [key, val]
            # visitor.logger.debug('DictEachFunc.evaluateCall key val', key, val, callinfo)
            callinfo.args[0].visit(visitor)
            visitor.popScope()
        # visitor.logger.debug('DictEachFunc.evaluateCall entry end', self, callinfo)
        del visitor.implicit_args_stack[0]
        return None

class GenericClass(BuiltinTypeClass):
    def __init__(self, name, impl):
        super(GenericClass, self).__init__()
        self.name = name
        self.impl = impl
        self.genericParams = impl.genericParams
        self.instantiator = ast.GenericInstantiator(impl.genericParams)
        self.astFieldNames = ['genericParams']
    def instantiate(self, genericArgs, visitor):
        realGenericArgs = self.instantiator.getRealArgs(genericArgs)
        cls = self.instantiator.find(realGenericArgs)
        if cls:
            # visitor.logger.debug('GenericClass.instantiate existing', self.name, self, genericArgs, realTypeArgs, cls.genericArgs)
            return cls
        cls = self.impl(realGenericArgs)
        # visitor.logger.debug('GenericClass.instantiate new', self.name, self, realGenericArgs, cls.genericArgs)
        self.instantiator.cache(cls)
        visitor.setupNewItem(cls, self, True)
        return cls

class GenericClassImpl(BuiltinTypeClass):
    def __init__(self, genericParams, genericArgs):
        BuiltinTypeClass.__init__(self)
        self.instantiation = ast.GenericInstantiation(genericParams, genericArgs)
        # self.astFieldNames = ['funcs']
    def cacheName(self, visitor):
        self.doVisitChildren(visitor)
    def findLocalSymbol(self, name):
        # print('GenericClassImpl.findLocalSymbol', name, self)
        ret = self.instantiation.findLocalSymbol(name)
        # print('GenericClassImpl.findLocalSymbol result', name, self, gt)
        return ret if ret else BuiltinTypeClass.findLocalSymbol(self, name)

class GenericDictClassImpl(GenericClassImpl):
    genericParams = [ast.GenericTypeParam('KeyType'), ast.GenericTypeParam('ValueType')]
    def __init__(self, genericArgs):
        super(GenericDictClassImpl, self).__init__(GenericDictClassImpl.genericParams, genericArgs)
        self.addDef(SimpleTypeFunc(self, 'size() => int', evaluator=len))
        self.addDef(SimpleTypeFunc(self, 'clear()', evaluator=lambda d:d.clear()))
        self.addDef(CustomTypeFunc(self, makeFuncProto('get', self.createValueType(), [self.createKeyType(), self.createValueType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('set', ast.makePrimitiveType('void'), [self.createKeyType(), self.createValueType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('add', ast.makePrimitiveType('void'), [self.createKeyType(), self.createValueType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('remove', ast.makePrimitiveType('void'), [self.createKeyType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('contains', ast.makePrimitiveType('bool'), [self.createKeyType()])))
        self.addDef(GenericDictEachFunc(self))
    def getItemType(self):
        return self.instantiation.genericArgs[1].type.getRealType()
    def getKeyType(self):
        return self.instantiation.genericArgs[0].type.getRealType()
    def getValueType(self):
        return self.instantiation.genericArgs[1].type.getRealType()
    def createKeyType(self):
        return ast.UserType(['KeyType'])
    def createValueType(self):
        return ast.UserType(['ValueType'])
    def eval_get(self, coll, key, defval=None):
        # print('DictClass.eval_get', coll, key, defval)
        return coll.get(key, defval)
    def eval_set(self, coll, key, item):
        # assert False, (self, coll, item)
        # print('DictClass.eval_set', self, coll, key, item)
        assert key is not None, (self, coll, key, item)
        # assert isinstance(key, str), (self, coll, key, item)
        # assert False, (self, coll, key, item)
        coll[key] = item
        return None
    def evaluateNil(self, visitor):
        return {}
    def eval_contains(self, coll, key):
        return key in coll
    def eval_not_contains(self, coll, key):
        return key not in coll


class GenericSetEachFunc(LibFunc):
    def __init__(self, cls):
        argtype = makeFuncSpec(ast.makePrimitiveType('void'), [cls.createElementType(), ast.makePrimitiveType('int')])
        super(GenericSetEachFunc, self).__init__(cls, makeFuncProto('each', ast.makePrimitiveType('void'), [argtype]))
    def evaluateCall(self, visitor, callinfo):
        # visitor.logger.debug('SetEachFunc.evaluateCall entry start', self, callinfo)
        assert len(callinfo.args) == 1, (callinfo.caller.object, callinfo.args)
        assert isinstance(callinfo.args[0], ast.Closure), (callinfo, callinfo.getOwnerFunc())
        callinfo.args[0].evaluateParam(visitor)
        coll = callinfo.caller.object.visit(visitor)
        # visitor.logger.debug('SetEachFunc.evaluateCall coll', self, callinfo, coll, coll.keys())
        visitor.implicit_args_stack.insert(0, [])
        i = 0
        for item in coll:
            visitor.pushScope()
            visitor.implicit_args_stack[0] = [item, i]
            # visitor.logger.debug('SetEachFunc.evaluateCall key val', key, val, callinfo)
            callinfo.args[0].visit(visitor)
            i += 1
            visitor.popScope()
        # visitor.logger.debug('SetEachFunc.evaluateCall entry end', self, callinfo)
        del visitor.implicit_args_stack[0]
        return None

class GenericSetClassImpl(GenericClassImpl):
    genericParams = [ast.GenericTypeParam('ElementType')]
    def __init__(self, genericArgs):
        super(GenericSetClassImpl, self).__init__(GenericSetClassImpl.genericParams, genericArgs)
        self.addDef(SimpleTypeFunc(self, 'size() => int'))
        self.addDef(SimpleTypeFunc(self, 'clear()'))
        self.addDef(CustomTypeFunc(self, makeFuncProto('add', ast.makePrimitiveType('void'), [self.createElementType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('remove', ast.makePrimitiveType('void'), [self.createElementType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('contains', ast.makePrimitiveType('bool'), [self.createElementType()])))
        self.addDef(GenericSetEachFunc(self))
    def createElementType(self):
        return ast.UserType(['ElementType'])
    def evaluateNil(self, visitor):
        return set()
    def eval_add(self, coll, key):
        coll.add(key)
    def eval_remove(self, coll, key):
        coll.remove(key)
    def eval_size(self, coll):
        return len(coll)
    def eval_contains(self, coll, key):
        return key in coll
    def eval_not_contains(self, coll, key):
        return key not in coll


def del_list(a):
    del a[:]

class GenericListEachFunc(LibFunc):
    def __init__(self, cls):
        argtype = makeFuncSpec(ast.makePrimitiveType('void'), [cls.createElementType(), ast.makePrimitiveType('int')])
        super(GenericListEachFunc, self).__init__(cls, makeFuncProto('each', ast.makePrimitiveType('void'), [argtype]))
        # print('GenericListEachFunc.init', self.getSpec(), self)
    def evaluateCall(self, visitor, callinfo):
        # visitor.logger.debug('ListEachFunc.evaluateCall entry start', self, callinfo, callinfo.caller.object, callinfo.getOwnerFunc())
        coll = callinfo.caller.object.visit(visitor)
        assert isinstance(callinfo.args[0], ast.Closure), (callinfo, callinfo.getOwnerFunc())
        callinfo.args[0].evaluateParam(visitor)
        visitor.implicit_args_stack.insert(0, [])
        i = 0
        for item in coll:
            visitor.pushScope()
            assert len(callinfo.args) == 1, (coll, item, callinfo.args)
            # assert False, (item, coll)
            # itemval = item.visit(visitor)
            itemval = item
            visitor.implicit_args_stack[0] = [itemval, i]
            # visitor.logger.debug('ListEachFunc.evaluateCall item', item, itemval, coll)
            callinfo.args[0].visit(visitor)
            i += 1
            visitor.popScope()
        # visitor.logger.debug('ListEachFunc.evaluateCall entry end', (self, callinfo))
        del visitor.implicit_args_stack[0]
        return None

class GenericListClassImpl(GenericClassImpl):
    genericParams = [ast.GenericTypeParam('ElementType')]
    def __init__(self, genericArgs):
        super(GenericListClassImpl, self).__init__(GenericListClassImpl.genericParams, genericArgs)
        self.addDef(SimpleTypeFunc(self, 'size() => int', evaluator=len))
        self.addDef(SimpleTypeFunc(self, 'empty() => bool', evaluator=lambda left:len(left)==0))
        self.addDef(SimpleTypeFunc(self, 'clear()', evaluator=del_list))
        self.addDef(CustomTypeFunc(self, makeFuncProto('set', ast.makePrimitiveType('void'), [ast.makePrimitiveType('int'), self.createElementType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('flatten', self.createElementType(), [self.createCollectionType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('swap', ast.makePrimitiveType('void'), [self.createCollectionType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('append', ast.makePrimitiveType('void'), [self.createElementType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('extend', ast.makePrimitiveType('void'), [self.createCollectionType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('insert', ast.makePrimitiveType('void'), [ast.makePrimitiveType('int'), self.createElementType()])))
        self.addDef(CustomTypeFunc(self, makeFuncProto('remove', ast.makePrimitiveType('void'), [self.createElementType()])))
        self.addDef(CustomTypeFunc(self, 'removeAt(int)'))
        self.addDef(CustomTypeFunc(self, makeFuncProto('contains', ast.makePrimitiveType('bool'), [self.createElementType()])))
        self.addDef(GenericListEachFunc(self))
        self.ops = {'==' : operator.eq, '!=':operator.ne,
        '+':operator.add,'*':operator.mul}
    def getItemType(self):
        # print('GenericListClassImpl.getItemType', self.name, self.genericArgs)
        return self.instantiation.genericArgs[0].type.getRealType()
    def createElementType(self):
        return ast.UserType(['ElementType'])
    def createCollectionType(self):
        return ast.createListType(self.createElementType())
    def eval_append(self, coll, item):
        # assert False, (self, coll, item)
        coll.append(item)
        return None
    def evaluateNil(self, visitor):
        # print('GenericListClassImpl.evaluateNil', self, visitor)
        return []
    def evaluateBinaryOp(self, visitor, opstr, left, right):
        # visitor.logger.debug('GenericListClassImpl.evaluateBinaryOp', opstr, left, right)
        left = left.visit(visitor)
        right = right.visit(visitor)
        op = self.ops[opstr]
        return op(left, right)
    def eval_contains(self, coll, item):
        return item in coll
    def eval_not_contains(self, coll, item):
        return item not in coll
    def eval_extend(self, coll, delta):
        coll.extend(delta)
    def eval_flatten(self, coll):
        ret = []
        for item in coll:
            ret.extend(item)
        return ret
    def eval_removeAt(self, coll, val):
        del coll[val]
    def eval_remove(self, coll, val):
        coll.remove(val)
    def eval_insert(self, coll, pos, val):
        coll.insert(pos, val)
    def eval_set(self, coll, pos, val):
        coll[pos] = val

class GenericArrayEachFunc(LibFunc):
    def __init__(self, cls):
        argtype = makeFuncSpec(ast.makePrimitiveType('void'), [cls.createElementType(), ast.makePrimitiveType('int')])
        super(GenericArrayEachFunc, self).__init__(cls, makeFuncProto('each', ast.makePrimitiveType('void'), [argtype]))
    def evaluateCall(self, visitor, callinfo):
        # visitor.logger.debug('GenericArrayEachFunc.evaluateCall entry start', self, callinfo, callinfo.caller.object, callinfo.getOwnerFunc())
        coll = callinfo.caller.object.visit(visitor)
        assert isinstance(callinfo.args[0], ast.Closure), (callinfo, callinfo.getOwnerFunc())
        callinfo.args[0].evaluateParam(visitor)
        visitor.implicit_args_stack.insert(0, [])
        i = 0
        for item in coll:
            visitor.pushScope()
            assert len(callinfo.args) == 1, (coll, item, callinfo.args)
            # assert False, (item, coll)
            # itemval = item.visit(visitor)
            itemval = item
            visitor.implicit_args_stack[0] = [itemval, i]
            # visitor.logger.debug('GenericArrayEachFunc.evaluateCall item', item, itemval, coll)
            callinfo.args[0].visit(visitor)
            i += 1
            visitor.popScope()
        # visitor.logger.debug('GenericArrayEachFunc.evaluateCall entry end', (self, callinfo))
        del visitor.implicit_args_stack[0]
        return None

class GenericArrayClassImpl(GenericClassImpl):
    genericParams = [ast.GenericTypeParam('ElementType'), ast.GenericLiteralParam(ast.UserType(['int']))]
    def __init__(self, genericArgs):
        super(GenericArrayClassImpl, self).__init__(GenericArrayClassImpl.genericParams, genericArgs)
        self.addDef(GenericArrayEachFunc(self))
        assert isinstance(genericArgs[1].literal, ast.IntLiteral), (genericArgs[1], self)
        self.size = genericArgs[1].literal.value
    def createElementType(self):
        return ast.UserType(['ElementType'])
    def evaluateNil(self, visitor):
        # assert False
        return [visitor.nilValue] * self.size
    def eval_get(self, coll, key, defval=None):
        # print('GenericArrayClassImpl.eval_get', coll, key, defval)
        return coll.get(key, defval)
    def eval_set(self, coll, key, item):
        # assert False, (self, coll, item)
        # print('GenericArrayClassImpl.eval_set', self, coll, key, item)
        assert key is not None, (self, coll, key, item)
        # assert isinstance(key, str), (self, coll, key, item)
        # assert False, (self, coll, key, item)
        coll[key] = item
        return None

def evalArg(arg, visitor):
    if isinstance(arg, ast.This):
        this = visitor.getThis()
        return id(this)
    return arg.visit(visitor)

def replaceAt(s, index, ch):
    assert len(ch) == 1
    sl = list(s)
    sl[index] = ch
    return ''.join(sl)

class StringClass(BuiltinTypeClass):
    def __init__(self):
        BuiltinTypeClass.__init__(self)
        self.name = 'string'
        self.addDef(CustomTypeFunc(self, 'split(string, int) => [string]'))
        self.addDef(CustomTypeFunc(self, 'bytes() => [byte]'))
        # self.addDef(CustomTypeFunc(self, 'fromBytes(byte[], int) => string'))
        self.addDef(SimpleTypeFunc(self, 'size() => int', evaluator=len))
        self.addDef(SimpleTypeFunc(self, 'empty() => bool', evaluator=lambda s: len(s) == 0))
        self.addDef(CustomTypeFunc(self, 'format() => string'))
        self.addDef(CustomTypeFunc(self, 'startsWith(string) => bool'))
        self.addDef(CustomTypeFunc(self, 'endsWith(string) => bool'))
        self.addDef(CustomTypeFunc(self, 'upper() => string'))
        self.addDef(CustomTypeFunc(self, 'lower() => string'))
        self.addDef(CustomTypeFunc(self, 'join([string]) => string'))
        self.addDef(CustomTypeFunc(self, 'replaceAt(int, char) => string'))
        self.addDef(CustomTypeFunc(self, 'mul(int) => string'))
        self.ops = {
            '==':operator.eq, '>':operator.gt, '!=':operator.ne,
            '<':operator.lt, '>=':operator.ge, '<=':operator.le,
            '+':operator.add, '*':operator.mul, '%':self.eval_format
        }
    def getItemType(self):
        return ast.builtinCharType
    def eval_startsWith(self, s, tag):
        # print('eval_startsWith', s, tag)
        return s.startswith(tag)
    def eval_endsWith(self, s, tag):
        ret = s.endswith(tag)
        # print('eval_endsWith', s, tag, ret)
        return ret
    def eval_upper(self, s):
        return s.upper()
    def eval_lower(self, s):
        return s.lower()
    def eval_split(self, s, sep, maxsplit=None):
        # assert False, (self, coll, item)
        # assert False, (self, coll, key, item)
        ret = s.split(sep, maxsplit) if maxsplit is not None else s.split(sep)
        # print('StringClass.eval_split', self, s, sep, maxsplit, ret)
        return ret
    def evaluateNil(self, visitor):
        return ''
    def evaluateBinaryOp(self, visitor, opstr, left, right):
        # visitor.logger.debug('StringClassBase.evaluateBinaryOp', opstr, left, right)
        left = left.visit(visitor)
        right = right.visit(visitor)
        op = self.ops[opstr]
        # visitor.logger.debug('StringClassBase.evaluateBinaryOp op', opstr, left, right, op)
        if opstr == '%':
            if not isinstance(right, list) and not isinstance(right, tuple):
                right = [right]
            return op(left, *right)
        return op(left, right)
    def eval_format(self, formatstr, *args):
        # print('eval_format start', formatstr, args)
        # if not isinstance(args, list) and not isinstance(args, tuple):
        #     args = [args]
        # print('eval_format start args', formatstr, *args)
        args = [id(arg) if isinstance(arg, ast.AstNode) else arg for arg in args]
        # print('eval_format', formatstr, args)
        return formatstr % tuple(args)
    def eval_join(self, sep, args):
        # print('eval_join start', sep, args)
        return sep.join(args)
    def eval_replaceAt(self, s, index, ch):
        return replaceAt(s, index, ch) 

class AnyRefClass(BuiltinTypeClass):
    def __init__(self):
        BuiltinTypeClass.__init__(self)
        self.name = 'AnyRef'
    def evaluateNil(self, visitor):
        return visitor.nilValue

class GenericTupleClassImpl(GenericClassImpl):
    genericParams = [ast.GenericVariadicTypeParam('ElementTypes')]
    def __init__(self, genericArgs):
        assert len(genericArgs) == 1, genericArgs
        super(GenericTupleClassImpl, self).__init__(GenericTupleClassImpl.genericParams, genericArgs)
        # print('GenericTupleClassImpl.init', genericArgs, genericArgs[0].types)
    def evaluateNil(self, visitor):
        return visitor.nilValue

def addLoggerVar(context, visitor):
    if context.loggerVar is not None:
        return
    s = ''
    if isinstance(context, ast.CodeUnit):
        s = 'Logging.getLogger("%s")' % context.name
    else:
        s = 'Logging.getLogger(getClassName())'
    v = ast.SingleVarDef('logger', ast.createUserType('Logger'), parser.parseExpr(s))
    visitor.logger.error('addLoggerVar', context, visitor, v)
    v.internal = True
    context.definitions.append(v)
    context.loggerVar = v
    visitor.setupNewItem(v, context, False)
    codeunit = context.getOwnerUnit()
    codeunit.addLoggerImports(visitor)
    return v

class LogFunction(LibFunc):
    def __init__(self, cls, name, level):
        proto = name + '([AnyRef])'
        LibFunc.__init__(self, cls, proto)
        self.level = level
    def evaluateCall(self, visitor, callinfo):
        loggerobj = visitor.getValue('logger')
        # visitor.logger.debug('LogFunction.evaluateCall', self, self.level, visitor, callinfo, callinfo.getOwner(), loggerobj)
        args = [arg.visit(visitor) for arg in callinfo.args]
        loggerobj.log(self.level, *args)
    def resolveCall(self, visitor, callinfo):
        cls = callinfo.getOwnerClass()
        assert isinstance(cls, ast.ClassDef) or cls is None, (self, visitor, callinfo, cls)
        if cls is None or cls.loggerVar is None:
            # if there is no logger var in class context or there is no class context, add logger var to code unit
            # print('LogFunction.resolveCall', callinfo, callinfo.getOwnerFunc(), callinfo.getOwnerFunc().getOwner())
            codeunit = callinfo.getOwnerUnit()
            addLoggerVar(codeunit, visitor)

class LogClass(LibClass):
    def __init__(self):
        LibClass.__init__(self, 'Log')
        self.addDef(LogFunction(self, 'trace', 5))
        self.addDef(LogFunction(self, 'debug', logging.DEBUG))
        self.addDef(LogFunction(self, 'info', logging.INFO))
        self.addDef(LogFunction(self, 'warn', logging.WARNING))
        self.addDef(LogFunction(self, 'event', logging.ERROR))
        self.addDef(LogFunction(self, 'error', logging.ERROR))
        self.addDef(LogFunction(self, 'critical', logging.CRITICAL))
        self.addDef(LogFunction(self, 'fatal', logging.CRITICAL))
