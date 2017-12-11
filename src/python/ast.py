
import xutils
import contextlib
import traceback
import inspect

def isSubClass(cls, basecls):
    assert isinstance(basecls, ClassDef), (cls, basecls)
    if not isinstance(cls, ClassDef):
        return False
    if cls is basecls:
        return True
    for b in cls.bases:
        bcls = b.getTarget()
        if isSubClass(bcls, basecls):
            return True
    return False

class AstSimpleContext(object):
    def __init__(self):
        self.owner = None
        self.astFieldNames = None
    def getOwner(self):
        return self.owner
    def setOwner(self, owner):
        assert owner, (self, self.owner)
        self.owner = owner
    def addSymbol(self, symbol):
        assert False, (self, symbol, self.owner, self.getOwnerFunc(), self.getOwnerClass())
    def findMember(self, name):
        # print('AstSimpleContext.findMember', self, name, self.owner)
        return None
    def resolveMember(self, path):
        return None
    def findSymbol(self, name):
        # print('AstSimpleContext.findSymbol', name, self, self.owner)
        return self.owner.findSymbol(name) if self.owner else None
    def getOwnerFunc(self):
        # print('getOwnerFunc', self, self.owner)
        if isinstance(self, FuncDef) or isinstance(self, FuncProto) or isinstance(self, LibFuncBase):
            return self
        # assert self.owner, self
        return self.owner.getOwnerFunc() if self.owner else None
    def getOwnerClass(self):
        # assert self.owner, self
        if isinstance(self, ClassDef) or isinstance(self, LibClassBase):
            return self
        return self.owner.getOwnerClass() if self.owner else None
    def getOwnerUnit(self):
        assert self.owner, self
        if isinstance(self, CodeUnit):
            return self
        return self.owner.getOwnerUnit() if self.owner else None
    def getOwnerClosure(self):
        assert self.owner, self
        if isinstance(self, Closure):
            return self
        return self.owner.getOwnerClosure() if self.owner else None
    def getOwnerBlockContext(self):
        assert self.owner, self
        if isinstance(self, AstBlockContext):
            return self
        return self.owner.getOwnerBlockContext() if self.owner else None
    def getOwnerFullContext(self):
        assert self.owner, self
        if isinstance(self, AstFullContext):
            return self
        return self.owner.getOwnerFullContext() if self.owner else None
    def resolveSymbol(self, path):
        if self.owner is None:
            # print('AstSimpleContext.resolveSymbol top', path, self)
            return None
        return self.owner.resolveSymbol(path)
    def visitChildren(self, visitor):
        return self.doVisitChildren(visitor)


class AstBlockContext(AstSimpleContext):
    def __init__(self):
        AstSimpleContext.__init__(self)
        self.symbols = {}
    def hasSymbol(self, name):
        return name in self.symbols
    def findMember(self, name):
        # print('AstBlockContext.findMember', self, name, self.owner, self.symbols)
        return self.findLocalSymbol(name)
    def findLocalSymbol(self, name):
        # print('AstBlockContext.findLocalSymbol', name, self, self.owner, self.symbols.get(name, None))
        return self.symbols.get(name, None)
    def resolveMember(self, path):
        # print('AstBlockContext.resolveMember', self, path, self.owner)
        node = self.findMember(path[0])
        if node is not None and len(path) > 1:
            # print('AstBlockContext.resolveMember in node', self, node, path, self.owner, self.symbols)
            return node.resolveMember(path[1:])
        # print('AstBlockContext.resolveMember found node', self, node, path, self.owner, self.symbols)
        return node
    def addSymbol(self, node):
        # print('AstBlockContext.addSymbol', node.name, node, self, self.owner)
        assert node.name not in self.symbols, (node.name, node, self, self.symbols)
        self.symbols[node.name] = node
        assert node.name in self.symbols and self.symbols[node.name], (node.name, node, self, self.symbols)
        if isinstance(self, (CodeUnit, LibUnit)):
            if not self.pkg.hasSymbol(node.name):
                # print('AstBlockContext.addSymbol to pkg', node.name, node, self, self.owner, self.pkg)
                self.pkg.addSymbol(node)
    def resolveSymbol(self, path):
        # print('AstBlockContext.resolveSymbol', path, self)
        assert path and isinstance(path, list), ('AstBlockContext.resolveSymbol: path should not be empty', self, path)
        node = self.findSymbol(path[0])
        if node is not None:
            if len(path) > 1:
                return node.resolveMember(path[1:])
            else:
                return node
        return self.owner.resolveSymbol(path) if self.owner is not None else None
    def findSymbol(self, name):
        # print('AstBlockContext.findSymbol', name, self, self.owner)
        node = self.findLocalSymbol(name)
        if node is not None:
            # print('findSymbol found:', name, node, self)
            return node
        if self.owner is None:
            # print('findSymbol failed:', name, self)
            return None
        # print('AstBlockContext.findSymbol in owner:', name, self, self.owner, self.symbols)
        return self.owner.findSymbol(name)
    def eachSymbol(self, f):
        for k, v in self.symbols.iteritems():
            f(k, v)
    def addVar(self, var):
        self.addSymbol(var)

class AstFullContext(AstBlockContext):
    def __init__(self):
        AstBlockContext.__init__(self)
        self.definitions = []
        self.functions = []
        self.classes = []
        self.vars = []
        self.consts = []
        self.enums = []
        self.types = []
        self.removedDefs = []
    def addFunc(self, func):
        # print('AstFullContext.addFunc', func.name, func, self)
        self.addSymbol(func)
        self.functions.append(func)
    def addClass(self, cls):
        self.addSymbol(cls)
        self.classes.append(cls)
    def addVar(self, var):
        self.addSymbol(var)
        self.vars.append(var)

class AstVisitor(object):
    def __init__(self):
        self.fullContexts = []
        self.blockContexts = []
        self.project = None
        self.logger = xutils.createLogger(self.__class__.__name__)
    def pushFullContext(self, context):
        self.conetxts.insert(0, context)
    def popFullContext(self, context):
        del self.conetxts[0]
    def previsit(self, node):
        pass
    def getOwnerUnit(self):
        #return getOwnerUnit(owner)
        return self.ast
    def getContext(self):
        return self.contexts[0]
    def autoVisit(self, node, func):
        # self.logger.debug('AstVisitor.autoVisit', node, self, node.owner, node.getOwnerFunc(), node.getOwnerClass())
        node.checkAstFieldNames()
        for argname in node.astFieldNames:
            # assert hasattr(node, argname), (node, argname)
            field = getattr(node, argname)
            # self.logger.debug('AstVisitor.autoVisit field', argname, field, node, self, node.getOwnerFunc())
            self.autoVisitField(argname, field, node, func)
    def autoVisitField(self, name, field, node, func):
        # self.logger.debug('AstVisitor.autoVisitField', field, node, self)
        if isinstance(field, list):
            # self.logger.debug('AstVisitor.autoVisitField list', field, node, self)
            for x in field[:]:
                self.autoVisitField(name, x, node, func)
        elif isinstance(field, dict):
            # self.logger.debug('AstVisitor.autoVisitField dict', field, node, self)
            for key, val in field.iteritems():
                self.autoVisitField(name, key, node, func)
                self.autoVisitField(name, val, node, func)
        elif isinstance(field, tuple):
            for x in list(field):
                self.autoVisitField(name, x, node, func)
        elif isinstance(field, AstNode):
            # self.logger.debug('AstVisitor.autoVisitField node', field, node, self, func)
            func(field, node)
        else:
            # self.logger.debug('AstVisitor.autoVisitField extra', field, node, self)
            assert isinstance(field, str) or isinstance(field, int) or isinstance(field, float) or isinstance(field, xutils.EnumItem) or field is None, (name, node, field, type(field), node.getOwnerFunc())
    def visit(self, astree):
        # self.logger.debug('AstVisitor.visit', self, astree.definitions)
        self.ast = astree
        self.contexts = []
        self.ast.visit(self)
    def visitNewItem(self, item):
        self.project.visitNewItem(item)
    def setupNewItem(self, item, owneritem, useCurrentVisitor):
        self.project.setupNewItem(item, owneritem, self if useCurrentVisitor else None)


class Passthrough(object):
    pass


passthrough = Passthrough()


class AstNode(object):
    MUST_EXIST = 1
    RETURN_ORGINAL = 2
    RETURN_NONE = 3
    RETURN_PASSTHROUGH = 4
    commands = [
        ('resolveRef' , RETURN_PASSTHROUGH),
        ('evalLiteral' , MUST_EXIST),
        ('matchType' , MUST_EXIST),
        ('resolveNameRef' , RETURN_NONE),
        ('resolveAttr' , MUST_EXIST),
        ('resolveCall' , RETURN_PASSTHROUGH),
        ('evaluateCall', MUST_EXIST),
        ('evaluateAttr', MUST_EXIST),
        ('evaluateNil', MUST_EXIST),
        ('evaluateVar', MUST_EXIST),
        ('evaluateIdentifierAttr', MUST_EXIST),
        ('evaluateGlobalVar', RETURN_PASSTHROUGH),
        ('evaluateBinaryOp', MUST_EXIST),
        ('evaluateUnaryOp', MUST_EXIST),
        ]
    def visit(self, visitor, *args):
        # print('AstNode.visit', self, visitor)
        visitor.previsit(self)
        # try internal `opname` method first
        func = getattr(self, visitor.opname, None)
        if func:
            ret = func(visitor, *args)
            if ret != passthrough:
                return ret
        # try external visit function
        ret = self.tryVisitExternal(self.__class__, visitor, *args)
        if ret != passthrough:
            return ret
        return self.visitDefault(visitor, *args)
    def tryVisitExternal(self, cls, visitor, *args):
        attrname = visitor.opname + '_' + cls.__name__
        # print('tryVisitExternal invoke', self, attrname)
        func = getattr(visitor, attrname, None)
        if func:
            ret = func(self, *args)
            if ret != passthrough:
                return ret
        for basecls in cls.__bases__:
            ret = self.tryVisitExternal(basecls, visitor, *args)
            if ret != passthrough:
                return ret
        return passthrough
    def visitDefault(self, visitor, *args):
        # print('AstNode.do_visit', visitor, args, self)
        self.visitChildren(visitor)
    def doVisitChildren(self, visitor):
        # print('AstNode.doVisitChildren', self, visitor)
        visitor.autoVisit(self, lambda node, owner: node.visit(visitor))
    def tryInvoke(self, name, cls, *args):
        attrname = name + '_' + cls.__name__
        # print('invoke', self, name, attrname, strategy, args, len(args))
        func = getattr(args[0], attrname, None)
        if func:
            return func(self, *args[1:]), True
        for basecls in cls.__bases__:
            ret, ok = self.tryInvoke(name, basecls, *args)
            if ok:
                return ret, ok
        return None, False
    def invoke(self, name, strategy, *args):
        ret, ok = self.tryInvoke(name, self.__class__, *args)
        if ok:
            return ret
        # print('---------------------- invoke default', self, name, args)
        if strategy == AstNode.RETURN_ORGINAL:
            return self
        if strategy == AstNode.RETURN_PASSTHROUGH:
            return passthrough
        if strategy == AstNode.RETURN_NONE:
            return None
        #assert(False, 'invoke no function %s %s' % (name, self))
        assert False, 'invoke no function %s %s' % (name, self)
        return None
    def getTarget(self):
        return self.target
    def resolveRef(self, visitor, *args):
        return self
    def constructAst(self, visitor):
        visitor.constructAst(self)
    def __copy__(self):
        return self.clone()
    def __deepcopy__(self):
        return self.clone()
    def setupType(self, t, visitor):
        if t is None:
            assert False, (self, t)
            return
        assert self.type is None, (self, self.type, t, visitor)
        t2 = t.clone()
        self.type = t2
        visitor.setupNewItem(self.type, self, True)
    def checkAstFieldNames(self):
        if self.astFieldNames is None:
            argspec = inspect.getargspec(self.__init__)
            assert argspec.args[0] == 'self', (self, argspec)
            self.astFieldNames = argspec.args[1:]
    def clone(self):
        # print('AstNode.clone', self)
        self.checkAstFieldNames()
        fields = []
        for argname in self.astFieldNames:
            # assert hasattr(node, argname), (node, argname)
            field = getattr(self, argname)
            # print('AstNode.clone field', argname, field, self)
            fields.append(self.cloneField(field))
        # print('AstNode.clone before result', self, type(self), fields)
        ret = type(self)(*fields)
        # print('AstNode.clone result', self, type(self), fields, ret)
        return ret
    def cloneField(self, field):
        # print('AstNode.cloneField', field, self)
        if isinstance(field, list):
            # print('AstNode.cloneField list', field, self)
            return [self.cloneField(x) for x in field]
        elif isinstance(field, dict):
            # print('AstNode.cloneField dict', field, self)
            return dict([(key, self.cloneField(val)) for key, val in field.iteritems()])
        elif isinstance(field, AstNode):
            # print('AstNode.cloneField node', field, self)
            return field.clone()
        else:
            # print('AstVisitor.cloneField extra', field, node, self)
            assert isinstance(field, str) or isinstance(field, int) or field is None, (node, field)
            return field
    def setExpectedType(self, expectedType):
        # assert expectedType, self
        self.expectedType = expectedType
    def getSpec(self):
        return self.getTypeClass().getSpec() if self.getTypeClass() else None
    def evaluateParam(self, visitor):
        assert not isinstance(self, StatementBody), self
        assert not isinstance(self, StatementBlock), self
        return self.visit(visitor)
    def getTarget(self):
        return self.target
    def isClass(self):
        return False
    def isFunc(self):
        return False
    def isVar(self):
        return False
    def isLiteral(self):
        return False
    def isUnit(self):
        return False

class LibUnit(AstNode, AstBlockContext):
    def __init__(self, name, packageDef, definitions):
        # print('LibUnit.init', name, formatId(self), packageDef, len(definitions))
        assert packageDef
        AstNode.__init__(self)
        AstBlockContext.__init__(self)
        self.pkg = None
        self.packageDef = packageDef
        self.definitions = definitions
        self.name = name
        self.imports = []
        self.scripts = []
        # self.visitors = []
    def isUnit(self):
        return True
    def __repr__(self):
        return 'LibUnit:%s:%s' % (self.name, formatId(self))
    def setType(self, node, type):
        assert False
        # print('CodeUnit.setType', self.name, node, type)
        node.setType(type)
        # print('CodeUnit.setType visitNewItem', self.name, node, type, node.getType())
        self.visitNewItem(node.getType())

class CodeUnit(AstNode, AstFullContext):
    def __init__(self, name, language, packageDef, scripts, imports, definitions):
        # print('CodeUnit.init', name, formatId(self), packageDef, imports, len(definitions))
        assert packageDef
        AstNode.__init__(self)
        AstFullContext.__init__(self)
        self.pkg = None
        self.packageDef = packageDef
        self.imports = imports
        self.definitions = definitions
        self.scripts = scripts
        self.basename = ''
        self.name = name
        self.language = language
        self.loggerVar = None
        self.loggerImports = []
        self.globalScope = None
    def isUnit(self):
        return True
    def __repr__(self):
        return 'CodeUnit:%s:%s' % (self.name, formatId(self))
    def setType(self, node, type):
        assert False
    def addLoggerImports(self, visitor):
        if not self.loggerImports:
            self.loggerImports.extend([Import(['sys'], ['Logging']), Import(['sys'], ['Logger'])])
            for imp in self.loggerImports:
                self.imports.append(imp)
                visitor.setupNewItem(imp, self, False)


def makeHandlerFunc(cmd, tag = AstNode.RETURN_NONE):
    func = lambda item, handler, *args : item.invoke(cmd, tag, handler, *args)
    return func


#for cmd, tag in AstNode.commands.iteritems():
for (cmd, tag) in AstNode.commands:
    #break
    # print('AstNode add method', cmd, tag)
    func = makeHandlerFunc(cmd, tag)
    # print('setattr makeHandlerFunc', AstNode, cmd, tag, func, id(func))
    setattr(AstNode, cmd, func)

def formatId(obj):
    return '0x%08x' % id(obj)


class SimpleNode(AstNode, AstSimpleContext):
    def __init__(self):
        AstSimpleContext.__init__(self)

class BlockNode(AstNode, AstBlockContext):
    def __init__(self):
        AstBlockContext.__init__(self)

class EmbeddedNode(SimpleNode):
    def __init__(self):
        SimpleNode.__init__(self)
        self.type = None
    def setType(self, t):
        assert False, (self, t)
    def getTarget(self):
        return self
    def getType(self):
        # assert False, (self, self.code)
        return self.type

class EmbeddedCode(EmbeddedNode):
    def __init__(self, code):
        EmbeddedNode.__init__(self)
        self.code = code
        self.type = None
    def getType(self):
        return self.code.getType()
    def __repr__(self):
        return 'EmbeddedCode(id=%s,code=%s)' % (formatId(self), self.code)

class EmbeddedStatement(EmbeddedNode):
    def __init__(self, statement):
        EmbeddedNode.__init__(self)
        self.statement = statement
        self.type = UserType([self.statement.__class__.__name__])
    def visitChildren(self, visitor):
        pass
    def __repr__(self):
        return 'EmbeddedStatement(id=%s,statement=%s)' % (formatId(self), self.statement)

class EmbeddedExpr(EmbeddedNode):
    def __init__(self, expr):
        EmbeddedNode.__init__(self)
        self.expr = expr
        self.type = UserType([self.expr.__class__.__name__])
    def visitChildren(self, visitor):
        pass
    def __repr__(self):
        return 'EmbeddedExpr(id=%s,expr=%s)' % (formatId(self), self.expr)

class ExprEvaluation(EmbeddedNode):
    def __init__(self, expr):
        EmbeddedNode.__init__(self)
        self.expr = expr
    def getType(self):
        return self.expr.getType()
    def __repr__(self):
        return 'ExprEvaluation(id=%s,expr=%s)' % (formatId(self), self.expr)

class Package(BlockNode):
    rootPackage = None

    @staticmethod
    def getRoot():
        return Package.rootPackage
    def visitChildren(self, visitor):
        for name, item in self.symbols.iteritems():
            item.visit(visitor)
    def __init__(self, path):
        BlockNode.__init__(self)
        # print('Package.init', path, formatId(self))
        if isinstance(path, list):
            self.path = path
            self.fullpath = '.'.join(path)
            assert not path or path[0] != '', path
        else:
            self.fullpath = path
            self.path = path.split('.') if path else []
            assert self.path != [''], self.path
            path = self.path
        self.name = path[len(path)-1] if path else ''
        self.packages = {}
    def findMember(self, name):
        # print('Package.findMember', self, name, self.owner, self.symbols)
        return self.findLocalSymbol(name)
    def getPackage(self, path):
        # print('Package.getPackage0', self.path, path, formatId(self))
        assert isinstance(path, list) or isinstance(path, str), path
        if isinstance(path, str):
            path = path.split('.') if path else []
        #assert len(self.path) > 0 or len(path) > 0, (self.path, path)
        if len(path) == 0:
            #assert False, path
            return self
        name = path[0]
        pkg = self.findLocalSymbol(name)
        if pkg is None:
            assert len(self.path) == 0 or self.path[-1] != path[0], (self.path, path, self.packages)
            # print('Package.getPackage create_child', self.path, path, formatId(self), self.packages)
            pkg = self.createChild(self.path + [path[0]])
            pkg.setOwner(self)
            # print('Package.getPackage create_child ok', self.path, pkg.path, path, formatId(self), formatId(pkg), self.packages, self.symbols)
            assert name not in self.symbols
            self.addSymbol(pkg)
        else:
            assert isinstance(pkg, Package)
        # print('Package.getPackage found package', getPackage.path, pkg.path, path, formatId(self), formatId(pkg))
        if len(path) == 1:
            return pkg
        return pkg.getPackage(path[1:])
    def __repr__(self):
        return 'Package:%s:0x%08x:%s' % (self.fullpath, id(self), self.packages.keys())
    def createChild(self, path):
        pkg = Package(path)
        # print('Package.create_child', path, self.path, formatId(self), formatId(pkg))
        return pkg
    def visitChildren(self, visitor):
        assert False, (self, visitor)

Package.rootPackage = Package('')

class PackageDef(SimpleNode):
    def __init__(self, path):
        SimpleNode.__init__(self)
        self.path = path
        self.fullpath = '.'.join(path)

class Import(SimpleNode):
    def __init__(self, path, names = []):
        SimpleNode.__init__(self)
        self.path = path
        self.fullpath = '.'.join(path)
        self.names = names
        self.target = None
    def getTarget(self):
        return self.target
    def setTarget(self, t):
        self.target = t
    def dump(self, out, depth):
        out.write('%s Import %s %s %s\n' % (depth * 4 * ' ', self.fullpath, len(self.names) if self.names else 0, self.getTarget()))

class Statement(AstNode):
    def __init__(self):
        AstNode.__init__(self)

class Definition(Statement):
    def __init__(self):
        Statement.__init__(self)

class Expression(AstNode):
    def __init__(self):
        AstNode.__init__(self)
        self.expectedType = None
    def getType(self):
        assert False, self
    def getTypeClass(self):
        if self.getType() is None:
            return None
        return self.getType().getTypeClass()

class SimpleExpression(Expression, AstSimpleContext):
    def __init__(self):
        Expression.__init__(self)
        AstSimpleContext.__init__(self)

class BlockExpression(Expression, AstBlockContext):
    def __init__(self):
        Expression.__init__(self)
        AstBlockContext.__init__(self)

class SimpleStatement(Statement, AstSimpleContext):
    def __init__(self):
        Statement.__init__(self)
        AstSimpleContext.__init__(self)

class BlockStatement(Statement, AstBlockContext):
    def __init__(self):
        Statement.__init__(self)
        AstBlockContext.__init__(self)

class SimpleDefinition(Definition, AstSimpleContext):
    def __init__(self):
        AstSimpleContext.__init__(self)

class BlockDefinition(Definition, AstBlockContext):
    def __init__(self):
        Definition.__init__(self)
        AstBlockContext.__init__(self)

class FullDefinition(Definition, AstFullContext):
    def __init__(self):
        Definition.__init__(self)
        AstFullContext.__init__(self)


class Type(SimpleExpression):
    def __init__(self):
        SimpleExpression.__init__(self)
    def getTypeClass(self):
        assert False, self
        return None
    def setupTypeClass(self, tc, visitor):
        # print('Type.setupTypeClass', tc, visitor, self.typeClass, visitor.ast.visitors)
        if self.typeClass is None:
            self.typeClass = tc
            visitor.setupNewItem(self.typeClass, self, True)

class Literal(SimpleExpression):
    def __init__(self):
        SimpleExpression.__init__(self)
        self.type = None
    def getType(self):
        return self.type
    def getTypeClass(self):
        return self.getType().getTypeClass() if self.getType() else None

class Nil(Literal):
    def __init__(self):
        # print('Nil.init', formatId(self))
        Literal.__init__(self)
    def getType(self):
        return self.expectedType

class This(Literal):
    def __init__(self, type=None):
        Literal.__init__(self)
        self.astFieldNames = ['type']
        self.target = None

class ExtensionDef(Definition, AstBlockContext):
    def __init__(self, name, definitions):
        # print('ExtensionDef.init', name, len(definitions))
        AstBlockContext.__init__(self)
        self.name = name
        self.definitions = definitions
        self.cls = None
    def getOwnerClass(self):
        # assert self.cls
        return self.cls
    def findLocalSymbol(self, name):
        # print('ExtensionDef.findLocalSymbol', name, self, self.owner)
        assert self.cls, (self, name)
        if self.cls:
            node = self.cls.findLocalSymbol(name)
            if node:
                return node
        return AstBlockContext.findLocalSymbol(self, name)
    def __repr__(self):
        return 'ExtensionDef:%s:0x%08x' % (self.name, id(self))

class GenericParam(SimpleNode):
    def __init__(self):
        SimpleNode.__init__(self)

class GenericTypeParam(GenericParam):
    def __init__(self, name):
        GenericParam.__init__(self)
        self.name = name

class GenericVariadicTypeParam(GenericParam):
    def __init__(self, name):
        GenericParam.__init__(self)
        self.name = name

class GenericLiteralParam(GenericParam):
    def __init__(self, type):
        GenericParam.__init__(self)
        assert isinstance(type, UserType), type
        self.type = type
    def mayBeTypeParam(self):
        return self.type.getTypeClass() is None and len(self.type.path) == 1

class GenericArg(SimpleNode):
    def __init__(self):
        SimpleNode.__init__(self)

class GenericTypeArg(GenericArg):
    def __init__(self, type):
        assert isinstance(type, (UserType, PointerType, FuncSpec)), (type, type.__class__)
        GenericArg.__init__(self)
        self.type = type

class GenericLiteralArg(GenericArg):
    def __init__(self, literal):
        GenericArg.__init__(self)
        self.literal = literal

class GenericVariadicTypeArg(GenericArg):
    def __init__(self, types):
        for t in types:
            assert isinstance(t, (UserType, PointerType, FuncSpec, ExprEvaluation)), (t, t.__class__, types)
        assert len(types) > 0
        GenericArg.__init__(self)
        self.types = types

class CaseClassDef(Definition, AstFullContext):
    def __init__(self, scripts, name, genericParams, fields, definitions):
        AstFullContext.__init__(self)
        self.scripts = scripts
        self.name = name
        self.genericParams = genericParams
        self.fields = fields
        self.definitions = definitions
    def __repr__(self):
        return 'CaseClassDef:%s:0x%08x' % (self.name, id(self))
    def visitChildren(self, visitor):
        pass

def isSameType(x, y):
    return x.getTypeClass() == y.getTypeClass()

def checkGenericArgsCompatible(genericParams, genericArgs):
    assert len(genericParams) == len(genericArgs), (genericParams, genericArgs)
    for i in range(len(genericParams)):
        param = genericParams[i]
        arg = genericArgs[i]
        if isinstance(param, GenericTypeParam):
            # type arg or literal arg
            assert isinstance(arg, GenericTypeArg), (param, arg)
            # print('checkGenericArgsCompatible type param', param, param.name, param.type, arg)
        elif isinstance(param, GenericLiteralParam):
            # type arg or literal arg
            assert isinstance(arg, (GenericTypeArg, GenericLiteralArg)), (param, arg)
            # print('checkGenericArgsCompatible literal param', param, param.type, arg)
            if isinstance(arg, GenericLiteralArg):
                assert param.type.getTypeClass(), ('checkGenericArgsCompatible literal param', param, param.type, arg)
        elif isinstance(param, GenericVariadicTypeParam):
            assert isinstance(arg, GenericVariadicTypeArg), (param, arg)
        else:
            assert False, (param, arg)
            assert isinstance(param, GenericLiteralParam) and isinstance(arg, GenericLiteralArg), (param, arg)
            assert isSameType(param.type, arg.literal.getType()), (param, arg, param.type, arg.literal)

class GenericInstantiator(object):
    def __init__(self, genericParams):
        self.genericParams = genericParams
        self.classes = []
    def getRealArgs(self, genericArgs):
        # print('GenericInstantiator.getRealArgs', self.genericParams, genericArgs)
        realGenericArgs = []
        for arg in genericArgs:
            if isinstance(arg, GenericTypeArg):
                if isinstance(arg.type, UserType):
                    if isinstance(arg.type.target, UserType):
                        newarg = GenericTypeArg(arg.type.getRealType())
                        # print('GenericClass.instantiate generic usertype arg', arg, arg.type, arg.type.getTarget(), newarg, newarg.type)
                        realGenericArgs.append(newarg)
                    else:
                        # print('GenericClass.instantiate usertype arg', arg, arg.type)
                        realGenericArgs.append(arg)
                else:
                    # print('GenericClass.instantiate arg', arg, arg.type)
                    realGenericArgs.append(arg)
            elif isinstance(arg, GenericVariadicTypeArg):
                realGenericArgs.append(arg)
            else:
                assert isinstance(arg, GenericLiteralArg), (arg)
                realGenericArgs.append(arg)
        return realGenericArgs
    def find(self, genericArgs):
        checkGenericArgsCompatible(self.genericParams, genericArgs)
        for cls in self.classes:
            if self.checkMatch(cls.instantiation.genericArgs, genericArgs):
                return cls
        return None
    def cache(self, cls):
        self.classes.append(cls)
    def isValidType(self, t):
        return isinstance(t, (UserType, FuncSpec))
    def checkMatch(self, x, y):
        checkGenericArgsCompatible(self.genericParams, x)
        checkGenericArgsCompatible(self.genericParams, y)
        assert isinstance(x, list) and isinstance(y, list), ('checkMatch', x, y)
        if len(x) != len(y):
            assert False, (x, y)
            return False
        for i in range(len(x)):
            argx = x[i]
            argy = y[i]
            if isinstance(argx, GenericTypeArg):
                assert isinstance(argy, GenericTypeArg)
                # print('GenericInstantiator', argx.type, argy.type, argx, argy)
                if not isSameType(argx.type, argy.type):
                    return False
            elif isinstance(argx, GenericVariadicTypeArg):
                assert isinstance(argy, GenericVariadicTypeArg)
                if len(argx.types) != len(argy.types):
                    return False
                for j in range(len(argx.types)):
                    xt = argx.types[j]
                    yt = argy.types[j]
                    if xt.getTypeClass() != yt.getTypeClass():
                        return False
            else:
                assert isinstance(argx, GenericLiteralArg) and isinstance(argy, GenericLiteralArg), (argx, argy)
        # print('checkMatch match', x[0], y[0])
        return True

class GenericInstantiation(object):
    def __init__(self, genericParams, genericArgs):
        checkGenericArgsCompatible(genericParams, genericArgs)
        # print('GenericClassImpl.init', name, genericParams, genericArgs)
        for t in genericArgs:
            pass
            # assert t.getTarget(), ('GenericClassImpl.init', name, genericParams, genericArgs, t)
            if isinstance(t, GenericTypeArg):
                if isinstance(t.type, UserType):
                    assert t.type.fullpath not in ['KeyType', 'ValueType', 'ElementType'], ('GenericClassImpl.init', self, genericParams, genericArgs, t, t.type, t.type.getTarget())
            elif isinstance(t, GenericVariadicTypeArg):
                for ta in t.types:
                    if isinstance(ta, UserType):
                        assert ta.fullpath not in ['KeyType', 'ValueType', 'ElementType'], ('GenericClassImpl.init', self, genericParams, genericArgs, t, ta, ta.getTarget())
        self.genericParams = genericParams
        self.genericArgs = genericArgs
        assert len(genericParams) == len(genericArgs)
        self.namedGenericArgs = {}
        for i in range(len(genericArgs)):
            param = genericParams[i]
            arg = genericArgs[i]
            if isinstance(param, (GenericTypeParam, GenericVariadicTypeParam)):
                assert isinstance(arg, (GenericTypeArg, GenericVariadicTypeArg)), (param, arg)
                self.namedGenericArgs[param.name] = arg
            elif isinstance(param, GenericLiteralParam):
                assert isinstance(arg, (GenericLiteralArg, GenericTypeArg)), (param, arg, param.type.getTypeClass())
                if param.mayBeTypeParam():
                    assert isinstance(arg, GenericTypeArg), (param, arg, param.type.getTypeClass())
                    self.namedGenericArgs[param.type.fullpath] = arg
                else:
                    assert isinstance(arg, GenericLiteralArg) and param.type.getTypeClass(), (param, arg, param.type.getTypeClass())
            else:
                assert False, (param, arg)
                assert isinstance(param, GenericLiteralParam) and isinstance(arg, GenericLiteralArg), (param, arg)
    def findLocalSymbol(self, name):
        # print('GenericClassImpl.findLocalSymbol', name, self)
        gt = self.namedGenericArgs.get(name, None)
        # print('GenericClassImpl.findLocalSymbol result', name, self, gt)
        return gt.type if gt else None

class ClassDef(Definition, AstFullContext):
    def __init__(self, scripts, name, genericParams, bases, fields, definitions, classType):
        AstFullContext.__init__(self)
        # assert name != 'NameResolver', (name, bases, definitions)
        self.constructors = []
        self.name = name
        self.genericParams = genericParams
        self.classType = classType
        self.definitions = definitions
        self.bases = bases
        self.scripts = scripts if scripts else []
        self.resolved = False
        self.type_name_resolved = False
        self.subclasses = []
        self.singleton = False
        self.ownercls = None
        self.script_processed = False
        assert len(self.scripts) < 10
        self.primaryVars = [SingleVarDef(v.name, v.getType().clone(), None) for v in fields]
        self.fields = []
        self.definitions.extend(self.primaryVars)
        self.mixin_vars = {}
        self.instantiator = None
        self.instantiation = None
        self.loggerVar = None
    def getType(self):
        return self
    def getTypeClass(self):
        return self
    def getSpec(self):
        return self.constructors[0].getSpec()
    def findMember(self, name):
        # print('ClassDef.findMember', self, name, self.owner)
        node = self.symbols.get(name)
        if node:
            return node
        #? findMember shouldnot search in generic instantiation
        # if self.instantiation:
        #     node = self.instantiation.findLocalSymbol(name)
        #     if node:
        #         return node
        for base in self.bases:
            node = base.getTarget().findMember(name) if base.getTarget() else None
            if node:
                return node
        return None
    def findLocalSymbol(self, name):
        # print('ClassDef.findLocalSymbol', name, self, self.symbols.get(name))
        node = self.symbols.get(name)
        if node:
            return node
        if self.instantiation:
            node = self.instantiation.findLocalSymbol(name)
            if node:
                return node
        for base in self.bases:
            node = base.getTarget().findLocalSymbol(name) if base.getTarget() else None
            if node:
                return node
        return None
    def __repr__(self):
        return 'ClassDef(%s,id=%s,generic=%s,%s)' % (self.name, formatId(self), self.genericParams, self.instantiation)
    def isProtoType(self):
        return self.genericParams and self.instantiation is None
    def isInstantiation(self):
        return self.instantiation is not None
    def isSimpleClass(self):
        return not self.genericParams
    def visitChildren(self, visitor):
        if self.isProtoType():
            # assert len(self.genericParams) == 0, (self, self.name, self.genericParams)
            # assert self.name != 'DeepAnalyzer', (self, self.name, self.genericParams)
            # print('ClassDef.visitChildren ignore', self, self.name, self.genericParams, visitor)
            for p in self.genericParams[:]:
                p.visit(visitor)
            return
        for p in self.genericParams[:]:
            p.visit(visitor)
        for b in self.bases[:]:
            b.visit(visitor)
        for d in self.definitions[:]:
            d.visit(visitor)
    def instantiate(self, genericArgs, visitor):
        # print('instantiate', self, self.genericParams, genericArgs, visitor)
        if self.instantiator is None:
            self.instantiator = GenericInstantiator(self.genericParams)
        realGenericArgs = self.instantiator.getRealArgs(genericArgs)
        cls = self.instantiator.find(realGenericArgs)
        if cls:
            # print('GenericClass.instantiate existing', self.name, self, genericArgs, realTypeArgs, cls.genericArgs)
            return cls
        cls = self.clone()
        # cls.genericArgs = genericArgs
        cls.instantiation = GenericInstantiation(self.genericParams, genericArgs)
        # print('GenericClass.instantiate new', self.name, self, realGenericArgs, cls.genericArgs)
        self.instantiator.cache(cls)
        visitor.setupNewItem(cls, self, True)
        return cls
    def isClass(self):
        return True

class EnumDef(BlockDefinition):
    def __init__(self, name, items, type=None):
        BlockDefinition.__init__(self)
        self.name = name
        self.type = UserType([name])
        self.items = items
        nextVal = 0
        for item in self.items:
            # print('EnumDef.addName', item.name, item)
            self.addSymbol(item)
            if item.value is None:
                item.value = makeLiteral(nextVal)
            else:
                nextVal = item.value.value
            item.type = UserType([name])
            nextVal += 1
    def getTypeClass(self):
        return self
    def getType(self):
        return self.type
    def getTarget(self):
        return self
    def findMember(self, name):
        # print('EnumDef.findMember', self, name, self.owner)
        return self.findLocalSymbol(name)

class Identifier(SimpleExpression):
    '''
    could point to a variable or user-defined getType()
    '''
    def __init__(self, name):
        # print('Identifier.init', name, formatId(self))
        SimpleExpression.__init__(self)
        self.name = name
        self.target = None
    def getType(self):
        assert self.target is None or isinstance(self.target, AstNode)
        return self.target.getType() if self.target else None
    def getSpec(self):
        return self.getTarget().getSpec() if self.getTarget() else None
    def __repr__(self):
        return 'ID(%s,%s)' % (self.name, formatId(self))

class Param(SimpleNode):
    def __init__(self, name, type):
        # assert isinstance(argtype, Type), (name, argtype)
        SimpleNode.__init__(self)
        self.name = name
        self.type = type
        assert not isinstance(type, str), (self, type)
    def getType(self):
        return self.type
    def getTypeClass(self):
        return self.getType().getTypeClass()
    def __repr__(self):
        return 'Param:%s:%s' % (self.name, self.getType())

class VarTag(SimpleNode):
    def __init__(self, name, type):
        # assert isinstance(argtype, Type), (name, argtype)
        SimpleNode.__init__(self)
        self.name = name
        self.type = type
        assert not isinstance(type, str), (self, type)
    def getType(self):
        return self.type
    def getTypeClass(self):
        return self.getType().getTypeClass()
    def __repr__(self):
        return 'VarTag:%s:%s' % (self.name, self.getType())

FuncType = xutils.Enum('FuncType', 'normal', 'constructor', 'destructor')
ClassType = xutils.Enum('ClassType', 'normal', 'interface', 'trait')

class FuncSpec(Type):
    def __init__(self, params, returnType):
        Type.__init__(self)
        for param in params:
            assert isinstance(param, Param), param
        self.params = params
        self.returnType = returnType
        self.static = False
        # self.cls = None
        self.typeClass = None
        # print('FuncSpec.init', params, returnType, formatId(self))
    def getTypeClass(self):
        return self.typeClass
    def __repr__(self):
        return 'FuncSpec:0x%08x(%s;%s)' % (id(self), self.params, self.returnType)

class FuncProto(BlockDefinition):
    def __init__(self, name, spec, receiver = None):
        assert(isinstance(name, str))
        BlockDefinition.__init__(self)
        self.name = name
        self.spec = spec
        assert not isinstance(receiver, str)
        self.receiver = receiver
        self.injected = receiver is not None
    def isFunc(self):
        return True
    def __repr__(self):
        return ('FuncProto(%s,%s,%s)' % (self.name, formatId(self), self.spec))
    def getTypeClass(self):
        return self.spec.getTypeClass()

class FuncModifiers(object):
    def __init__(self):
        self.isStatic = False

class FuncInfo(object):
    def __init__(self):
        self.type = FuncType.normal
        self.dispatched = False

class FuncDef(BlockDefinition):
    def __init__(self, scripts, name, spec, body, receiver = None):
        # print('FuncDef.init', name, spec, formatId(self))
        BlockDefinition.__init__(self)
        assert spec
        assert isinstance(body, StatementBody) and body, body
        assert not isinstance(receiver, str)
        assert isinstance(scripts, list), (scripts, name)
        self.info = FuncInfo()
        self.scripts = scripts
        self.name = name
        self.receiver = receiver
        self.injected = receiver is not None
        self.spec = spec
        self.body = body
        self.ownercls = None
        self.resolved = False
        self.injection_cls = None
        self.cls = None
    def isFunc(self):
        return True
    def getSpec(self):
        return self.spec
    def getType(self):
        return self.spec
    def doSetType(self, t):
        assert False
    def getTypeClass(self):
        return self.spec.getTypeClass()
    def shortname(self):
        return 'FuncDef(%s.%s)' % (self.cls.name, self.name) if self.cls else 'FuncDef(%s)' % self.name
    def __repr__(self):
        clsname = self.cls.name + '.' if self.cls else ''
        if not clsname and isinstance(self.owner, ExtensionDef):
            clsname = '.' + self.owner.name
        return ('FuncDef(%s%s,id=%s,%s,%d)' % (clsname, self.name, formatId(self), self.spec, len(self.body.statements)))


class ConstSpec(SimpleDefinition):
    def __init__(self, name, vartype, initial):
        # print('ConstSpec', name, vartype, initial)
        SimpleDefinition.__init__(self)
        self.name = name
        self.type = vartype
        self.initial = initial
        if self.getType() is None and self.initial:
            self.type = self.initial.getType()
    def getType(self):
        return self.type
    def getTarget(self):
        return self
    def getTypeClass(self):
        return self.getType().getTypeClass()
    def __repr__(self):
        return 'ConstSpec(name=%s,type=%s,initial=%s)' % (self.name, self.getType(), self.initial)

class ConstDef(SimpleDefinition):
    def __init__(self, vars):
        # print('ConstDef', vars)
        SimpleDefinition.__init__(self)
        assert(len(vars) > 0)
        self.vars = vars
    def __repr__(self):
        return ('ConstDef:%d %s' % (len(self.vars), self.vars))

class SingleVarDef(SimpleDefinition):
    def __init__(self, name, type, initial):
        # print('SingleVarDef.init', name, type, initial, '0x%08x' % id(self))
        assert type is None or isinstance(type, Type), (name, type, initial)
        SimpleDefinition.__init__(self)
        self.name = name
        self.type = type
        self.expectedType = None
        self.initial = initial
        self.cls = None
        self.internal = False
        if self.getType() is None and self.initial:
            self.type = self.initial.getType()
        assert self.type is None or isinstance(self.type, Type), (name, type, self.type, initial)
    def isVar(self):
        return True
    def getSpec(self):
        return self.getTypeClass().getSpec() if self.getTypeClass() else None
    def getType(self):
        return self.type
    def getTarget(self):
        return self
    def getTypeClass(self):
        # print('SingleVarDef.getTypeClass', self, self.getType())
        return self.getType().getTypeClass() if self.getType() else None
    def __repr__(self):
        return 'SingleVarDef(name=%s,id=0x%08x,type=%s,initial=%s)' % (self.name, id(self), self.getType(), self.initial)

class TupleVarDef(SimpleDefinition):
    def __init__(self, vars, type, initial):
        # print('SingleVarDef', name, type, initial, '0x%08x' % id(self))
        SimpleDefinition.__init__(self)
        assert len(vars) > 1, (vars, type, initial)
        self.vars = vars
        self.type = type
        self.expectedType = None
        self.initial = initial
        self.cls = None
        if self.getType() is None and self.initial:
            self.type = self.initial.getType()
        if self.type:
            assert len(self.vars) == len(self.type.elementTypes)
            for i in range(len(self.vars)):
                self.vars[i].setType(self.type.elementTypes[i])
    def getSpec(self):
        return self.getTypeClass().getSpec() if self.getTypeClass() else None
    def getType(self):
        return self.type
    def getTarget(self):
        return self
    def getTypeClass(self):
        # print('SingleVarDef.getTypeClass', self, self.getType(), self.getType().getTypeClass())
        return self.getType().getTypeClass()
    def __repr__(self):
        return 'TupleVarDef(vars=%s,id=0x%08x,type=%s,initial=%s)' % (self.vars, id(self), self.getType(), self.initial)

class MultipleVarDef(SimpleDefinition):
    def __init__(self, vars):
        # print('MultipleVarDef', vars)
        SimpleDefinition.__init__(self)
        assert(len(vars) > 0)
        self.vars = vars
    def __repr__(self):
        return ('MultipleVarDef:%d %s' % (len(self.vars), self.vars))

class TypeDef(SimpleDefinition):
    def __init__(self, name, target):
        SimpleDefinition.__init__(self)
        self.name = name
        self.target = target
    def getTypeClass(self):
        return self.target.getTypeClass()
    def getType(self):
        return self.target.getType()
    def dump(self, out, depth):
        out.write('%s TypeDef:%s %s' % (depth * 4 * ' ', self.name, self.target))

def unescapeString(s):
    return s.decode('string_escape')

class PrimitiveLiteral(Literal):
    def __init__(self, text, type, value=None):
        assert isinstance(type, UserType), ('PrimitiveLiteral', text, type, value)
        assert isinstance(text, str), ('PrimitiveLiteral', text, type, value)
        Literal.__init__(self)
        self.text = text
        self.type = type
        self.value = value if value is not None else text
        if type.fullpath in ['string', 'char']:
            self.value = unescapeString(text)
    def __repr__(self):
        return '%s:%s:%s:%s:%s' % (self.__class__.__name__, self.text, self.getType().fullpath, self.value, type(self.value))

class StringLiteral(PrimitiveLiteral):
    def __init__(self, text, value=None):
        PrimitiveLiteral.__init__(self, text, builtinStringType, value)

class IntLiteral(PrimitiveLiteral):
    def __init__(self, text, value=None):
        PrimitiveLiteral.__init__(self, text, builtinIntType, value)

class LongLiteral(PrimitiveLiteral):
    def __init__(self, text, value=None):
        PrimitiveLiteral.__init__(self, text, builtinLongType, value)

class BoolLiteral(PrimitiveLiteral):
    def __init__(self, text, value=None):
        PrimitiveLiteral.__init__(self, text, builtinBoolType, value)

class CharLiteral(PrimitiveLiteral):
    def __init__(self, text, value=None):
        PrimitiveLiteral.__init__(self, text, builtinCharType, value)

class FloatLiteral(PrimitiveLiteral):
    def __init__(self, text, value=None):
        PrimitiveLiteral.__init__(self, text, builtinFloatType, value)


class StringEvaluation(SimpleExpression):
    def __init__(self, literal):
        SimpleExpression.__init__(self)
        self.literal = literal
        self.evaluation = None
        self.type = makePrimitiveType('string')
    def getType(self):
        return self.literal.getType()
    def visitChildren(self, visitor):
        self.literal.visit(visitor)
        if self.evaluation:
            self.evaluation.visit(visitor)
    def __repr__(self):
        return 'StringEvaluation(id=%s,%s)' % (formatId(self), self.literal)

class ListLiteral(Literal):
    def __init__(self, values):
        Literal.__init__(self)
        self.values = values
        self.type = None
        self.setExpectedType(None)
        for val in values:
            assert isinstance(val, AstNode), (val, values, self)
        # print('ListLiteral.init', values)
    def getTypeClass(self):
        return self.getType().getTypeClass()
    def __repr__(self):
        return 'ListLiteral(%s,%s,getType()=%s)' % (len(self.values), self.values, self.getType())

class TupleLiteral(Literal):
    def __init__(self, values):
        Literal.__init__(self)
        self.values = values
        self.type = None
        self.setExpectedType(None)
        # print('TupleLiteral.init', values)
    def __repr__(self):
        return 'TupleLiteral:%s:%s' % (len(self.values), self.values)
    def setExpectedType(self, t):
        assert t is None or (isinstance(t, UserType) and t.fullpath == 'Tuple'), ('TupleLiteral.setExpectedType', self, t)
        Literal.setExpectedType(self, t)

class NamedTypeItem(SimpleNode):
    def __init__(self, name, type):
        SimpleNode.__init__(self)
        self.name = name
        self.type = type
    def __repr__(self):
        return 'NamedTypeItem:%s:%s' % (self.name, self.type)

class NamedExpressionItem(SimpleNode):
    def __init__(self, name, value):
        SimpleNode.__init__(self)
        self.name = name
        self.value = value
    def getType(self):
        return self.value.getType()
    def __repr__(self):
        return 'NamedExpressionItem:%s:%s' % (self.name, self.value)

class DictItem(SimpleNode):
    def __init__(self, key, value):
        SimpleNode.__init__(self)
        self.key = key
        self.value = value
        # print('DictItem', self)
        # print('DictItem.transform', self, self.key, self,val)
    def __repr__(self):
        return 'DictItem:%s:%s' % (self.key, self.value)

class DictLiteral(Literal):
    def __init__(self, values):
        Literal.__init__(self)
        self.values = values
        self.type = None
        # print('DictLiteral', self)
    def __repr__(self):
        return 'DictLiteral:%s:%s' % (len(self.values), self.values)

class SetLiteral(Literal):
    def __init__(self, values):
        Literal.__init__(self)
        self.values = values
        self.type = None
        # print('SetLiteral', self)
    def __repr__(self):
        return 'SetLiteral:%s:%s' % (len(self.values), self.values)

class ListComprehensionFor(SimpleExpression):
    def __init__(self, variable, source, condition):
        SimpleExpression.__init__(self)
        self.variable = variable
        self.source = source
        self.condition = condition
    def __repr__(self):
        return 'ListComprehensionFor:%s:%s' % (self.variable, self.source)

class ListComprehension(BlockExpression):
    def __init__(self, expr, fors):
        assert not isinstance(expr, ListLiteral), (expr, fors)
        BlockExpression.__init__(self)
        self.expr = expr
        self.fors = fors
        self.type = None
    def getType(self):
        return self.type
    def __repr__(self):
        return 'ListComprehension:id=%s:%s:%s' % (formatId(self), self.expr, len(self.fors))

def makePrimitiveType(name):
    return UserType([name])

class UserType(Type):
    def __init__(self, path, genericArgs=None):
        assert(path)
        Type.__init__(self)
        self.path = path
        self.fullpath = '.'.join(path)
        self.genericArgs = genericArgs or []
        for t in self.genericArgs:
            assert isinstance(t, GenericArg), ('UserType.init check generic arg', path, t, self.genericArgs)
        self.target = None
    def getType(self):
        return self.target.getType() if isinstance(self.target, UserType) else self
    def setTarget(self, t):
        self.target = t
    def getTarget(self):
        return self.target
    def getRealType(self):
        if isinstance(self.target, (UserType)):
            return self.target.getRealType()
        return self
    def getItemType(self):
        # print('UserType.getItemType', self.fullpath, self.target)
        return self.target.getItemType() if self.target else None
    def getKeyType(self):
        return self.target.getKeyType() if self.target else None
    def getValueType(self):
        return self.target.getValueType() if self.target else None
    def getTypeClass(self):
        assert self.getTarget() != self
        if isinstance(self.target, UserType):
            return self.target.getTypeClass()
        return self.target
    def shortname(self):
        return self.fullpath
    def clone(self):
        if isinstance(self.target, UserType):
            return self.target.clone()
        x = UserType(path=self.path, genericArgs=[t.clone() for t in self.genericArgs])
        x.target = self.target
        return x
    def __repr__(self):
        return 'UserType:%s,id=%s,owner=%s,genericArgs=,type_class=%s' % ('.'.join(self.path), formatId(self), formatId(self.owner) if self.owner else None, self.getTypeClass())

class PointerType(Type):
    def __init__(self, elementType):
        Type.__init__(self)
        self.elementType = elementType
        self.typeClass = None
    def getTypeClass(self):
        return self.elementType.getTypeClass()
    def __repr__(self):
        return 'PointerType(%s,%s)' % (self.elementType, self.getTypeClass())

class GenericExpr(SimpleExpression):
    def __init__(self, base, genericArgs):
        SimpleExpression.__init__(self)
        self.base = base
        self.genericArgs = genericArgs
        self.target = None
    def getTarget(self):
        return self.target
    def getType(self):
        # assert False, (self, self.base, self.genericArgs, self.base.getType(), self.base.getTarget())
        return self.target.getType() if self.target else None

class Call(SimpleExpression):
    def __init__(self, caller, args, namedArgs = None):
        # print('Call', caller, args)
        SimpleExpression.__init__(self)
        assert isinstance(caller, AstNode), (caller, args, namedArgs)
        assert isinstance(namedArgs, list) or namedArgs is None, (caller, args, namedArgs)
        self.caller = caller
        self.args = args
        self.namedArgs = namedArgs if namedArgs else []
        for arg in self.namedArgs:
            assert isinstance(arg, NamedExpressionItem), arg
        self.type = None
        self.spec = None
    def getSpec(self):
        # print('Call.getSpec', self.caller, self.args)
        return self.caller.getSpec()
    def getType(self):
        # typeclass = self.caller.getTypeClass() if self.caller.getTypeClass() else None
        # return typeclass.returnType if typeclass else None
        spec = self.getSpec()
        # print('Call.getType', self.caller, self.args, spec)
        return spec.returnType if spec else None 
    def dump(self, out, depth):
        out.write('%s %s\n' % (depth * 4 * ' ', self.fullstr()))
    def __repr__(self):
        return 'Call(%s(%s:%s):%s,id=%s)' % (self.caller, self.args, self.namedArgs, self.getType(), formatId(self))
    def fullstr(self):
        return 'Call(%s,%s,%s,%s)' % (self.caller, self.args, self.namedArgs, self.getType())

class Subscript(SimpleExpression):
    def __init__(self, collection, key):
        SimpleExpression.__init__(self)
        self.collection = collection
        self.key = key
    def getType(self):
        return self.collection.getType().getItemType() if self.collection.getType() else None
    def __repr__(self):
        return 'Subscript(id=%s,coll=%s,key=%s)' % (formatId(self), self.collection, self.key)
    def is_composite(self):
        return False

class Slicing(SimpleExpression):
    def __init__(self, collection, start, stop, step):
        SimpleExpression.__init__(self)
        self.collection = collection
        self.start = start
        self.stop = stop
        self.step = step
        self.type = None
    def getType(self):
        return self.collection.getType()
    def __repr__(self):
        return 'Slicing:%s:%s:%s:%s' % (self.collection, self.start, self.stop, formatId(self))

class Break(SimpleStatement):
    def __init__(self):
        SimpleStatement.__init__(self)
    def dump(self, out, depth):
        out.write('%s break\n' % (depth * 4 * ' '))

class Continue(SimpleStatement):
    def __init__(self):
        SimpleStatement.__init__(self)

class AssertStatement(SimpleStatement):
    def __init__(self, expr, msg = None):
        assert expr, expr
        SimpleStatement.__init__(self)
        self.expr = expr
        self.msg = msg
    def dump(self, out, depth):
        out.write('%s Assert %s, %s\n' % (depth * 4 * ' ', self.expr, self.msg))

class Return(SimpleStatement):
    def __init__(self, value):
        assert not isinstance(value, list), value
        SimpleStatement.__init__(self)
        self.value = value
    def __repr__(self):
        return 'Return(%s)' % self.value
    def dump(self, out, depth):
        out.write('%s Return: %s\n' % (depth * 4 * ' ', self.value))

class CompoundStatement(BlockStatement):
    def __init__(self):
        # print('CompoundStatement.init 0x%08x' % id(self))
        BlockStatement.__init__(self)
        assert len(self.symbols) == 0

class StatementBody(SimpleNode):
    def __init__(self, statements):
        assert statements is not None
        SimpleNode.__init__(self)
        self.statements = statements
        for stmt in statements:
            assert stmt, statements
    def __repr__(self):
        return 'StatementBody(id=%s,count=%d)' % (formatId(self), len(self.statements))
    def dump(self, out, depth):
        out.write('%s StatementBody: %d\n' % (depth * 4 * ' ', len(self.statements)))
        for stmt in self.statements:
            # print('StatementBody.dump item', stmt, self)
            stmt.dump(out, depth + 1)

class StatementBlock(CompoundStatement):
    def __init__(self, body):
        # print('StatementBlock 0x%08x' % id(self))
        CompoundStatement.__init__(self)
        assert isinstance(body, StatementBody) and body, body
        self.body = body
    def dump(self, out, depth):
        out.write('%s StatementBlock:\n' % (depth * 4 * ' '))
        self.body.dump(out, depth+1)

class WhileStatement(CompoundStatement):
    def __init__(self, condition, body):
        CompoundStatement.__init__(self)
        assert isinstance(body, StatementBody) and body, body
        self.condition = condition
        self.body = body
    def dump(self, out, depth):
        out.write('%s While:%s\n' % (depth * 4 * ' ', self.cond))
        self.body.dump(out, depth)

class DoWhileStatement(CompoundStatement):
    def __init__(self, condition, body):
        assert isinstance(body, StatementBody) and body, body
        CompoundStatement.__init__(self)
        self.condition = condition
        self.body = body
        #initContext(self)
    def dump(self, out, depth):
        out.write('%s DoWhile:%s\n' % (depth * 4 * ' ', self.cond))
        self.body.dump(out, depth)

class ForEachStatement(CompoundStatement):
    def __init__(self, item, collection, body):
        assert isinstance(body, StatementBody) and body, body
        # print('ForEachStatement %s 0x%08x %s' % (name, id(self), stmtblock))
        CompoundStatement.__init__(self)
        self.item = item
        self.collection = collection
        self.body = body
    def dump(self, out, depth):
        out.write('%s ForEachStatement:%s:%s\n' % (depth * 4 * ' ', self.item, self.collection))
        self.body.dump(out, depth)

class ForEachDictStatement(CompoundStatement):
    def __init__(self, key, value, collection, body):
        assert isinstance(body, StatementBody) and body, body
        CompoundStatement.__init__(self)
        self.key = key
        self.value = value
        self.collection = collection
        self.body = body
    def dump(self, out, depth):
        out.write('%s ForEachDict:%s:%s:%s\n' % (depth * 4 * ' ', self.key, self.value, self.collection))
        self.body.dump(out, depth)

class ForStatement(CompoundStatement):
    def __init__(self, init, condition, step, body):
        assert isinstance(body, StatementBody) and body, body
        CompoundStatement.__init__(self)
        assert self.symbols is not None, (self, self.owner)
        assert init is None or isinstance(init, AstNode), (init, condition, step, body)
        assert step is None or isinstance(step, AstNode), (init, condition, step, body)
        self.init = init
        self.condition = condition
        self.step = step
        self.body = body
        # print('ForStatement.init', formatId(self), init, condition, step, body)
    def dump(self, out, depth):
        out.write('%s For:%s:%s:%s\n' % (depth * 4 * ' ', self.init, self.condition, self.step))
        self.body.dump(out, depth)

class WithStatement(CompoundStatement):
    def __init__(self, expr, body):
        assert isinstance(body, StatementBody) and body, body
        CompoundStatement.__init__(self)
        assert self.symbols is not None, (self, self.owner)
        self.expr = expr
        self.body = body
        # print('ForStatement.init', formatId(self), init, condition, step, body)
    def dump(self, out, depth):
        out.write('%s With:%s\n' % (depth * 4 * ' ', self.expr))
        self.body.dump(out, depth)

class UsingStatement(CompoundStatement):
    def __init__(self, variable, body):
        assert isinstance(body, StatementBody) and body, body
        CompoundStatement.__init__(self)
        assert self.symbols is not None, (self, self.owner)
        self.variable = variable
        self.body = body
        # print('ForStatement.init', formatId(self), init, condition, step, body)
    def dump(self, out, depth):
        out.write('%s Using:%s\n' % (depth * 4 * ' ', self.expr))
        self.body.dump(out, depth)

class IfBranch(SimpleNode):
    def __init__(self, condition, body):
        assert isinstance(body, StatementBody) and body, body
        assert condition and body, (condition, body)
        SimpleNode.__init__(self)
        self.condition = condition
        self.body = body

class IfStatement(CompoundStatement):
    def __init__(self, branches, elseBranch):
        CompoundStatement.__init__(self)
        for branch in branches:
            assert branch, branches
        self.branches = branches
        self.elseBranch = elseBranch
    def dump(self, out, depth):
        out.write('%s If:%s:%s' % (depth * 4 * ' ', self.branches, self.elseBranch))

class CaseVarSpec(SimpleNode):
    def __init__(self, variable):
        SimpleNode.__init__(self)
        self.variable = variable
    def __repr__(self):
        return 'CaseVarSpec:%s' % (self.variable)
    def getTarget(self):
        return self.variable

class CaseEntryExpr(BlockNode):
    def __init__(self, pattern, expr):
        # print('CaseEntryExpr.init', pattern, expr)
        BlockNode.__init__(self)
        self.pattern = pattern
        self.expr = expr
        assert not isinstance(pattern, list), (expr, pattern)
        assert not isinstance(expr, list), (expr, pattern)
    def __repr__(self):
        return 'CaseEntryExpr(id=%s,pattern=%s)' % (formatId(self), self.pattern)
    def findSymbol(self, name):
        # print('CaseEntryExpr.findSymbol', name, self, self.owner)
        node = self.findLocalSymbol(name)
        if node:
            # print('findSymbol found:', name, node, self)
            return node
        if isinstance(self.pattern, Identifier):
            target = self.pattern.getTarget()
            if isinstance(target, ClassDef):
                if self.owner.matchVar:
                    pass
                else:
                    node = target.findSymbol(name)
                if node:
                    return node
        if self.owner is None:
            # print('CaseEntryExpr.findSymbol failed:', name, self)
            return None
        # print('CaseEntryExpr.findSymbol in owner:', name, self.owner)
        return self.owner.findSymbol(name)

class CaseEntryStmt(BlockNode):
    def __init__(self, pattern, body):
        assert isinstance(body, StatementBody) and body, body
        BlockNode.__init__(self)
        self.pattern = pattern
        self.body = body
        # self.names = {}
        assert not isinstance(pattern, list), (body, pattern)
        # assert isinstance(body, list), (body, pattern)
        # print('CaseEntryStmt.init', pattern, body)
    def findSymbol(self, name):
        # print('CaseEntryStmt.findSymbol', name, self, self.owner)
        node = self.findLocalSymbol(name)
        if node:
            # print('CaseEntryStmt.findSymbol found:', name, node, self.pattern, self)
            return node
        if self.pattern and isinstance(self.pattern, Identifier):
            target = self.pattern.getTarget()
            if isinstance(target, ClassDef):
                if self.owner.matchVar:
                    pass
                else:
                    # print('CaseEntryStmt.findSymbol pattern', name, self.pattern, self, self.owner)
                    node = target.findSymbol(name)
                    # print('CaseEntryStmt.findSymbol pattern ret', name, self.pattern, self, self.owner)
                if node:
                    return node
        if self.owner is None:
            # print('CaseEntryStmt.findSymbol failed:', name, self)
            return None
        # print('CaseEntryStmt.findSymbol in owner:', name, self.owner)
        return self.owner.findSymbol(name)

class CaseEntry(BlockNode):
    def __init__(self, value, body):
        assert isinstance(body, StatementBody) and body, body
        BlockNode.__init__(self)
        self.value = value
        self.body = body

class CaseBlock(SimpleNode):
    def __init__(self, entries):
        SimpleNode.__init__(self)
        self.entries = entries
        self.matchVar = None
    def getType(self):
        return self
    def getTypeClass(self):
        return self

class SwitchCaseStatement(CompoundStatement):
    def __init__(self, expr, entries):
        CompoundStatement.__init__(self)
        self.expr = expr
        self.entries = entries
    def dump(self, out, depth):
        out.write('%s SwitchCase:%s:%d\n' % (depth * 4 * ' ', self.expr, len(self.entries)))

class IfElseExpr(SimpleExpression):
    def __init__(self, condition, truePart, falsePart):
        SimpleExpression.__init__(self)
        self.condition = condition
        self.truePart = truePart
        self.falsePart = falsePart
    def getType(self):
        return self.truePart.getType() if self.truePart.getType() else self.falsePart.getType()
    def __repr__(self):
        return 'IfElseExpr(%s,%s,%s)' % (self.condition, self.truePart, self.falsePart)

class BinaryOp(SimpleExpression):
    def __init__(self, op, left, right):
        # print('BinaryOp.init', left, right, op)
        assert isinstance(op, str), (op, left, right)
        SimpleExpression.__init__(self)
        self.left = left
        self.right = right
        self.op = op
        #print('BinaryOp', left, right, op, left.getType(), right.getType())
    def getType(self):
        if self.op in bool_ops_index:
            return builtinBoolType
        return self.left.getType() if self.left.getType() else self.right.getType()
    def __repr__(self):
        return 'BinaryOp:%s%s%s:%s' % (self.left, self.op, self.right, self.getType())

class UnaryOp(SimpleExpression):
    def __init__(self, op, operand):
        SimpleExpression.__init__(self)
        self.operand = operand
        self.op = op
        self.type = operand.getType()
    def getType(self):
        if self.op == '!':
            return builtinBoolType
        return self.operand.getType()
    def __repr__(self):
        return 'UnaryOp:op=%s,operand=%s' % (self.op, self.operand)

class TypeCast(SimpleExpression):
    def __init__(self, source, type):
        SimpleExpression.__init__(self)
        self.source = source
        self.type = type
    def getType(self):
        return self.type
    def __repr__(self):
        return 'TypeCast:source=%s,getType()=%s' % (self.source, self.getType())

class Assignment(SimpleStatement):
    def __init__(self, targets, op, values):
        assert isinstance(targets, list) and isinstance(values, list), (targets, op, values)
        assert len(targets) == len(values)
        SimpleStatement.__init__(self)
        self.targets = targets
        self.values = values
        self.op = op
    def dump(self, out, depth):
        out.write('%s Assignment: %s %s %s\n' % (depth * 4 * ' ', self.targets, self.op, self.values))
    def __repr__(self):
        return 'Assign(%s,%s,%s)' % (self.targets, self.op, self.values)

class CallStatement(SimpleStatement):
    def __init__(self, call):
        SimpleStatement.__init__(self)
        self.call = call
    def __repr__(self):
        return 'CallStatement:%s' % self.call
    def dump(self, out, depth):
        self.call.dump(out, depth)

class AttrRef(SimpleExpression):
    def __init__(self, object, ref):
        SimpleExpression.__init__(self)
        self.object = object
        self.ref = ref
        self.target = None
    def getSpec(self):
        # print('AttrRef.getSpec', self.object, self.ref, self.getTarget())
        return self.getTarget().getSpec() if self.getTarget() else None
    def getType(self):
        # print('AttrRef.getType', self.object, self.ref)
        return self.getTarget().getType() if self.getTarget() else None
    def __repr__(self):
        return 'AttrRef(%s.%s,id=%s,target=%s)' % (self.object, self.ref, formatId(self), self.getTarget())

class SimpleNativeCall(SimpleExpression):
    def __init__(self, name, caller, args):
        SimpleExpression.__init__(self)
        self.name = name
        self.caller = caller
        self.args = args

class NativeCaller(SimpleExpression):
    def __init__(self, name):
        SimpleExpression.__init__(self)
        self.name = name

class ArgumentPlaceholder(SimpleExpression):
    def __init__(self, sequence):
        SimpleExpression.__init__(self)
        self.sequence = sequence
        self.closure = None
    def getType(self):
        return self.closure.spec.params[self.sequence].type if self.closure else None

class Closure(BlockExpression):
    def __init__(self, spec, body):
        BlockExpression.__init__(self)
        assert isinstance(spec, FuncSpec) or spec is None, spec
        assert isinstance(body, StatementBody) and body, body
        self.body = body
        self.spec = spec
        # self.setTarget(self)
        self.stack = None
        # self.names = {}
    def getType(self):
        return self.spec
    def visitChildren(self, visitor):
        # print('Closure.visitChildren', self, visitor, self.getOwner(), self.getOwnerFunc())
        self.doVisitChildren(visitor)
    def evaluateParam(self, visitor):
        self.stack = visitor.getCurrentStack()
        return self
    def shortname(self):
        return 'Closure(id=%s,spec=%s)' % (formatId(self), self.spec)

class LocalClass(AstNode):
    def __init__(self, name):
        self.name = name

class IdPath(SimpleExpression):
    def __init__(self, path):
        SimpleExpression.__init__(self)
        self.path = path
        self.fullpath = '.'.join(path)
    def __repr__(self):
        return 'IdPath:%s' % (self.fullpath)

class LibClassBase(Type, AstBlockContext):
    def __init__(self):
        Type.__init__(self)
        AstBlockContext.__init__(self)
    def isClass(self):
        return True

class LibFuncBase(SimpleNode):
    def __init__(self):
        # print('LibFunc.init', cls, proto)
        SimpleNode.__init__(self)

class GoPackageInfo(BlockNode):
    def __init__(self, fullpath, path, declarations):
        self.fullpath = fullpath
        self.path = path
        self.declarations = declarations

class Script(SimpleNode):
    def __init__(self, caller, args, namedArgs):
        SimpleNode.__init__(self)
        self.caller = IdPath(caller)
        self.args = args
        self.namedArgs = namedArgs
        self.inherit = False
        for arg in self.namedArgs:
            assert isinstance(arg, NamedExpressionItem), arg
    def __repr__(self):
        return 'Script(%s:%s:args=%s)' % (self.caller.fullpath, formatId(self), self.args)
    def __setattr__(self, name, val):
        if name in []:
            raise TypeError
        if name == 'args':
            if hasattr(self, name):
                raise TypeError
        self.__dict__[name] = val
    def setTarget(self, t):
        self.target = t
    def getTarget(self):
        return self.target
    def dump(self, out, depth):
        out.write('Script:%s:%s\n' % (self.caller, self.args))

class ScriptFunction(SimpleNode):
    def __init__(self):
        SimpleNode.__init__(self)
        self.inherit = False
        self.spec = None
        self.name = None
        self.astFieldNames = ['spec']
    def visitChildren(self, visitor):
        pass
    def getTypeClass(self):
        return self
    def getSpec(self):
        return self.spec
    def getType(self):
        return self.type
    def getTarget(self):
        return self.target
    def cacheName(self, visitor):
        assert self.name
        self.getOwner().addSymbol(self)

def makeNativeCall(name, args):
    return Call(NativeCaller(name), args)

def makeLiteral(val):
    if isinstance(val, str):
        return StringLiteral(val)
    if isinstance(val, int):
        return IntLiteral(str(val), val)
    if isinstance(val, long):
        return LongLiteral(str(val), val)
    if isinstance(val, float):
        return FloatLiteral(str(val), val)
    if isinstance(val, list):
        return ListLiteral([makeLiteral(x) for x in val])
    assert False, val

def makeType(t):
    if t is None:
        return UserType(['void'])
    if isinstance(t, tuple):
        return UserType(['Tuple'], [GenericVariadicTypeArg(list(t))])
    if isinstance(t, list):
        assert(len(t) == 1)
        assert False
        return createListType(t[0])
    if isinstance(t, dict):
        assert(len(t) == 1)
        assert False
        return UserType(['Dict'], [t.items()[0][0], t.items()[0][1]])
    if t is int or t == 'int':
        return makePrimitiveType('int')
    if t is long or t == 'long':
        return makePrimitiveType('long')
    if t is float or t == 'float':
        return makePrimitiveType('float')
    if t is bool or t == 'bool':
        return makePrimitiveType('bool')
    if t == 'string':
        return makePrimitiveType('string')
    if t == 'char':
        return makePrimitiveType('char')
    assert False, t
    return None


def makeVar(name, vartype, initial):
    var = SingleVarDef(name, vartype, initial)
    return var

def createTupleVarDef(names, tupleType, initial):
    vars = [SingleVarDef(name, None, None) for name in names]
    return TupleVarDef(vars, tupleType, initial)

def isPrimitiveType(t, name):
    return isinstance(t, UserType) and t.fullpath == name

def createLibUnit(pkgpath, defs):
    assert isinstance(pkgpath, str), pkgpath
    return LibUnit('$'+ pkgpath, PackageDef(pkgpath.split('.')), defs)

def createLibClass(name):
    return ClassDef(name, [], [], [], [], ClassType.normal)

def createLibInterface(name):
    return ClassDef(name, [], [], [], [], ClassType.interface)

def createListType(elementType):
    return UserType(['List'], [GenericTypeArg(elementType)])

def createSetType(elementType):
    return UserType(['Set'], [GenericTypeArg(elementType)])

def createArrayType(elementType, sizeLiteral):
    return UserType(['Array'], [GenericTypeArg(elementType), GenericLiteralArg(sizeLiteral)])

def createDictType(keyType, valueType):
    return UserType(['Dict'], [GenericTypeArg(keyType), GenericTypeArg(valueType)])

def createTupleType(elementTypes):
    return UserType(['Tuple'], [GenericVariadicTypeArg(elementTypes)])

def createUserType(fullpath):
    return UserType(fullpath.split('.'))

builtinCharType = makePrimitiveType('char')
builtinBoolType = makePrimitiveType('bool')
builtinStringType = makePrimitiveType('string')
builtinIntType = makePrimitiveType('int')
builtinLongType = makePrimitiveType('long')
builtinFloatType = makePrimitiveType('float')

compare_ops = ['==', '>', '<', '<=', '>=', '!=']
logical_ops = ['and', 'or']
extra_bool_ops = ['in', 'not-in', 'is', 'is-not']
bool_ops = compare_ops + logical_ops + extra_bool_ops
bool_ops_index = dict(zip(bool_ops, bool_ops))
