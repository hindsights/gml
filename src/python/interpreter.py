
import libs
import basetype
import operator
import ast
import xutils
import sys
import xutils
import parser

def calcClassMatchingDigree(sourceCls, targetCls):
    # print('calcClassMatchingDigree', sourceCls, targetCls)
    assert sourceCls is not None, (sourceCls, targetCls)
    if targetCls is None:
        # default case
        return sys.maxint
    if sourceCls is targetCls:
        # print('calcClassMatchingDigree exact match', sourceCls, targetCls)
        return 0
    minDegree = sys.maxint
    for base in sourceCls.bases:
        degree = calcClassMatchingDigree(base.getTarget(), targetCls)
        if degree == 0:
            minDegree = degree + 1
            # print('calcClassMatchingDigree exact match in base', sourceCls, base, targetCls)
            break
        elif degree < minDegree:
            minDegree = degree + 1
    # print('calcClassMatchingDigree result', sourceCls, targetCls, minDegree)
    return minDegree

def calcClassFuncMatchingDigree(sourceCls, funcname):
    # print('calcClassFuncMatchingDigree', sourceCls, funcname)
    if sourceCls.hasSymbol(funcname):
        func = sourceCls.findLocalSymbol(funcname)
        if func.info.dispatched is False:
            # print('calcClassFuncMatchingDigree hasSymbol', sourceCls, funcname, func)
            return 0, func
    minDegree = sys.maxint
    minSymbol = None
    for base in sourceCls.bases:
        degree, symbol = calcClassFuncMatchingDigree(base.getTarget(), funcname)
        if degree == 0:
            minDegree = degree + 1
            minSymbol = symbol
            # print('calcClassFuncMatchingDigree hasSymbol in direct base', sourceCls, base, minDegree, funcname)
            break
        if degree < minDegree:
            minDegree = degree + 1
            minSymbol = symbol
            # print('calcClassFuncMatchingDigree hasSymbol in more direct base', sourceCls, base, degree, minDegree, funcname)
    # print('calcClassFuncMatchingDigree return', sourceCls, minDegree, minSymbol, funcname)
    return minDegree, minSymbol

class GlobalScope(object):
    def __init__(self, unit):
        self.unit = unit
    # def has(self, name):
    #     return name in self.values
    def getVar(self, name):
        # print('GlobalScope.getVar', name, self.unit.name, self.unit.pkg.fullpath)
        assert False, (self, name)
        var = self.unit.findSymbol(name)
        if var.isVar() and var.owner.isUnit():
            # global var
            return var
        # assert False, (self, name, var)
        return None
    def setValue(self, name, val):
        assert name in self.values, (name, val, self.values)
        assert False
    def getValue(self, name):
        # print('GlobalScope.getValue', name, self.values)
        assert False
        pass

class EvaluatorScope(object):
    def __init__(self):
        self.vars = {}
    def __repr__(self):
        return 'EvaluatorScope(%s)' % self.vars
    # def has(self, name):
    #     return name in self.vars
    def addVar(self, name, var):
        # print('EvaluatorScope.addVar', name, var, self)
        assert name not in self.vars, (name, var, self.vars)
        self.vars[name] = var
    def getVar(self, name):
        # print('EvaluatorScope.getVar', name, self.vars)
        return self.vars.get(name)
    def setValue(self, name, val):
        assert name in self.vars, (name, val, self.vars)
        if name == 'text':
            assert isinstance(val, str), (name, val)
        # print('EvaluatorScope.setValue', name, val)
        self.vars[name].setValue(val)
    def getValue(self, name):
        # print('EvaluatorScope.getValue', name, self.vars)
        return self.vars.get(name).getValue()

class VarHolder(ast.AstNode):
    def __init__(self, var, value):
        assert var is not None and value is not None, ('VarHolder.init', var, value)
        self.var = var
        self.value = value
        # print('VarHolder.new', var.name, var, val, self)
        # assert var.getType() != ast.makePrimitiveType('int') or not isinstance(value, str)
    def setValue(self, val):
        assert val is not None, ('VarHolder.setValue', self.var, self.value, val)
        oldval = self.value
        self.value = val
        # print('VarHolder.setValue', self.var.name, self.var, self.value, val, self, oldval)
    def getValue(self):
        # print('VarHolder.getValue', self.var.name, self.var, self.value)
        return self.value
    def __repr__(self):
        return 'VarHolder:%s:%s:val=%s' % (self.var, ast.formatId(self), self.value)

FlowFlags = xutils.Enum('FlowFlags', 'NORMAL', 'RETURN', 'BREAK', 'CONTINUE')

class EvaluatorStack(object):
    def __init__(self, f, args, this, env, nilVal):
        assert this is None or isinstance(this, ClassDefEvaluator), this
        self.func = f
        self.args = args
        self.this = this
        self.unit = f.getOwnerUnit()
        # self.global_scope = GlobalScope(self.unit)# if env is None else None
        self.scopes = [this, self.unit.globalScope] if this else [self.unit.globalScope]
        self.flowFlag = FlowFlags.NORMAL
        self.returnValue = nilVal
        # env is the variable context for closure
        self.env = env
    def __repr__(self):
        return 'EvaluatorStack(%s)' % self.func.shortname()
    def addVar(self, name, val):
        # print('EvaluatorStack.addVar', name, val, self, self.this, self.scopes)
        return self.scopes[0].addVar(name, val)
    def getVar(self, name):
        # print('EvaluatorStack.getVar', name)
        for scope in self.scopes:
            # print('EvaluatorStack.getVar scope', name, scope, type(scope), self, self.scopes)
            var = scope.getVar(name)
            if var:
                # print('EvaluatorStack.getVar scope found', name, var, scope)
                return var
        if self.env:
            # print('EvaluatorStack.getVar search in env', name, self.env, self.env.scopes, self, self.scopes)
            return self.env.getVar(name)
        assert False, (name, self.scopes, self.env)
        return None
    def getValue(self, name):
        return self.getVar(name).getValue()
    def setValue(self, name, val):
        return self.getVar(name).setValue(val)

class ExprEvaluator(ast.AstVisitor):
    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.name = 'exprEvaluator'
        self.opname = 'evalExprEvaluation'
    def evalExprEvaluation_AstNode(self, node):
        node.visitChildren(self)
        return node
    def evalExprEvaluation_ExprEvaluation(self, expreval):
        # print('evalExprEvaluation_ExprEvaluation', expreval, expreval.expr, expreval.getOwnerFunc(), expreval.expr.getOwner())
        return expreval.expr
    def evalExprEvaluation_Param(self, param):
        param.type = param.type.visit(self)
        # print('evalExprEvaluation_Param type', param.type)
        return param
    def evalExprEvaluation_TupleType(self, tupletype):
        tupletype.elementTypes = [t.visit(self) for t in tupletype.elementTypes]
        return tupletype
    def evalExprEvaluation_FuncSpec(self, spec):
        for param in spec.params:
            param.visit(self)
        if spec.returnType is not None:
            spec.returnType = spec.returnType.visit(self)
            # print('evalExprEvaluation_FuncSpec returnType', spec.returnType)
        return spec

class NilValue(ast.SimpleNode):
    def __init__(self):
        ast.SimpleNode.__init__(self)
    def evaluateAttr(self, visitor, attr):
        assert False, ('NilValue.evaluateAttr', self, visitor, attr)

class Interpreter(ast.AstVisitor):
    def __init__(self):
        self.name = 'interpreter'
        self.opname = 'evaluate'
        self.stacks = []
        self.ops = {'==' : operator.eq, '>':operator.gt, '!=':operator.ne,
        '<':operator.lt, '>=':operator.ge, '<=':operator.le, 'not':operator.not_,
        'in':self.op_in,
        '+':operator.add,'-':operator.sub,'*':operator.mul,'/':operator.div,'%':operator.mod}
        self.assign_ops ={'+=':operator.iadd, '-=':operator.isub, '=':self.op_assign}
        self.implicit_args_stack = []
        self.nilValue = NilValue()
        self.logger = xutils.createLogger('Interpreter')
    def op_assign(self, var, val):
        return val
    def op_not_in(self, left, right):
        # self.logger.debug('op_not_in', left, right)
        return left not in right
    def op_in(self, left, right):
        # self.logger.debug('op_in', left, right)
        return left in right
    def getValue(self, name):
        # self.logger.debug('Interpreter.getValue', name)
        return self.getCurrentStack().getValue(name)
    def setValue(self, name, val):
        # self.logger.debug('Interpreter.setValue', name, val)
        return self.getCurrentStack().setValue(name, val)
    def addVar(self, name, val):
        # self.logger.debug('Interpreter.addVar', name, val)
        return self.getCurrentStack().addVar(name, val)
    def getVar(self, name):
        return self.getCurrentStack().getVar(name)
    def getCurrentStack(self):
        return self.stacks[0]
    def pushStack(self, f, args, this, env):
        # self.logger.debug('pushStack', f, args, this, len(self.stacks))
        stack = EvaluatorStack(f, args, this, env, self.nilValue)
        self.stacks.insert(0, stack)
        return stack
    def popStack(self):
        # self.logger.debug('popStack', len(self.stacks))
        del self.stacks[0]
    def popScope(self):
        del self.getCurrentStack().scopes[0]
    def pushScope(self):
        scope = EvaluatorScope()
        self.getCurrentStack().scopes.insert(0, scope)
        # self.logger.debug('pushScope', scope, self.getCurrentStack().scopes)
        return scope
    def printStack(self):
        self.logger.error('printStack', len(self.stacks))
        i = 0
        for stack in self.stacks[::-1]:
            funcname = stack.func.shortname()
            self.logger.error('stack', i, funcname, stack.args, stack.this, stack.unit)
            i += 1
        self.logger.error('printStack end.', i)
    def evaluateGlobalVar(self, units):
        # self.logger.debug('evaluateGlobalVar', units)
        for unit in units:
            # self.logger.debug('evaluateGlobalVar unit', unit, unit.ast)
            unit.ast.evaluateGlobalVar(self)
    def evaluateGlobalVar_SingleVarDef(self, var):
        if var.cls is None:
            # global var
            # self.logger.debug('evaluateGlobalVar_SingleVarDef global var', var)
            initialval = var.initial.visit(self) if var.initial else self.nilValue
            self.logger.error('evaluateGlobalVar_SingleVarDef var initial', var, initialval)
            v = VarHolder(var.name, initialval)
            unit = var.getOwnerUnit()
            unit.globalScope.addVar(var.name, v)
    def evaluateGlobalVar_MultipleVarDef(self, var):
        for v in var.vars:
            v.evaluateGlobalVar(self)
    def evaluateGlobalVar_FuncDef(self, func):
        pass
    def evaluateGlobalVar_TraitDef(self, cls):
        pass
    def evaluateGlobalVar_ClassDef(self, cls):
        pass
    def evaluateGlobalVar_EnumDef(self, enumdef):
        pass
    def evaluateGlobalVar_ExtensionDef(self, extdef):
        pass
    def evaluateGlobalVar_CodeUnit(self, unit):
        unit.globalScope = EvaluatorScope()
        for d in unit.definitions:
            d.evaluateGlobalVar(self)
    def execute(self, entryfunc, args):
        self.logger.error('execute', self, entryfunc)
        try:
            func = self.project.pkg.resolveSymbol(entryfunc)
            # self.logger.error('execute', self, entryfunc, func)
            return self.evalFunc(func, None, [args], {})
        except Exception as e:
            # etype, evalue, etb = sys.exc_info()
            # print('execute error:', e, etype, evalue, etb, dir(etb))
            self.logger.error('execute error:', e)
            xutils.printException(e, 50)
            self.printStack()
            return e
    def evaluate_AstNode(self, node):
        assert False, ('evaluate_AstNode', node, node.getOwnerFunc())
    def evaluate_ExprEvaluation(self, expreval):
        assert False, expreval
    def evaluate_EmbeddedCode(self, ec):
        text = ec.code.visit(self)
        expr = parser.exprParser.parse(text)
        # self.logger.debug('evaluate_EmbeddedCode', ec, text, expr)
        expr.setOwner(ec.getOwner())
        self.project.visitNewItem(expr)
        ret = expr.visit(self)
        # self.logger.debug('evaluate_EmbeddedCode ret', ec, text, expr, ret)
        return ret
    def evaluate_EmbeddedStatement(self, ebd):
        # self.logger.debug('evaluate_EmbeddedStatement', ebd, ebd.getOwnerFunc())
        astConstructor = libs.GmlAstConstructor(self, True)
        ret = astConstructor.visit(ebd.statement)
        # self.logger.debug('evaluate_EmbeddedStatement', ec, ret)
        return ret
    def evaluate_EmbeddedExpr(self, ebd):
        # self.logger.debug('evaluate_EmbeddedExpr', ebd, ebd.getOwnerFunc())
        astConstructor = libs.GmlAstConstructor(self, True)
        ret = astConstructor.visit(ebd.expr)
        # self.logger.debug('evaluate_EmbeddedExpr', ec, ret)
        return ret
    def evaluateNil_UserTypeClass(self, utc):
        return self.nilValue
    def callConstructor(self, cls, args, named_args, topclsvar):
        args = [arg.evaluateParam(self) for arg in args]
        named_args = dict([(arg.name, arg.value.evaluateParam(self)) for arg in named_args])
        return self.evalConstructor(cls, args, named_args, topclsvar)
    def evalConstructor(self, cls, args, named_args, topclsvar):
        # self.logger.debug('evalConstructor', cls.name, cls, args, cls.constructors, self.getThis())
        clsvar = ClassDefEvaluator(cls, self)
        clsvar.evalConstructor(self, args, named_args, topclsvar)
        for name, arg in named_args.iteritems():
            # self.logger.debug('evalConstructor arg', name, arg, clsvar, cls)
            if name == 'text':
                assert isinstance(arg, str), (clsvar, name, arg)
            clsvar.setValue(name, arg)
        return clsvar
    def evaluate_FuncDef(self, f):
        # self.logger.debug('evaluate_FuncDef', f, f.getOwnerClass(), f.cls, self.getThis(), f.body)
        if f.cls and f.cls.singleton and f.name == 'instance':
            assert len(f.body.statements) == 0
            if not hasattr(f.cls, 'singleton_instance') or f.cls.singleton_instance is None:
                f.cls.singleton_instance = self.evalConstructor(f.cls, [], {}, None)
            return f.cls.singleton_instance
        # assert len(f.spec.params) == 1
        assert self.getCurrentStack().flowFlag == FlowFlags.NORMAL
        f.body.visit(self)
        return self.getCurrentStack().returnValue
    def createVar(self, var):
        # self.logger.debug('createVar', var, var.initial, self.getThis(), var.getOwnerFunc(), var.getOwnerClass())
        val = self.nilValue
        if var.initial and var.cls is None:
            val = var.initial.visit(self)
            # self.logger.debug('createVar initial', var, val, var.getOwnerFunc())
            assert val is not None, ('createVar initial', var, var.initial, self.getThis(), var.getOwnerFunc(), var.getOwnerClass(), val)
        else:
            val = var.getType().getTypeClass().evaluateNil(self)
            assert val is not None, ('createVar', var, var.initial, self.getThis(), var.getOwnerFunc(), var.getOwnerClass(), val)
            # self.logger.debug('createVar initial none', var, val, var.getOwnerFunc())
        # self.logger.debug('createVar initial ok', var, val)
        if var.name == 'text':
            assert isinstance(val, str), (var, val, var.getOwnerFunc(), var.getOwnerClass())
        varholder = VarHolder(var, val)
        # self.logger.debug('createVar ret', var, val, varholder)
        return varholder
    def createTupleVar(self, var):
        # self.logger.debug('createTupleVar', var, var.initial, self.getThis(), var.getOwnerFunc(), var.getOwnerClass())
        vals = self.nilValue
        if var.initial and var.cls is None:
            vals = var.initial.visit(self)
            # self.logger.debug('createVar initial', var, val, var.getOwnerFunc())
        else:
            vals = var.getType().getTypeClass().evaluateNil(self)
        assert len(vals) == len(var.vars)
        holders = []
        for i in range(len(vals)):
            holders.append(VarHolder(var.vars[i], vals[i]))
        return holders
    def constructVar(self, var):
        # self.logger.debug('constructVar', var, var.initial, self.getThis())
        val = self.nilValue
        if var.initial:
            val = var.initial.visit(self)
            # self.logger.debug('constructVar setValue', var.name, var, val)
            self.setValue(var.name, val)
        # return val
    def evaluate_SingleVarDef(self, var):
        # self.logger.debug('evaluate_SingleVarDef', var)
        val = self.createVar(var)
        self.addVar(var.name, val)
        # self.logger.debug('evaluate_SingleVarDef', var, val)
        return val
    def evaluate_TupleVarDef(self, var):
        # self.logger.debug('evaluate_SingleVarDef', var)
        vals = self.createTupleVar(var)
        for val in vals:
            self.addVar(val.var.name, val)
        # self.logger.debug('evaluate_SingleVarDef', var, val)
        return vals
    def evalStatementBlock(self, stmtblock):
        assert not self.is_func_finished()
        # self.logger.debug('evaluate_StatementBlock', stmtblock)
        ret = stmtblock.body.visit(self)
        return ret
    def evaluate_Break(self, stmt):
        # assert False, (stmt, stmt.owner, stmt.getOwnerFunc(), stmt.getOwnerClass())
        self.set_loop_break()
    def evaluate_Continue(self, stmt):
        # assert False, (stmt, stmt.getOwnerFunc(), stmt.getOwnerClass())
        self.set_loop_continue()
    def checkFlowAbort(self):
        flowFlag = self.getFlowFlag()
        if flowFlag == FlowFlags.RETURN:
            return True
        if flowFlag == FlowFlags.BREAK:
            self.getCurrentStack().flowFlag = FlowFlags.NORMAL
            return True
        if flowFlag == FlowFlags.CONTINUE:
            self.getCurrentStack().flowFlag = FlowFlags.NORMAL
        return False
    def evaluate_ForStatement(self, stmt):
        # self.logger.debug('evaluate_ForStatement', stmt, len(stmt.stmtblock.statements), stmt.inits)
        scope = self.pushScope()
        if stmt.init:
            stmt.init.visit(self)
        while stmt.condition is None or stmt.condition.visit(self):
            self.pushScope()
            stmt.body.visit(self)
            needAbort = self.checkFlowAbort()
            if needAbort:
                self.popScope()
                break
            if stmt.step:
                stmt.step.visit(self)
            self.popScope()
        # assert False, (self, stmt)
        self.popScope()
    def evaluate_ForEachStatement(self, stmt):
        # self.logger.debug('evaluate_ForEachStatement', stmt, stmt.collection, len(stmt.body.statements))
        scope = self.pushScope()
        stmt.item.visit(self)
        coll = stmt.collection.visit(self)
        # self.logger.debug('evaluate_ForEachStatement coll', coll, stmt.item)
        for item in coll:
            self.pushScope()
            scope.setValue(stmt.item.name, item)
            # self.logger.debug('evaluate_ForEachStatement item', item, stmt.item.name)
            stmt.body.visit(self)
            self.popScope()
        self.popScope()
    def evaluate_ForEachDictStatement(self, stmt):
        # self.logger.debug('evaluate_ForEachDictStatement', stmt, stmt.collection, len(stmt.body.statements))
        scope = self.pushScope()
        stmt.key.visit(self)
        stmt.value.visit(self)
        coll = stmt.collection.visit(self)
        for key, val in coll.iteritems():
            scope.setValue(stmt.key.name, key)
            scope.setValue(stmt.value.name, val)
            # self.logger.debug('evaluate_ForEachDictStatement item', key, val, stmt.key.name, stmt.value.name)
            stmt.body.visit(self)
        self.popScope()
    def evaluateCall(self, callinfo):
        assert False
        return
    def evaluate_CallStatement(self, callstmt):
        callstmt.call.visit(self)
    def evaluate_ArgumentPlaceholder(self, param):
        # self.logger.debug('evaluate_ArgumentPlaceholder', self, param, param.sequence, self.implicit_args_stack[0])
        return self.implicit_args_stack[0][param.sequence]
    def evaluateVar_Identifier(self, identifier):
        # self.logger.debug('evaluateVar_Identifier', identifier, self)
        return self.getVar(identifier.name)
    def evaluateVar_AttrRef(self, attr):
        # self.logger.debug('evaluateVar_AttrRef', attr, self)
        obj = attr.object.visit(self)
        # self.logger.debug('evaluateVar_AttrRef obj', attr, self, obj)
        return obj.evaluateAttrVar(self, attr)
    def evaluateVar_Subscript(self, subscript):
        coll = subscript.collection.visit(self)
        # self.logger.debug('evaluateVar_Subscript', subscript, self, coll)
        assert False
        return self.getVar(identifier.name)
    def evalAssignment(self, op, var, val):
        # self.logger.debug('evalAssignment', op, var, val)
        varholder = var.evaluateVar(self)
        oldval = var.visit(self)
        newval = op(oldval, val)
        # self.logger.debug('evalAssignment op', op, var, oldval, val, newval)
        varholder.setValue(newval)
    def evaluate_AssertStatement(self, stmt):
        # self.logger.debug('evaluate_AssertStatement', stmt.expr, stmt.msg, stmt.getOwnerFunc())
        expr = stmt.expr.visit(self)
        if stmt.msg:
            assert expr, (stmt.msg.visit(self), stmt.getOwnerFunc(), stmt.getOwnerClass())
        else:
            assert expr, (stmt.getOwnerFunc(), stmt.getOwnerClass())
    def evaluate_Assignment(self, assign):
        # self.logger.debug('evaluate_Assignment', assign, assign.getOwnerFunc())
        values = [val.visit(self) for val in assign.values]
        for i in range(len(assign.targets)):
            target = assign.targets[i]
            # self.logger.debug('evaluate_Assignment target', i, target, assign.values[i], assign.op)
            if isinstance(target, ast.Subscript):
                if assign.op == '=':
                    val = assign.values[i]
                    coll = target.collection.visit(self)
                    # self.logger.debug('evaluate_Assignment subscript key', coll, target.key, val)
                    key = target.key.visit(self)
                    # self.logger.debug('evaluate_Assignment val', coll, key, target.key, val)
                    newval = values[i]
                    # self.logger.debug('evaluate_Assignment set', coll, key, val, newval)
                    # assert False, (assign, assign.variable.collection.getTypeClass().eval_set)
                    target.collection.getTypeClass().eval_set(coll, key, newval)
                    continue
            op = self.assign_ops[assign.op]
            # self.logger.debug('evaluate_Assignment normal', op, val, target, values[i])
            self.evalAssignment(op, target, values[i])
    def evaluate_Subscript(self, subscript):
        # self.logger.debug('evaluate_Subscript', subscript, subscript.collection, subscript.collection.getTarget(), subscript.key)
        coll = subscript.collection.visit(self)
        key = subscript.key.visit(self)
        # self.logger.debug('evaluate_Subscript coll', subscript, coll, key, coll[key])
        if isinstance(coll, list):
            assert isinstance(key, int) and key < len(coll), ('evaluate_Subscript invalid list coll', subscript, subscript.collection, coll, key, len(coll), subscript.getOwnerFunc())
        elif isinstance(coll, dict):
            assert key in coll, ('evaluate_Subscript invalid dict coll', subscript, subscript.collection, coll, key, subscript.getOwnerFunc())
        elif isinstance(coll, str):
            assert isinstance(key, int) and key < len(coll), ('evaluate_Subscript invalid str coll', subscript, subscript.collection, coll, key, subscript.getOwnerFunc())
        else:
            assert False, ('evaluate_Subscript invalid coll', subscript, subscript.collection, coll, key, subscript.getOwnerFunc())
        return coll[key]
    def evaluate_Slicing(self, slicing):
        # self.logger.debug('evaluate_Slicing', slicing)
        seq = slicing.collection.visit(self)
        start = slicing.start.visit(self) if slicing.start and slicing.start != self.nilValue else None
        stop = slicing.stop.visit(self) if slicing.stop and slicing.stop != self.nilValue else None
        # self.logger.debug('evaluate_Subscript coll', seq, start, stop)
        return seq[start:stop]
    def evaluate_AttrRef(self, attr):
        # self.logger.debug('evaluate_AttrRef', attr, attr.object, attr.ref, attr.getOwnerFunc())
        obj = attr.object.visit(self)
        # # self.logger.debug('evaluate_AttrRef obj', attr, attr.object, obj, attr.getOwnerFunc())
        return obj.evaluateAttr(self, attr)
    def evaluate_TypeCast(self, typecast):
        src = typecast.source.visit(self)
        if src is None or src == self.nilValue:
            return self.nilValue
        srctype = src.cls
        dsttype = typecast.type.getTarget()
        # self.logger.debug('evaluate_TypeCast', typecast, typecast.source, typecast.type, srctype, dsttype, src)
        if ast.isSubClass(srctype, dsttype):
            return src
        return self.nilValue
    def evaluateAttr_UserTypeClass(self, utc, attr):
        assert False
        if attr.ref in utc.cls.classes:
            assert False
            return utc.cls.classes[attr.ref]
        if attr.ref in utc.cls.functions:
            assert False, (self, attr.ref, utc.cls.name)
            return utc.cls.functions[attr.ref]
        assert False, (self, utc, attr)
    def evaluateAttr1_AstNode(self, node, attr):
        # self.logger.debug('evaluateAttr_SingleVarDef', var, attr)
        return node.getTypeClass().evaluateAttr(self, attr)
    def evaluateAttr1_SingleVarDef(self, var, attr):
        # self.logger.debug('evaluateAttr_SingleVarDef', var, attr)
        return var.getTypeClass().evaluateAttr(self, attr)
    def evaluateAttr1_Param(self, param, attr):
        # self.logger.debug('evaluateAttr_Param', param)
        return param.getTypeClass().evaluateAttr(self, attr)
    def evaluateAttr1_Identifier(self, identifier, attr):
        # self.logger.debug('evaluateAttr_Identifier', identifier, attr, attr.getTarget())
        target = identifier.getTarget()
        return target.evaluateIdentifierAttr(self, attr)
        if isinstance(target, (ast.ClassDef, ast.EnumDef, basetype.LibClass)):
            # self.logger.debug('evaluateAttr_Identifier target', attr, target, attr.target)
            # assert not isinstance(attr.target, ast.FuncDef), (identifier, target, attr, attr.target)
            if isinstance(attr.target, ast.FuncDef):
                return attr.target
            return attr.target.visit(self)
        obj = identifier.visit(self)
        # self.logger.debug('evaluateAttr_Identifier normal', attr, target, obj)
        assert obj and isinstance(obj, ast.AstNode), ('evaluateAttr_Identifier obj is nil', identifier, obj, attr, attr.getOwnerFunc(), target)
        return obj.evaluateAttr(self, attr)
    def evaluateIdentifierAttr_AstNode(self, node, attr):
        identifier = attr.object
        obj = identifier.visit(self)
        # self.logger.debug('evaluateAttr_Identifier normal', attr, target, obj)
        assert obj and isinstance(obj, ast.AstNode), ('evaluateAttr_Identifier obj is nil', identifier, obj, attr, attr.getOwnerFunc(), target)
        return obj.evaluateAttr(self, attr)
    def evaluateIdentifierAttr_EnumDef(self, enumdef, attr):
        return attr.target.visit(self)
    def evaluateAttr_LibClass(self, cls, attr):
        return attr.target# if isinstance(attr.target, ast.LibFuncBase) else attr.target.visit(self)
    def evaluateAttr_ClassDef(self, cls, attr):
        return attr.target# if isinstance(attr.target, (ast.FuncDef, ast.FuncProto)) else attr.target.visit(self)
    def evaluateAttr_ScriptClass(self, cls, attr):
        return attr.target# if isinstance(attr.target, (ast.FuncDef, ast.FuncProto)) else attr.target.visit(self)
    def evaluateAttr_ClassDef(self, cls, attr):
        # self.logger.debug('evaluateAttr_ClassDef', attr)
        assert False, (cls, attr, attr.getOwnerFunc())
        ret = cls.findLocalSymbol(attr.ref)
        assert ret, (cls, attr)
        return ret
    def evaluate_NamedExpressionItem(self, item):
        # self.logger.debug('evaluate_NamedExpressionItem', item.value)
        # return item.value.value if isinstance(item.value, xutils.EnumItem) else item.value
        return item.value.visit(self)
    def evaluateAttr_EnumDef(self, enumdef, attr):
        # self.logger.debug('evaluateAttr_EnumDef', attr, enumdef.symbols.get(attr.ref).value, enumdef.symbols)
        return enumdef.symbols.get(attr.ref).visit(self)
    def evaluate_Closure(self, c):
        # self.logger.debug('evaluate_Closure', c)
        # assert False, (c, c.owner, c.getOwnerFunc())
        assert c.stack, ('evaluate_Closure nil stack', c, c.owner, c.getOwnerFunc())
        ret = c.body.visit(self)
        return self.getCurrentStack().returnValue
    def evaluate_Call(self, callinfo):
        # self.logger.debug('evaluate_Call', callinfo, callinfo.owner, callinfo.getOwnerFunc(), callinfo.getOwnerClass())
        ret = callinfo.caller.evaluateCall(self, callinfo)
        # self.logger.debug('evaluate_Call ret', callinfo, callinfo.caller, ret)
        return ret
    def evaluateCall_GenericExpr(self, expr, callinfo):
        ret = expr.getTarget().evaluateCall(self, callinfo)
        # self.logger.debug('evaluateCall_GenericExpr ret', expr, callinfo, expr.getTarget(), ret)
        return ret
    def evaluateCall_Closure(self, closure, callinfo):
        # self.logger.debug('evaluateCall_Closure', closure, callinfo)
        args = [arg.visit(self) for arg in callinfo.args]
        stack = self.pushStack(closure, args, None, closure.stack)
        scope = self.pushScope()
        self.implicit_args_stack.insert(0, args)
        ret = closure.visit(self)
        del self.implicit_args_stack[0]
        self.popScope()
        self.popStack()
        return ret
    def evaluateCall_AttrRef(self, attr, callinfo):
        # self.logger.debug('evaluateCall_AttrRef', attr, callinfo, attr.getTarget(), attr.getOwnerFunc())
        target = attr.getTarget()
        if isinstance(target, (ast.FuncDef, ast.FuncProto)):
            if (not target.spec.static) or target.injection_cls:
                # self.logger.debug('evaluateCall_AttrRef func start', attr, callinfo, attr.getTarget(), target.injection_cls, target.spec.static)
                caller = callinfo.caller.visit(self)
                # self.logger.debug('evaluateCall_AttrRef func', attr, callinfo, attr.getTarget(), caller, target.injection_cls)
                return caller.evaluateCall(self, callinfo)
        if isinstance(target, libs.ScriptFunc) and (not target.spec.static):
            # self.logger.debug('evaluateCall_AttrRef script func start', attr, callinfo, attr.getTarget())
            obj = callinfo.caller.object.visit(self)
            callerfunc = getattr(obj, 'ScriptMethod_' + callinfo.caller.ref)
            assert callerfunc, (callinfo, callinfo.caller.object, obj, callerfunc)
            # self.logger.debug('evaluateCall_AttrRef script func', attr, callinfo, attr.getTarget(), callerfunc)
            args = [arg.evaluateParam(self) for arg in callinfo.args]
            named_args = dict([(arg.name, arg.value.visit(self)) for arg in callinfo.namedArgs])
            return callerfunc(*args, **named_args)
        # self.logger.debug('evaluateCall_AttrRef attr target', attr, callinfo, target)
        ret = target.evaluateCall(self, callinfo)
        # self.logger.debug('evaluateCall_AttrRef ret', attr, callinfo, attr.getTarget(), ret)
        return ret
    def evaluateCall_ClassDef(self, cls, callinfo):
        # self.logger.debug('evaluateCall_ClassDef', cls.name, callinfo.args, callinfo.getOwnerFunc(), self.getThis())
        return self.callConstructor(cls, callinfo.args, callinfo.namedArgs, None)
    def callFunc(self, func, this, args, named_args):
        # self.logger.debug('callFunc', func, this, args, named_args, self.getThis())
        if func.injection_cls:
            assert this, (func, this, args)
            args.insert(0, this)
        # self.logger.debug('callFunc evaluateParam', func, this, args, named_args)
        args = [arg.evaluateParam(self) for arg in args]
        named_args = dict([(arg.name, arg.value.evaluateParam(self)) for arg in named_args])
        ret = self.evalFunc(func, this, args, named_args)
        # self.logger.debug('callFunc end', func, this, args, named_args, ret)
        return ret
    def evalFunc(self, func, this, args, named_args):
        # self.logger.debug('evalFunc', func, this, args, named_args, self.getThis(), func.getOwnerClass(), func.getOwnerUnit())
        assert len(args) == len(func.spec.params), (args, func.name, func.spec, this, func.spec.static, func, func.getOwnerClass(), func.getOwnerUnit())
        # assert func.name != 'cacheName', (func, this, args, func.injection_cls)
        self.prepareEvalFunc(func, args, this)
        if func.info.type == ast.FuncType.constructor:
            for var in func.cls.vars:
                self.constructVar(var)
        ret = func.visit(self)
        self.popStack()
        # self.logger.debug('evalFunc end', func, this, args, named_args, ret)
        return ret
    def prepareEvalFunc(self, f, args, this):
        stack = self.pushStack(f, args, this, None)
        scope = self.pushScope()
        assert scope
        # self.logger.debug('prepareEvalFunc', f, this, stack, scope, len(args), len(f.spec.params), len(self.stacks), args)
        if len(args) == len(f.spec.params):
            for i in range(len(args)):
                # self.logger.debug('prepareEvalFunc arg', i, f, args[i], f.spec.params[i])
                # assert not isinstance(args[i], ast.AstNode) or isinstance(args[i], ClassDefEvaluator), (f, args[i], f.spec.params[i])
                scope.addVar(f.spec.params[i].name, VarHolder(f.spec.params[i], args[i]))
        else:
            assert False
    def evaluateCall_FuncDef(self, f, callinfo):
        # self.logger.debug('evaluateCall_FuncDef', f, callinfo.caller, callinfo.args, f.injection_cls)
        this = None
        args = callinfo.args
        if (not f.spec.static) or f.injection_cls:
            if isinstance(callinfo.caller, ast.AttrRef):
                this = callinfo.caller.object.visit(self)
                # self.logger.debug('evaluateCall_FuncDef new this', f, this, callinfo.caller.object)
            else:
                this = self.getCurrentStack().this
                # self.logger.debug('evaluateCall_FuncDef old this', f, this, callinfo.caller)
        return self.callFunc(f, this, args, callinfo.namedArgs)
    def evaluateCall_AstNode(self, node, callinfo):
        assert False, (node, callinfo, callinfo.caller, callinfo.getOwnerFunc())
    def evaluateCall_Identifier(self, identifier, callinfo):
        # self.logger.debug('evaluateCall_Identifier', identifier, identifier.getTarget(), callinfo, self.getThis(), callinfo.getOwnerFunc())
        target = identifier.getTarget()
        if isinstance(target, ast.ClassDef) or isinstance(target, basetype.LibClass):
            return target.evaluateCall(self, callinfo)
        if isinstance(target, ast.UserType):
            assert target.getTarget() and not isinstance(target.getTarget(), ast.UserType)
            return target.getTarget().evaluateCall(self, callinfo)
        if isinstance(target, ast.FuncDef) or isinstance(target, ast.FuncProto) or isinstance(target, basetype.LibFunc):
            if target.spec.static or target.cls is None:
                # self.logger.debug('evaluateCall_Identifier static func', identifier, target, callinfo)
                return target.evaluateCall(self, callinfo)
            this = self.getThis()
            if this is None:
                return target.evaluateCall(self, callinfo)
            func = this.getVar(identifier.name)
            assert func, ('evaluateCall_Identifier FuncDef or FuncProto or LibFunc', identifier, identifier.getTarget(), callinfo, self.getThis(), callinfo.getOwnerFunc())
            return func.evaluateCall(self, callinfo)
        # self.logger.debug('evaluateCall_Identifier var func', identifier, target, callinfo, self.getValue(identifier.name))
        return self.getValue(identifier.name).evaluateCall(self, callinfo)
    def evaluateListComprehension(self, listcomp, i):
        # self.logger.debug('evaluateListComprehension', listcomp.expr, listcomp.fors[0].source, i)
        if i >= len(listcomp.fors):
            return [listcomp.expr.visit(self)]
        listfor = listcomp.fors[i]
        coll = listfor.source.visit(self)
        ret = []
        # self.logger.debug('evaluateListComprehension coll', coll, i, len(listcomp.fors))
        for item in coll:
            scope = self.pushScope()
            # self.logger.debug('evaluateListComprehension item', coll, i, item, scope, listfor.name)
            self.addVar(listfor.variable.name, VarHolder(listfor.variable, item))
            cond = listfor.condition.visit(self) if listfor.condition else True
            if cond:
                ret.extend(self.evaluateListComprehension(listcomp, i + 1))
            self.popScope()
        return ret
    def evaluate_ListComprehension(self, listcomp):
        # self.logger.debug('evaluate_ListComprehension', listcomp, listcomp.expr)
        ret = self.evaluateListComprehension(listcomp, 0)
        # self.logger.debug('evaluate_ListComprehension ret', listcomp, listcomp.expr, ret)
        return ret
    def evaluate_StringEvaluation(self, se):
        # self.logger.debug('evaluate_StringEvaluation', se, se.evaluation, se.getOwnerFunc())
        return se.literal.visit(self) if se.evaluation is None else se.evaluation.visit(self)
    def evaluate_PrimitiveLiteral(self, literal):
        # self.logger.debug('evaluate_PrimitiveLiteral', literal, literal.value, literal.text)
        return literal.value
    def evaluate_TupleLiteral(self, literal):
        # non-layzy evaluation
        # self.logger.debug('evaluate_TupleLiteral', literal.values)
        return tuple([val.visit(self) for val in literal.values])
    def evaluate_ListLiteral(self, literal):
        # non-layzy evaluation
        # self.logger.debug('evaluate_ListLiteral', literal.values)
        return [val.visit(self) for val in literal.values]
        # return literal.values
    def evaluate_DictLiteral(self, literal):
        # non-layzy evaluation
        # self.logger.debug('evaluate_ListLiteral', literal.values)
        return dict([(item.key.visit(self), item.value.visit(self)) for item in literal.values])
        # return literal.values
    def getThis(self):
        # self.logger.debug('getThis', self, self.getCurrentStack(), self.stacks)
        return self.getCurrentStack().this if len(self.stacks) > 0 else None
    def evaluate_CaseBlock(self, caseblock):
        assert False, caseblock
    def evaluate_CaseEntryExpr(self, caseexpr):
        return caseexpr.expr.visit(self)
    def evaluate_CaseEntryStmt(self, casestmt):
        return casestmt.body.visit(self)
    def evaluate_Identifier(self, identifier):
        # self.logger.debug('evaluate_Identifier', identifier, identifier.getTarget(), identifier.getOwner(), identifier.getOwnerFunc(), self.getThis())
        target = identifier.getTarget()
        if isinstance(target, (ast.ClassDef, ast.LibClassBase, ast.EnumDef)):
            return target
        if isinstance(target, basetype.LibLiteral):
            return target.value
        if isinstance(target, ast.FuncDef) or isinstance(target, ast.FuncProto) or isinstance(target, basetype.LibFunc):
            if target.spec.static:
                return target
            assert self.getThis()
            return self.getThis().getValue(target.name)
        ret =  self.getValue(identifier.name)
        # self.logger.debug('evaluate_Identifier ret', ret, identifier, identifier.getTarget(), identifier.getOwner(), identifier.getOwnerFunc(), identifier.getOwner().getOwner(), identifier.getOwner().getOwner().getOwner(), identifier.getOwner().getOwner().getOwner().getOwner())
        return ret
    def evaluate_Nil(self, nil):
        return self.nilValue
    def evaluate_This(self, this):
        # self.logger.debug('evaluate_This', this.owner, self.getThis())
        # assert not this.owner.getOwnerFunc().spec.static, (this, this.getOwnerFunc())
        assert self.getThis(), (this, this.getOwnerFunc(), this.getOwnerClass())
        return self.getThis()
    def evaluate_IfElseExpr(self, expr):
        cond = expr.condition.visit(self)
        # self.logger.debug('evaluate_IfElseExpr', expr, expr.condition, expr.truePart, expr.falsePart, cond)
        assert cond is not None, ('evaluate_IfElseExpr', expr, expr.condition, cond)
        if cond and cond != self.nilValue:
            return expr.truePart.visit(self)
        return expr.falsePart.visit(self)
    def evaluate_ExprList(self, exprlist):
        exprs = [expr.visit(self) for expr in exprlist.exprs]
        # self.logger.debug('evaluate_ExprList', exprs, exprlist)
        return exprs
    def evaluate_UnaryOp(self, expr):
        # self.logger.debug('evaluate_UnaryOp', expr)
        operand = expr.operand.visit(self)
        return expr.operand.getTypeClass().evaluateUnaryOp(self, expr.op, operand)
    def evaluate_BinaryOp(self, expr):
        # self.logger.debug('evaluate_BinaryOp', expr, expr.getOwnerFunc(), expr.left, expr.left.getTypeClass(), expr.right, expr.right.getTypeClass())
        if expr.op == 'not-in':
            left = expr.left.visit(self)
            right = expr.right.visit(self)
            return expr.right.getTypeClass().eval_not_contains(right, left)
        if expr.op == 'in':
            left = expr.left.visit(self)
            right = expr.right.visit(self)
            return expr.right.getTypeClass().eval_contains(right, left)
        assert expr.left.getTypeClass(), ('evaluate_BinaryOp invalid left', expr.left, expr.right, expr.op, 'types', expr.left.getType(), expr.right.getType())
        # self.logger.debug('evaluate_BinaryOp normal', expr, expr.getOwnerFunc(), expr.left, expr.left.getTypeClass(), expr.right, expr.right.getTypeClass())
        return expr.left.getTypeClass().evaluateBinaryOp(self, expr.op, expr.left, expr.right)
    def evaluate_Return(self, stmt):
        # self.logger.debug('evaluate_Return', stmt, stmt.values[0] if len(stmt.values) > 0 else None)
        ret = stmt.value.visit(self) if stmt.value is not None else self.nilValue
        # assert ret is not None, ('evaluate_Return', stmt, stmt.value, ret)
        if ret is None:
            ret = self.nilValue
        # self.logger.debug('evaluate_Return ret', stmt, ret)
        self.set_func_finished(ret)
    def resetFlowFlag(self):
        self.getCurrentStack().flowFlag = FlowFlags.NORMAL
    def getFlowFlag(self):
        return self.getCurrentStack().flowFlag
    def is_func_finished(self):
        return self.getCurrentStack().flowFlag == FlowFlags.RETURN
    def set_func_finished(self, ret):
        # self.logger.debug('set_func_finished', self, ret)
        self.getCurrentStack().flowFlag = FlowFlags.RETURN
        self.getCurrentStack().returnValue = ret
    def set_loop_break(self):
        # self.logger.debug('set_loop_break', self)
        self.getCurrentStack().flowFlag = FlowFlags.BREAK
    def set_loop_continue(self):
        # self.logger.debug('set_loop_continue', self)
        self.getCurrentStack().flowFlag = FlowFlags.CONTINUE
    def matchClasses(self, cls, entries, funcname, argcount):
        # self.logger.debug('matchClasses start', cls, funcname)
        matchingDegree, matchingEntry = calcClassFuncMatchingDigree(cls, funcname) if 1 == argcount else (None, None)
        if matchingDegree == 0:
            # self.logger.debug('matchClasses exact entry', cls, funcname, matchingEntry, entry)
            return matchingEntry
        for entry in entries:
            targetcls = None
            if entry and entry.pattern:
                targetcls = entry.pattern.getTarget() if isinstance(entry.pattern, ast.Identifier) else entry.pattern.getType().getTypeClass()
            degree = self.calcClassMatchingDigree(cls, targetcls)
            if matchingDegree is None or matchingDegree > degree:
                # self.logger.debug('matchClasses check entry', cls, funcname, matchingDegree, degree, matchingEntry, entry, matchingEntry.pattern if matchingEntry else None, entry.pattern)
                matchingDegree = degree
                matchingEntry = entry
        if matchingEntry:
            # self.logger.debug('matchClasses found entry', cls, funcname, matchingDegree, matchingEntry)
            return matchingEntry
        return None
    def calcClassMatchingDigree(self, cls, targetcls):
        return calcClassMatchingDigree(cls, targetcls)
    def evaluate_SwitchCaseExpr(self, expr):
        # self.logger.debug('evaluate_SwitchCaseExpr', expr)
        if isinstance(expr.entries[0], ast.CaseEntryExpr):
            matchexpr = expr.expr.visit(self)
            # self.logger.debug('evaluate_SwitchCaseExpr CaseEntryExpr', expr.getOwnerFunc(), expr.entries[0], expr.entries[0].pattern, expr.expr, matchexpr)
            matchingDegree = sys.maxint
            matchingEntry = None
            for entry in expr.entries:
                targetcls = entry.pattern.variable.getType().getTarget()
                degree = calcClassMatchingDigree(matchexpr.cls, targetcls)
                if degree < matchingDegree:
                    # self.logger.debug('evaluate_SwitchCaseExpr try match entry', matchingDegree, degree, matchexpr.cls, targetcls, expr.expr)
                    matchingDegree = degree
                    matchingEntry = entry
            # self.logger.debug('evaluate_SwitchCaseExpr final match', matchingDegree, degree, matchexpr.cls, targetcls, expr.expr, matchingEntry.pattern.variable if matchingEntry else None)
            assert matchingEntry, (matchingDegree, degree, matchexpr.cls, targetcls, expr.expr, matchingEntry)
            var = self.getVar(expr.expr.name)
            self.addVar(matchingEntry.pattern.variable.name, var) 
            return matchingEntry.expr.visit(self)
        else:
            assert False, (stmt, stmt.entries[0])
    def evaluate_UsingStatement(self, stmt):
        scope = self.pushScope()
        stmt.variable.visit(self)
        stmt.body.visit(self)
        self.popScope()
    def evaluate_SwitchCaseStatement(self, stmt):
        # self.logger.debug('evaluate_SwitchCaseStatement', stmt, stmt.getOwnerFunc(), stmt.getOwnerClass())
        if isinstance(stmt.entries[0], ast.CaseEntryStmt):
            matchexpr = stmt.expr.visit(self)
            # self.logger.debug('evaluate_SwitchCaseStatement CaseEntryStmt', stmt, stmt.entries[0], stmt.entries[0].pattern, stmt.expr, matchexpr)
            matchingDegree = sys.maxint
            matchingEntry = None
            for entry in stmt.entries:
                targetcls = entry.pattern.variable.getType().getTarget()
                degree = calcClassMatchingDigree(matchexpr.cls, targetcls)
                if degree < matchingDegree:
                    # self.logger.debug('evaluate_SwitchCaseStatement try match entry', matchingDegree, degree, matchexpr.cls, targetcls, stmt.expr)
                    matchingDegree = degree
                    matchingEntry = entry
            # self.logger.debug('evaluate_SwitchCaseStatement final match', matchingDegree, degree, matchexpr.cls, targetcls, stmt.expr)
            assert matchingEntry, (matchingDegree, degree, matchexpr.cls, targetcls, stmt.expr, matchingEntry, stmt.getOwnerFunc(), stmt.getOwnerClass())
            var = self.getVar(stmt.expr.name)
            self.addVar(matchingEntry.pattern.variable.name, var) 
            matchingEntry.body.visit(self)
        else:
            assert False, (stmt, stmt.entries[0])
    def evaluate_StatementBlock(self, stmtblock):
        scope = self.pushScope()
        stmtblock.body.visit(self)
        self.popScope()
    def evaluate_StatementBody(self, stmtbody):
        # self.logger.debug('evaluate_StatementBody', stmtbody, len(stmtbody.statements))
        for stmt in stmtbody.statements:
            # self.logger.debug('evaluate_StatementBody stmt', stmt)
            stmt.visit(self)
            flowFlag = self.getFlowFlag()
            if flowFlag != FlowFlags.NORMAL:
                # self.logger.debug('evaluate_StatementBody break', stmt, flowFlag)
                break
    def evaluate_IfStatement(self, stmt):
        # self.logger.debug('evaluate_IfStatement', len(stmt.branches))
        for branch in stmt.branches:
            scope = self.pushScope()
            cond = branch.condition.visit(self)
            # self.logger.debug('evaluate_IfStatement branch', branch.condition, cond)
            assert cond is not None, ('evaluate_IfStatement', expr, expr.condition, cond)
            if cond and cond != self.nilValue:
                branch.body.visit(self)
                self.popScope()
                # self.logger.debug('evaluate_IfStatement branch match ret', branch.condition, cond, branch.body)
                return
            self.popScope()
        # self.logger.debug('evaluate_IfStatement else', len(stmt.branches))
        if stmt.elseBranch:
            stmt.elseBranch.visit(self)
    def evaluateNil_ClassDef(self, cls):
        return self.nilValue
    def evaluateNil_EnumDef(self, enumdef):
        return enumdef.items[0].value
    def evaluateUnaryOp_ClassDef(self, cls, op, operand):
        assert op in ['not']
        return operand is None
    def evaluateBinaryOp_ClassDef(self, cls, op, left, right):
        # self.logger.debug('evaluateBinaryOp_ClassDef', cls, op, left, right)
        left = left.visit(self)
        right = right.visit(self)
        # self.logger.debug('evaluateBinaryOp_ClassDef', cls, op, left, right)
        assert op in ['==', '!=', 'and', 'or']
        if op == '==':
            if right is None:
                return left is None
            return left == right
        if op == '!=':
            if right is None:
                return left is not None
            return left != right
        if op == 'and':
            return left and right
        if op == 'or':
            return left or right
        assert False, (op, left, right)
    def evaluateBinaryOp_EnumDef(self, cls, op, left, right):
        # self.logger.debug('evaluateBinaryOp_ClassDef', cls, op, left, right)
        left = left.visit(self)
        right = right.visit(self)
        # self.logger.debug('evaluateBinaryOp_ClassDef', cls, op, left, right)
        assert op in ['==', '!=', 'and', 'or']
        if op == '==':
            if right is None:
                return left is None
            return left == right
        if op == '!=':
            if right is None:
                return left is not None
            return left != right
        if op == 'and':
            return left and right
        if op == 'or':
            return left or right
        assert False, (op, left, right)


class FuncDefEvaluator(ast.AstNode):
    def __init__(self, f, clsvar):
        self.func = f
        self.clsvar = clsvar
    def __repr__(self):
        return 'FuncDefEvaluator:%s%s:this=%s:%s' % (self.func.cls.name + '.' if self.func.cls else '', self.func.name, self.clsvar, ast.formatId(self))
    def getValue(self):
        return self
    def evaluateCall(self, visitor, callinfo):
        # visitor.logger.debug('FuncDefEvaluator.evaluateCall', self, self.clsvar, callinfo.caller, visitor.getThis(), callinfo.args)
        # assert visitor.getThis() == self.clsvar
        this = None
        if (not self.func.spec.static) or self.func.injection_cls:
            if isinstance(callinfo.caller, ast.AttrRef):
                this = callinfo.caller.object.visit(visitor)
                # visitor.logger.debug('FuncDefEvaluator.evaluateCall new this', self.func, this, callinfo.caller.object)
            else:
                this = visitor.getThis()
                # visitor.logger.debug('FuncDefEvaluator.evaluateCall old this', self.func, this, callinfo.caller)
        # assert (visitor.getThis() is not None and not self.func.spec.static) or (visitor.getThis() is None and self.func.spec.static), (visitor.getThis(), self.func)
        return visitor.callFunc(self.func, self.clsvar, callinfo.args, dict(callinfo.namedArgs))

class ClassDefEvaluator(ast.AstNode):
    def __init__(self, cls, visitor):
        self.cls = cls
        self.visitor = visitor
        self.vars = {}
        self.bases = [ClassDefEvaluator(base.getTarget(), visitor) for base in cls.bases]
        for var in cls.vars:
            # print('ClassDefEvaluator.add', var.name, var, self.cls)
            innervar = visitor.createVar(var)
            # print('ClassDefEvaluator.add ok', var.name, var, self.cls, innervar)
            self.vars[var.name] = innervar
        # print('ClassDefEvaluator.init', self)
    def __repr__(self):
        name = self.vars.get('name') 
        return 'ClassDefEvaluator:%s%s:%s' % (self.cls.name, '(%s)' % name.getValue() if name else '', ast.formatId(self))
    def getLocalVar(self, name, clsvar):
        # assert False, (self, self.cls, name)
        # print('ClassDefEvaluator.getLocalVar', name, self, self.cls, clsvar, self.vars)
        obj = self.vars.get(name)
        if obj:
            # print('ClassDefEvaluator.getLocalVar var obj', name, self, self.cls, clsvar, obj)
            return obj
        obj = self.cls.symbols.get(name)
        # print('ClassDefEvaluator.getLocalVar found symbol', name, self, self.cls, self.vars, obj)
        if isinstance(obj, ast.FuncDef):
            # print('ClassDefEvaluator.getLocalVar found function', name, self, self.cls, self.vars, obj)
            return FuncDefEvaluator(obj, clsvar or self)
        assert obj is None, (self, name, clsvar, obj)
        return None
    def getVar(self, name, clsvar=None):
        # print('ClassDefEvaluator.getVar search bases', name, self, self.vars)
        if clsvar is None:
            clsvar = self
        nodes = [self]
        while len(nodes) > 0:
            node = nodes.pop(0)
            ret = node.getLocalVar(name, clsvar)
            if ret:
                return ret
            for base in node.bases:
                nodes.append(base)
        return None
    def getValue(self, name):
        # print('ClassDefEvaluator.getValue', name, self)
        return self.getVar(name).getValue()
    def setValue(self, name, val):
        if self.getValue(name) == [] and val is None:
            assert False, ('Class.setValue', self, name, val, self.getValue(name))
        self.getVar(name).setValue(val)
    def evaluateAttr(self, visitor, attr):
        # visitor.logger.debug('ClassDefEvaluator.evaluateAttr', attr.ref, self, attr)
        obj = self.getVar(attr.ref)
        if obj:
            return obj.getValue()
        visitor.logger.debug('ClassDefEvaluator.evaluateAttr cls', attr.ref, self, self.cls, attr, obj)
        return self.cls.evaluateAttr(visitor, attr)
    def evaluateAttrVar(self, visitor, attr):
        # visitor.logger.debug('ClassDefEvaluator.evaluateAttrVar', attr.ref, self, attr)
        return self.getVar(attr.ref)
    def evalConstructor(self, visitor, args, named_args, topclsvar):
        # visitor.logger.debug('ClassDefEvaluator.evalConstructor', self, visitor, args, named_args, self.bases)
        clsvar = topclsvar if topclsvar else self
        for b in self.bases:
            b.evalConstructor(visitor, [], {}, clsvar)
        visitor.evalFunc(self.cls.constructors[0], clsvar, args, named_args)
