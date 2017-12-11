
import ast
from basetype import LibClass, LibFunc
from scripts.classinfo import NameScript
from parser import parseFuncProto

class MetaClass(LibClass):
    def __init__(self, name):
        LibClass.__init__(self, name)
        self.target = None
    def dump(self, out, depth):
        out.write('%s MetaClass name=%s\n' % (depth * 4 * ' ', 'Meta:' + self.name))

class CallMethodScript(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
        self.name = 'callMethod'
        self.spec = parseFuncProto('callMethod()').spec
        self.returnType = self.spec.returnType
        self.target = self
    def getTypeClass(self):
        return self.getType().getTypeClass()
    def getType(self):
        return self.spec
    def getTarget(self):
        return self.target

class ClassNameScript(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
        self.name = 'name'
        self.type = ast.makePrimitiveType('string')
        self.target = None
    def getType(self):
        return self.type
    def getTarget(self):
        return self.target
    def evalLiteral(self, expander):
        assert False, ('ClassNameScript.evalLiteral', self, self.name, self.getOwnerFunc())
        cls = self.getOwnerClass()
        assert isinstance(cls, ast.ClassDef), (cls)
        return cls.name

class GetClassNameScript(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
        self.name = 'getClassName'
        self.type = ast.makePrimitiveType('string')
        self.target = None
    def getType(self):
        return self.type
    def resolveName(self, resolver):
        return self
    def evaluate(self, visitor):
        assert False, (self, visitor)

class CollectFunctionsMethodScript(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
        self.proto = parseFuncProto('collectFunctions() => [(string,gml.FuncDef)]')
        self.name = self.proto.name
        self.spec = self.proto.spec
        self.type = self.spec.returnType
    def evaluate(self, visitor):
        assert False, (self, visitor)
    def evaluateCall(self, visitor, callinfo):
        func = callinfo.getOwnerFunc()
        this = visitor.getThis()
        assert func and func.cls, (self, visitor, callinfo, func)
        assert this and this.cls, (self, visitor, callinfo, this)
        assert len(callinfo.args) == 1, (self, visitor, callinfo, func)
        tag = callinfo.args[0].visit(visitor)
        funcs = []
        for f in this.cls.functions:
            if f.name.startswith(tag):
                visitor.logger.debug('collect func', f, func)
                funcs.append((f.name[len(tag):], f))
        return funcs

class GetFunctionMethodScript(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
        self.proto = parseFuncProto('getFunction() => [(string,gml.FuncDef)]')
        self.name = self.proto.name
        self.spec = self.proto.spec
        self.type = self.spec.returnType
    def evaluate(self, visitor):
        assert False, (self, visitor)
    def evaluateCall(self, visitor, callinfo):
        func = callinfo.getOwnerFunc()
        this = visitor.getThis()
        assert func and func.cls, (self, visitor, callinfo, func)
        assert this and this.cls, (self, visitor, callinfo, this)
        assert len(callinfo.args) == 1, (self, visitor, callinfo, func)
        tag = callinfo.args[0].visit(visitor)
        funcs = []
        for f in this.cls.functions:
            if f.name.startswith(tag):
                visitor.logger.debug('collect func', f, func)
                funcs.append((f.name[len(tag):], f))
        return funcs

def createMetaClass():
    cls = MetaClass('Class')
    cls.addDef(ClassNameScript())
    cls.addDef(GetClassNameScript())
    cls.addDef(CallMethodScript())
    cls.addDef(CollectFunctionsMethodScript())
    assert cls, 'createMetaClass %s' % cls.name
    return cls

def loadAll():
    unit = ast.createLibUnit('sys.lang', [])
    print('sys.core.loadAll sys.lang', unit)
    unit.definitions.append(createMetaClass())
    return unit
