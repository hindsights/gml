import ast
from parser import parseFuncProto
import parser
import builtins

def getScriptQuialifiedName(path):
    if isinstance(path, ast.Identifier):
        return [path.name]
    if isinstance(path, ast.AttrRef):
        return getScriptQuialifiedName(path.obj) + [path.ref]
    assert False

class NameScript(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
        self.inherit = True
        # assert False
    def processScript(self, visitor, script):
        owner = script.owner
        assert isinstance(owner, ast.ClassDef), (script, script.owner)
        # visitor.logger.debug('NameScript.processScript', self, script, owner)
        cls = owner
        if not cls.hasSymbol('getClassName'):
            # visitor.logger.debug('NameScript.processScript add getClassName', self, script, owner)
            proto = parseFuncProto('getClassName() => string')
            stmts = [ast.Return(ast.makeLiteral(cls.name))]
            func = ast.FuncDef([], proto.name, proto.spec, ast.StatementBody(stmts))
            cls.definitions.append(func)
            func.setOwner(cls)
            visitor.visitNewItem(func)

class SingletonScript(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
    def processScript(self, visitor, script):
        owner = script.owner
        assert isinstance(owner, ast.ClassDef)
        cls = owner
        cls.singleton = True
        if not cls.hasSymbol('instance'):
            proto = parseFuncProto('instance() => %s' % owner.name)
            func = ast.FuncDef([], proto.name, proto.spec, ast.StatementBody([]))
            func.spec.static = True
            cls.definitions.append(func)
            func.setOwner(cls)
            visitor.visitNewItem(func)
            visitor.logger.debug('SingletonScript.processScript func', cls.name, func.name, cls, func)

class MixinScript(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
    def resolveName(self, visitor, script):
        owner = script.owner
        script.mixin_var_name = script.args[1].name
        script.mixin_propget_name = script.args[2].name
        owner.mixin_vars[script.mixin_var_name] = script
    def processScript(self, visitor, script):
        owner = script.owner
        # visitor.logger.debug('MixinScript.processScript', script, owner.bases, script.args)
        assert isinstance(owner, ast.ClassDef)
        script.mixin_var_type = ast.UserType(getScriptQuialifiedName(script.args[0]))
        script.mixin_var = ast.SingleVarDef(script.mixin_var_name, script.mixin_var_type, ast.Call(script.args[0].clone(), script.args[3:], script.namedArgs))
        proto = parseFuncProto('%s() => %s' % (script.mixin_propget_name, script.mixin_var_type.fullpath))
        script.mixin_propget = ast.FuncDef([], script.mixin_propget_name, proto.spec, ast.StatementBody([ast.Return(ast.Identifier(script.mixin_var_name))]))
        script.mixin_class = owner.resolveSymbol(script.mixin_var_type.path)
        # visitor.logger.debug('MixinScript.processScript add var', owner, script.owner, script, owner.bases, script.args, script.mixin_var)
        owner.definitions.append(script.mixin_var)
        script.mixin_var.setOwner(script.owner)
        owner.definitions.append(script.mixin_propget)
        script.mixin_propget.setOwner(script.owner)
        # visitor.logger.debug('MixinScript.processScript add var', owner, script.owner, script, owner.bases, script.args, script.mixin_var, script.mixin_var.owner)
        visitor.visitNewItem(script.mixin_var)
        visitor.visitNewItem(script.mixin_propget)
        self.addMixinFuncs(visitor, script, script.mixin_class, owner)
    def addMixinFuncs(self, visitor, script, mixincls, cls):
        for func in mixincls.functions:
            if func.info.type == ast.FuncType.normal and not func.injected:
                self.addMixinFunc(visitor, script, func, cls, mixincls)
        for base in mixincls.bases:
            basecls = cls.resolveSymbol(base.path)
            self.addMixinFuncs(visitor, script, basecls, cls)
    def addMixinFunc(self, visitor, script, f, owner, mixincls):
        # visitor.logger.debug('addMixinFunc', f.name, owner, f, mixincls)
        if not owner.hasSymbol(f.name):
            callinfo = ast.Call(ast.AttrRef(script.args[1].clone(), f.name), [ast.Identifier(param.name) for param in f.spec.params])
            # visitor.logger.debug('addMixinFunc callinfo', f.name, owner, f, mixincls, callinfo, callinfo.caller)
            newfunc = ast.FuncDef([], f.name, f.spec.clone(), ast.StatementBody([ast.Return(callinfo)]))
            owner.definitions.append(newfunc)
            newfunc.setOwner(owner)
            visitor.visitNewItem(newfunc)

class StaticMethodScript(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
    def resolveName(self, visitor, script):
        script.owner.spec.static = True

class InternalVarScript(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
    def resolveName(self, visitor, script):
        assert isinstance(script.owner, ast.SingleVarDef)
        script.owner.internal = True

class LoggerScript(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
    def processScript(self, visitor, script):
        pass
    def resolveName(self, visitor, script):
        visitor.logger.debug('LoggerScript.processScript', script, script.owner)
        cls = script.owner
        builtins.addLoggerVar(cls, visitor)

def loadAll(ns):
    ns['name'] = NameScript()
    ns['singleton'] = SingletonScript()
    ns['mixin'] = MixinScript()
    ns['logger'] = LoggerScript()
    ns['static_method'] = StaticMethodScript()
    # ns['internal'] = InternalVarScript()
