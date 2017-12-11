
import ast
import parser
import re

def parseCreator(s, ut):
    # print('parseCreator', s, ut)
    if not s:
        return None
    creator = parser.parseFuncProto(s)
    creator.spec.returnType = ut
    return creator

def parseConstructors(strs, ut):
    # print('parseConstructors', strs, ut)
    if not strs:
        if strs is not None:
            assert len(strs) == 0, strs
        return []
    cs = []
    for s in strs:
        c = parseCreator(s, ut)
        if c:
            cs.append(c)
    return cs

def convertStdNameChar(ch):
    #print('convertStdNameChar', ch, dir(ch), str(ch), ch.group(1))
    return '_' + ch.group(1).lower()
def convertStdName(name):
    return re.sub(r'([A-Z])', convertStdNameChar, name)

def convertStdToCamelName(s):
    parts = s.split('_')
    tailParts = [part.capitalize() for part in parts[1:]]
    return ''.join([parts[0]] + tailParts)

def capitalizeFirst(s):
    if not s:
        return s
    return s[0].upper() + s[1:]

def camelizeFirst(s):
    if not s:
        return s
    return s[0].lower() + s[1:]

def convertToCamelName(s):
    parts = s.split('_')
    tailParts = [capitalizeFirst(part) for part in parts[1:]]
    return ''.join([camelizeFirst(parts[0])] + tailParts)

def convertStdToPascalName(s):
    return convertToPascalName(s)
def convertToPascalName(s):
    parts = s.split('_')
    capParts = [capitalizeFirst(part) for part in parts]
    return ''.join(capParts)

def makeFuncProto(name, rettype, param_types):
    spec = makeFuncSpec(rettype, param_types)
    proto = ast.FuncProto(name, spec)
    return proto

def makeFuncSpec(rettype, param_types):
    params = [ast.Param(None, t) for t in param_types]
    # print('makeFuncSpec proto params', name, param_types, params)
    spec = ast.FuncSpec(params, rettype)
    return spec


class TypeClass(ast.BlockNode):
    def __init__(self):
        ast.BlockNode.__init__(self)
        self.spec = None
    def clone(self):
        return self
    def getSpec(self):
        return self.spec
    def getTypeClass(self):
        return self

class LibClass(ast.LibClassBase):
    def __init__(self, name):
        ast.LibClassBase.__init__(self)
        self.name = name
        self.constructors = []
        self.bases = []
        self.spec = ast.FuncSpec([], ast.UserType([self.name]))
        self.definitions = []
        self.astFieldNames = ['definitions']
    def addDef(self, child):
        self.definitions.append(child)
    def findMember(self, name):
        return self.findLocalSymbol(name)
    def getSpec(self):
        return self.spec
    def getTypeClass(self):
        return self
    def getType(self):
        return self
    def resolveAttr(self, visitor, expr):
        # visitor.logger.debug('LibClass.resolveAttr', expr, expr.ref, expr.object, expr.object.getTarget(), self.names, self.functions, self.vars)
        child = self.findLocalSymbol(expr.ref)
        if isinstance(child, (LibFunc, LibVar, LibLiteral)):
            return child
        assert False, (expr, expr.object, expr.ref, expr.getOwner(), expr.getOwnerFunc(), self, self.symbols)
        return None
    def __repr__(self):
        return '%s:%s:0x%08x' % (type(self), self.name, id(self))
    def cacheName(self, visitor):
        # visitor.logger.debug('LibClass.cacheName', self.name, self, visitor, self.getOwner(), self.getOwner().pkg)
        self.getOwner().addSymbol(self)
        self.visitChildren(visitor)
    def dump(self, out, depth):
        out.write('%s LibClass name=%s\n' % (depth * 4 * ' ', 'LibClass:' + self.name))


class ClassInfo(LibClass):
    def __init__(self, cls):
        LibClass.__init__(self, 'Class')
        self.cls = cls

class LibVar(ast.SimpleNode):
    def __init__(self):
        # print('LibFunc.init', cls, proto)
        ast.SimpleNode.__init__(self)
    def cacheName(self, visitor):
        self.getOwner().addSymbol(self)
    def getType(self):
        return self.type
    def isVar(self):
        return True

class LibLiteral(LibVar):
    def __init__(self, name, type, value):
        LibVar.__init__(self)
        self.name = name
        self.type = type
        self.value = value
    def isLiteral(self):
        return True
    def getValue(self):
        return self.value
    def evaluate(self, visitor):
        return self.value

class LibFunc(ast.LibFuncBase):
    def __init__(self, cls, proto):
        # print('LibFunc.init', cls, proto)
        ast.LibFuncBase.__init__(self)
        self.cls = cls
        self.protostr = proto
        self.proto = parser.parseFuncProto(proto) if isinstance(proto, str) else proto
        self.proto.setOwner(self)
        assert(isinstance(self.proto, ast.FuncProto))
        self.target_name = self.proto.name
        self.name = self.proto.name
        assert self.name, (self.name, self, proto)
        self.spec = self.proto.spec
        self.type = self.spec
        self.headers = []
        self.returnType = self.spec.returnType
        # self.setTarget(self)
        self.type_name_resolved = False
        self.resolved = False
        self.evaluator = None
        self.astFieldNames = ['spec']
        assert(self.name)
    def isFunc(self):
        return True
    def cacheName(self, visitor):
        # visitor.logger.debug('LibFunc.cacheName', self.name, self, visitor, self.getOwner())
        self.getOwner().addSymbol(self)
        self.visitChildren(visitor)
    def getSpec(self):
        # print('LibFunc.getSpec', self.name, self, self.spec)
        return self.spec
    def getType(self):
        # print('LibFunc.getType', self.name, self, self.spec)
        return self.spec
    def getTypeClass(self):
        return self
    def resolveRef(self, visitor):
        # visitor.logger.debug('LibFunc.resolveRef', self, visitor, self.getTypeClass())
        if not self.getTypeClass():
            self.visitChildren(visitor)
            self.spec.typeClass = FunctionClass(self.spec)
            # visitor.logger.debug('LibFunc.resolveRef set_type_class', self, visitor, self.getTypeClass())
        assert self.getTypeClass(), self
        return self
    def dump(self, out, depth):
        return
    def evaluateCall(self, visitor, callinfo):
        # visitor.logger.debug('LibFunc.evaluateCall', self.protostr, self, visitor, callinfo, callinfo.caller, callinfo.caller.object, callinfo.args)
        evaluator = self.evaluator if self.evaluator else getattr(self.cls, 'eval_' + self.name)
        caller = callinfo.caller.object.visit(visitor)
        args = [arg.evaluateParam(visitor) for arg in callinfo.args]
        # visitor.logger.debug('LibFunc.evaluateCall eval', self.protostr, visitor, callinfo, evaluator, caller, callinfo.caller.object, callinfo.args, args)
        return evaluator(caller, *args)

class SimpleTypeFunc(LibFunc):
    def __init__(self, cls, protostr, targetName = None, headers = None, evaluator = None):
        LibFunc.__init__(self, cls, protostr)
        self.targetName = targetName if targetName else self.name
        self.headers = headers if headers else []
        self.evaluator = evaluator

class CustomTypeFunc(LibFunc):
    def __init__(self, cls, proto, evaluator = None):
        LibFunc.__init__(self, cls, proto)
        self.evaluator = evaluator
    def __repr__(self):
        return 'CustomTypeFunc(%s.%s,id=%s)' % (self.cls, self.proto, ast.formatId(self))
    def resolveType(self, visitor):
        # assert False, self
        return self

class BuiltinTypeClass(TypeClass):
    def __init__(self):
        TypeClass.__init__(self)
        self.type = self
        self.pkg = ast.Package.getRoot()
        self.definitions = []
        self.astFieldNames = ['definitions']
    def isClass(self):
        return True
    def addDef(self, child):
        self.definitions.append(child)
    def cacheName(self, visitor):
        self.getOwner().addSymbol(self)
        self.visitChildren(visitor)
    def resolveAttr(self, visitor, expr):
        # visitor.logger.debug('BuiltinTypeClass.resolveAttr', self, expr, expr.object, expr.ref, self.funcs)
        child = self.findLocalSymbol(expr.ref)
        if isinstance(child, (LibFunc, LibVar, LibLiteral)):
            return child
        assert False, (expr, expr.object, expr.ref, expr.getOwner(), expr.getOwnerFunc(), self, self.symbols)
        return None


class FunctionClass(BuiltinTypeClass):
    def __init__(self, spec):
        super(FunctionClass, self).__init__()
        # print('FunctionClass.init', self, spec)
        self.spec = spec
        self.params = spec.params
        self.returnType = spec.returnType
    def cacheName(self, visitor):
        self.doVisitChildren(visitor)
    def evaluateNil(self, visitor):
        return visitor.nilValue

class FuncGetClass(LibFunc):
    def __init__(self, cls):
        LibFunc.__init__(self, cls, 'ClassInfo getClass()')
    def log(self, depth):
        print('%s FuncGetClass 0x%08x %s %s %s' % (depth * 4 * ' ', id(self), self.name, self.spec.returnType, self.spec.params))

