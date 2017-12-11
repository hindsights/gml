
import basetype
import ast


class LibFuncMatch(basetype.LibFunc):
    def __init__(self):
        basetype.LibFunc.__init__(self, None, 'match()')
        self.spec.static = True
    def evaluateCall(self, visitor, callinfo):
        # visitor.logger.debug('LibFuncMatch.evaluateCall start', callinfo.caller, callinfo.args)
        argcount = len(callinfo.args)
        assert argcount in [1, 2]
        caseblock = callinfo.args[-1]
        casevar = None
        if argcount == 1:
            casevar = visitor.getThis()
        else:
            casevar = callinfo.args[0].visit(visitor)
        assert casevar, (callinfo, callinfo.args, caseblock.entries)
        # visitor.logger.debug('LibFuncMatch.evaluateCall', casevar, casevar.cls, caseblock.entries)
        entry = visitor.matchClasses(casevar.cls, caseblock.entries, callinfo.getOwnerFunc().name, argcount)
        assert entry, (casevar, caseblock, callinfo)
        # visitor.logger.debug('LibFuncMatch found entry', entry, casevar, casevar.cls, caseblock, callinfo, callinfo.getOwnerFunc())
        return entry.visit(visitor)
    def resolveNameRef(self, visitor, callinfo):
        # visitor.logger.debug('LibFuncMatch.resolveNameRef', self, visitor, callinfo, callinfo.getOwnerFunc(), callinfo.caller, callinfo.args)
        # assert False
        callinfo.getOwnerFunc().info.dispatched = True
        argcount = len(callinfo.args)
        assert argcount in [1, 2]
        caseblock = callinfo.args[-1]
        assert isinstance(caseblock, ast.CaseBlock)
        if argcount == 2:
            caseblock.matchVar = callinfo.args[0]
            for entry in caseblock.entries:
                if entry.pattern:
                    assert hasattr(entry.pattern, 'name'), ('match resolve entry', callinfo.caller, caseblock.matchVar, entry.pattern, callinfo.getOwnerFunc())
                    assert hasattr(caseblock.matchVar, 'name'), ('match resolve matchVar', callinfo.caller, caseblock.matchVar, entry.pattern, callinfo.getOwnerFunc())
                    # casevar = ast.CaseVarSpec(ast.Param(caseblock.matchVar.name, ast.UserType([entry.pattern.name])))
                    entry.pattern = ast.VarTag(caseblock.matchVar.name, ast.UserType([entry.pattern.name]))
                    # visitor.logger.debug('match resolve entry', callinfo.caller, caseblock.matchVar, entry.pattern, callinfo.getOwnerFunc())
                    visitor.setupNewItem(entry.pattern, entry, False)

class LibFuncSwitch(basetype.LibFunc):
    def __init__(self):
        basetype.LibFunc.__init__(self, None, 'switch()')
        self.spec.static = True
    def evaluateCall(self, visitor, callinfo):
        # visitor.logger.debug('LibFuncMatch.evaluateCall start', callinfo.caller, callinfo.args)
        argcount = len(callinfo.args)
        assert argcount == 2, "evaluateCall"
        caseblock = callinfo.args[-1]
        casevar = None
        if argcount == 1:
            casevar = visitor.getThis()
        else:
            casevar = callinfo.args[0].visit(visitor)
        assert casevar, (callinfo, callinfo.args)
        # visitor.logger.debug('LibFuncMatch.evaluateCall', casevar, casevar.cls)
        entry = visitor.matchClasses(casevar.cls, caseblock.entries, callinfo.getOwnerFunc().name)
        assert entry, (casevar, caseblock, callinfo)
        # visitor.logger.debug('LibFuncMatch found entry', entry, casevar, casevar.cls, caseblock, callinfo, callinfo.getOwnerFunc())
        return entry.visit(visitor)
    def resolveNameRef(self, visitor, callinfo):
        # assert False
        # visitor.logger.debug('LibFuncMatch.resolveNameRef', self, visitor, callinfo)
        callinfo.getOwnerFunc().info.dispatched = True
        argcount = len(callinfo.args)
        assert argcount == 2
        caseblock = callinfo.args[-1]
        assert isinstance(caseblock, ast.CaseBlock)
        if argcount == 2:
            caseblock.matchVar = callinfo.args[0]
            for entry in caseblock.entries:
                # visitor.logger.debug('match resolve entry', callinfo.caller, caseblock.matchVar, entry.pattern, callinfo.getOwnerFunc())
                assert hasattr(entry.pattern, 'name'), ('match resolve entry', callinfo.caller, caseblock.matchVar, entry.pattern, callinfo.getOwnerFunc())
                assert hasattr(caseblock.matchVar, 'name'), ('match resolve matchVar', callinfo.caller, caseblock.matchVar, entry.pattern, callinfo.getOwnerFunc())
                casevar = ast.CaseVarSpec(ast.Param(caseblock.matchVar.name, ast.UserType([entry.pattern.name])))
                entry.addSymbol(casevar.variable)
                casevar.setOwner(entry)
                visitor.visitNewItem(casevar)

class LibFuncAssert(basetype.LibFunc):
    def __init__(self):
        basetype.LibFunc.__init__(self, None, 'assert()')
        self.spec.static = True
    def evaluateCall(self, visitor, callinfo):
        expr = callinfo.args[0].visit(visitor)
        # assert expr, (callinfo.getOwnerFunc(), callinfo.getOwnerClass())
        if len(callinfo.args) == 1:
            assert expr, (callinfo.args[1].visit(visitor), callinfo.getOwnerFunc(), callinfo.getOwnerClass())
        msgs = [arg.visit(visitor) for arg in callinfo.args[1:]]
        assert expr, tuple(msgs + ["==============", callinfo.getOwnerFunc(), callinfo.getOwnerClass()])

class LibFuncWith(basetype.LibFunc):
    def __init__(self):
        basetype.LibFunc.__init__(self, None, 'with()')
        self.spec.static = True
    def evaluateCall(self, visitor, callinfo):
        expr = callinfo.args[0].visit(visitor)
        assert len(callinfo.args) == 2, (self, callinfo)
        assert isinstance(callinfo.args[1], ast.Closure), (self, callinfo)
        assert expr, (callinfo.getOwnerFunc(), callinfo.getOwnerClass())
        assert False
        msgs = [arg.visit(visitor) for arg in callinfo.args[1:]]
        assert expr, tuple(msgs + [callinfo.getOwnerFunc(), callinfo.getOwnerClass()])

def loadAll():
    unit = ast.createLibUnit('sys.lang', [])
    print('sys.core.loadAll sys.lang', unit)
    unit.definitions.extend([LibFuncMatch(), LibFuncAssert(), LibFuncWith(), LibFuncSwitch()])
    return unit
