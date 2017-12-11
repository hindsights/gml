
import ast
import builtins
import basetype

def chooseType(left, right):
    # print('chooseType', left, right, left.getType(), right.getType())
    return left.getType()


class TypeMatcher(ast.AstVisitor):
    def __init__(self):
        ast.AstVisitor.__init__(self)
        self.opname = 'matchType'
        self.name = 'typeMatcher'
    def visit(self, astree):
        return astree
    def matchType_UserType(self, ut, gtype, types):
        # self.logger.debug('matchType_UserType', ut, gtype, types)
        assert(isinstance(gtype, ast.UserType))
        assert(len(gtype.path) == 1)
        for t in types:
            if t == gtype.path[0]:
                # self.logger.debug('matchType_UserType match', ut, gtype, types, t)
                return t, ut
        assert(False)


class Resolver(ast.AstVisitor):
    def __init__(self):
        ast.AstVisitor.__init__(self)
        self.opname = 'resolve'
        self.name = 'resolver'
    def visit(self, astree):
        # self.logger.debug('Resolver.visit', self, astree, len(astree.definitions))
        self.ast = astree
        for i in self.ast.imports:
            i.visit(self)
        for d in self.ast.definitions:
            d.visit(self)
        return self.ast
    def resolve_Import(self, i):
        # self.logger.debug('resolve_Import', i, i.path)
        pass
    def resolveAttr_EnumDef(self, enumdef, attr):
        ret = enumdef.findMember(attr.ref)
        assert ret, (enumdef, attr, ret, attr.ref, attr.object, enumdef.symbols)
        return ret
    def resolveAttr_ClassDef(self, cls, attr):
        ret = cls.findMember(attr.ref)
        assert ret, (cls, attr, ret, attr.ref, attr.object, cls.functions, cls.vars, cls.symbols)
        return ret
    def resolve_ClassDef(self, cls):
        # self.logger.debug('resolve_ClassDef', cls, cls.name, len(cls.definitions))
        if cls.isProtoType():
            for p in cls.genericParams[:]:
                p.visit(self)
            return
        if cls.resolved:
            return cls
        cls.resolved = True
        for s in cls.scripts:
            # self.logger.debug('resolve_ClassDef script', s)
            s.visit(self)
        for b in cls.bases:
            b.visit(self)
            # self.logger.debug('resolve_ClassDef base', cls, cls.name, b)
            for s in b.getTarget().scripts:
                if s.getTarget().inherit:
                    # self.logger.debug('resolve_ClassDef base script', s, s.caller, s.args)
                    s2 = ast.Script(s.caller.path, s.args, s.namedArgs)
                    cls.scripts.append(s2)
                    s2.setOwner(cls)
                    s2.visit(self)
        for d in cls.definitions:
            # self.logger.debug('resolve_ClassDef def', cls.name, d)
            d.visit(self)
    def resolve_FuncDef(self, func):
        # self.logger.debug('resolve_FuncDef', func.name, func.resolved, func.cls, func)
        assert func.owner, (func, func.owner)
        owner = func.owner
        assert isinstance(owner, ast.ClassDef) or isinstance(owner, ast.CodeUnit) or isinstance(owner, ast.ExtensionDef), 'resolve_ClassDef owner is invalid: %s %s' % (owner, func)
        #assert isinstance(owner, ast.ClassDef) or isinstance(owner, ast.CodeUnit), 'resolve_FuncDef owner=%s' % owner
        if func.resolved:
            # assert func.spec.returnType, (func.name, func.spec.returnType, func)
            return
        func.resolved = True
        # self.logger.debug('resolve_FuncDef start', func, func.name)
        for param in func.spec.params:
            param.visit(self)
        if func.cls is None and isinstance(owner, ast.ClassDef):
            func.cls = owner
        func.spec.visit(self)
        func.body.visit(self)
        if func.spec.returnType is None:
            if len(func.body.statements) == 0:
                func.spec.returnType = ast.makePrimitiveType('void')
            else:
                lastStmt = func.body.statements[-1]
                # self.logger.debug('resolve_FuncDef rettype', func.name, func, lastStmt)
                if isinstance(lastStmt, ast.Return) and lastStmt.value:
                    assert func.spec.returnType is None, (func, func.spec)
                    func.spec.returnType = lastStmt.value.getType().clone()
                    # self.logger.debug('resolve_FuncDef rettype with return', lastStmt, lastStmt.value.getType(), func, func.spec)
                else:
                    func.spec.returnType = ast.makePrimitiveType('void')
            self.setupNewItem(func.spec.returnType, func.spec, True)
        if func.spec.returnType is None:
            assert False, (func, func.spec)
        # self.logger.debug('resolve_FuncDef end', func.name, func.resolved, func.spec.returnType, func.cls, func)
    def resolve_ForEachStatement(self, stmt=None):
        stmt.collection.visit(self)
        if stmt.item.getType() is None:
            stmt.item.setupType(stmt.collection.getType().getItemType(), self)
        stmt.body.visit(self)
    def resolve_ForEachDictStatement(self, stmt):
        # self.logger.debug('resolve_ForEachDictStatement', stmt, stmt.collection, stmt.collection.getType(), stmt.key, stmt.value)
        stmt.collection.visit(self)
        # self.logger.debug('resolve_ForEachDictStatement type', stmt, stmt.collection, stmt.collection.getType(), stmt.key, stmt.value)
        if stmt.key.getType() is None:
            stmt.key.setupType(stmt.collection.getType().getKeyType(), self)
        if stmt.value.getType() is None:
            stmt.value.setupType(stmt.collection.getType().getValueType(), self)
        stmt.key.visit(self)
        stmt.value.visit(self)
        # self.logger.debug('resolve_ForEachDictStatement', stmt.collection.getTarget())
        stmt.body.visit(self)
    def resolve_Script(self, script):
        sfunc = self.ast.project.findScript(script.caller.path)
        # self.logger.debug('resolve_Script', script, script.caller, sfunc, script.caller.path)
        script.setTarget(sfunc)
        sfunc.visit(self, script)
    def resolve_FuncSpec(self, funcspec):
        if funcspec.returnType:
            funcspec.returnType.visit(self)
        for param in funcspec.params:
            param.visit(self)
        funcspec.setupTypeClass(basetype.FunctionClass(funcspec), self)
        # self.logger.debug('resolve_FuncSpec end', funcspec, funcspec.returnType, funcspec.params)
    def resolve_TupleVarDef(self, var):
        if var.initial:
            var.initial.visit(self)
        if var.type is None:
            var.type = var.initial.getType()
        if var.type:
            assert isinstance(var.type, ast.UserType) and var.type.fullpath == 'Tuple', ('resolve_TupleVarDef', var, var.type, var.initial)
            etypes = var.type.getTarget().instantiation.genericArgs[0].types
            for i in range(len(var.vars)):
                var.vars[i].setExpectedType(etypes[i])
                var.vars[i].visit(self)
    def resolve_SingleVarDef(self, var):
        # self.logger.debug('resolve_SingleVarDef', var.name, var, var.owner, var)
        owner = var.owner
        assert owner == var.owner
        assert var.getType() is None or isinstance(var.getType(), ast.Type), (var, var.getType(), var.expectedType, var.initial)
        if var.initial:
            # self.logger.debug('resolve_SingleVarDef initial', var, var.name, var.initial)
            var.initial.visit(self)
            # self.logger.debug('resolve_SingleVarDef initial2', var, var.initial, var.initial.getType())
        if var.getType():
            var.getType().visit(self)
            # self.logger.debug('resolve_SingleVarDef type', var, var.getType(), var.getTypeClass())
        else:
            # self.logger.debug('resolve_SingleVarDef initial type', var, var.initial, var.getOwnerFunc())
            assert (var.initial and var.initial.getType()) or var.expectedType, (var, var.getOwnerFunc(), var.getOwnerFullContext(), var.initial, var.getType())
            var.setupType((var.initial.getType() if var.initial else None) or var.expectedType, self)
            assert isinstance(var.getType(), ast.Type), (var, var.getType(), var.expectedType, var.initial)
            # self.logger.debug('resolve_SingleVarDef initial type', var, var.getType())
        # self.logger.debug('resolve_SingleVarDef type_class', var.name, var.getTypeClass(), id(var), var.getType().getTarget())
        assert var.getType() is None or isinstance(var.getType(), ast.Type), (var, var.getType(), var.expectedType, var.initial)
        if hasattr(var.getTypeClass(), 'rettype'):
            var.returnType = var.getTypeClass().returnType
        assert var.getType(), var
        assert var.getTypeClass(), ('resolve_SingleVarDef', var, var.getType(), var.getOwnerFunc(), var.getOwnerClass())
        assert var.getType().getTypeClass(), var.getType()
    def resolve_GenericExpr(self, expr):
        expr.visitChildren(self)
        target = expr.base.getTarget()
        target = target.instantiate(expr.genericArgs, self)
        # self.logger.debug('resolve_GenericExpr target', expr, expr.base, expr.target, target)
        assert target
        expr.target = target
    def resolve_ConstSpec(self, var):
        # self.logger.debug('resolve_ConstSpec', var.name, var, var.owner)
        assert owner == var.owner
        if var.initial:
            # self.logger.debug('resolve_ConstSpec initial', var, var.name, var.initial)
            var.initial.visit(self)
            # self.logger.debug('resolve_ConstSpec initial2', var, var.initial, var.initial.getType())
        if var.getType():
            var.getType().visit(self)
            # self.logger.debug('resolve_ConstSpec type', var, var.getType(), var.getTypeClass())
        else:
            assert(var.initial and var.initial.getType())
            self.ast.setType(var, var.initial.getType())
            var.getType().visit(self)
            # self.logger.debug('resolve_ConstSpec initial type', var, var.getType())
        # self.logger.debug('resolve_ConstSpec type_class', var.name, var.getTypeClass(), id(var))
        if hasattr(var.getTypeClass(), 'rettype'):
            var.returnType = var.getTypeClass().returnType
        assert var.getType(), var
        assert var.getTypeClass(), var.getType()
        assert var.getType().getTypeClass(), var.getType()
    def resolveCall_AttrRef(self, attrref, callinfo):
        # self.logger.debug('resolveCall_AttrRef', attrref, callinfo, callinfo.caller, callinfo.caller.getTarget())
        callinfo.caller.getTarget().resolveCall(self, callinfo)
    def resolveCall_SingleVarDef(self, var, callinfo):
        # self.logger.debug('resolveCall_SingleVarDef', var, callinfo)
        pass
    def resolveCall_Identifier(self, idvar, callinfo):
        # self.logger.debug('resolveCall_Identifier', idvar, callinfo, callinfo.caller.getTarget())
        if callinfo.caller.getTarget():
            callinfo.caller.getTarget().resolveCall(self, callinfo)
    def resolve_Return(self, stmt):
        rettype = stmt.getOwnerFunc().spec.returnType
        # self.logger.debug('resolve_Return', stmt.values, stmt, rettype, stmt.getOwnerFunc(), stmt.getOwnerClass())
        stmt.expected_type = rettype
        expr = stmt.value
        # self.logger.debug('resolve_Return expr', stmt, expr, rettype)
        assert not isinstance(expr, list), ('resolve_Return value is list', expr, rettype, stmt, stmt.getOwnerFunc())
        if expr is not None:
            expr.setExpectedType(rettype)   
            expr.visit(self)
        # self.logger.debug('resolve_Return need_return expr', expr, expr.getTarget())
    def resolve_Call(self, callinfo):
        # self.logger.debug('resolve_Call', callinfo, callinfo.caller, callinfo.caller.getTarget(), callinfo.args, callinfo.getType(), callinfo.getOwnerFunc())
        callinfo.caller.visit(self)
        assert callinfo.caller.getTarget(), ('resolve_Call caller.target', callinfo, callinfo.caller, callinfo.caller.getTarget(), callinfo.args, callinfo.getType(), callinfo.getOwnerFunc())
        callinfo.caller.getTarget().visit(self)
        callinfo.caller.getTarget().resolveCall(self, callinfo)
        func = callinfo.caller.getTarget()
        spec = callinfo.getSpec()
        assert func.getSpec() is not None and spec, ('resolve_Call', callinfo, func, func.spec, spec)
        # self.logger.debug('resolve_Call spec', callinfo, callinfo.caller, callinfo.args, spec, callinfo.getType())
        for i in range(len(callinfo.args)):
            arg = callinfo.args[i]
            # self.logger.debug('resolve_Call arg %d' % i, arg, spec)
            # self.logger.debug('resolve_Call arg %d' % i, arg, callinfo.caller, spec, arg.getType(), spec.params[i].getType() if i < len(spec.params) else None)
            expectedArgType = spec.params[i].getType() if i < len(spec.params) else None
            # self.logger.debug('resolve_Call arg visit', i, arg, callinfo.caller, expectedArgType, spec.params)
            arg.setExpectedType(expectedArgType)
            arg.visit(self)
            if i < len(spec.params):
                param = spec.params[i]
                if arg.getType() is None:
                    assert False, (self, arg, param, arg.getType(), param.getType())
                    self.ast.setType(arg, param.getType())
            if arg.getType() is None:
                pass
            # self.logger.debug('resolve_Call arg.resolve', callinfo, arg, arg.getTarget(), arg.getType(), arg.getType().getTarget())
            assert arg.getType(), arg
        for arginfo in callinfo.namedArgs:
            name = arginfo.name
            arg = arginfo.value
            func = callinfo.caller.getTarget()
            if isinstance(func, ast.ClassDef):
                field = func.findLocalSymbol(name)
                assert field, ('resolve_Call field', func, name, field, callinfo.getOwnerFunc())
                arg.setExpectedType(field.getType())
            arg.visit(self)
            assert arg.getType(), ('resolve_Call named_arg arg.getType() is None:%s,%s' % (name, arg), arg.getOwnerFunc(), arg.getOwnerClass())
        assert callinfo.getType(), (callinfo, spec)
    def resolveAttr_AstNode(self, node, expr):
        # self.logger.debug('resolveAttr_AstNode', node, expr, node.getTypeClass())
        return node.getTypeClass().resolveAttr(self, expr) if node.getTypeClass() else None
    def resolve_AttrRef(self, expr):
        # self.logger.debug('resolve_AttrRef', expr, expr.object, expr.ref, expr.getOwnerFunc(), expr.object.getType(), expr.getOwnerFunc())
        expr.object.visit(self)
        expr.target = expr.object.resolveAttr(self, expr)
        # self.logger.debug('resolve_AttrRef target 2', expr, expr.object, expr.ref, expr.target, expr.object.getType(), expr.object.getTypeClass(), expr.getOwner())
        assert expr.getTarget(), ('resolve_AttrRef no target', expr, expr.object, expr.object.getType(), expr.ref, expr.getOwner())
        if expr.getTarget():
            expr.getTarget().visit(self)
        return expr
    def resolve_Identifier(self, expr):
        owner = expr.owner
        expr.target = owner.findSymbol(expr.name)
        # self.logger.debug('resolve_Identifier target', expr, expr.name, expr.getTarget())
        assert expr.getTarget(), (expr, expr.getTarget(), expr.getOwnerFunc())
        expr.getTarget().visit(self)
        assert expr.getType(), (expr, expr.getTarget(), expr.getTarget().getType())
        # assert expr.getType().getTarget(), (expr, expr.getType(), expr.getTarget(), expr.getTarget().getType(), expr.owner, expr.getOwnerFunc())
        if expr.name == 'funcname':
            assert expr.getType(), expr
            assert expr.getTypeClass(), expr
            assert expr.getType().getTypeClass(), expr.getType()
        # self.logger.debug('resolve_Identifier target', expr, expr.name, expr.getTarget(), expr.getType(), expr.getTypeClass())

    def resolve_Assignment(self, expr=None):
        # self.logger.debug('resolve_Assignment', expr, expr.targets, expr.values, expr.owner)
        expr.visitChildren(self)
        for i in range(len(expr.values)):
            val = expr.values[i]
            if isinstance(val, ast.ListLiteral) and (not val.values) and val.getType() is None:
                val.expectedType = expr.targets[i].getType()
    def resolve_NamedExpressionItem(self, item):
        # assert False, (item, item.owner, item.value)
        item.visitChildren(self)
    def resolve_EnumDef(self, expr):
        pass
    def resolve_Break(self, expr):
        pass
    def resolve_Continue(self, expr):
        pass
    def resolve_This(self, expr):
        # self.logger.debug('resolve_This', expr.owner, expr.getOwnerFunc(), expr.getOwnerClass())
        if expr.getType() is None:
            expr.setupType(ast.UserType([expr.getOwnerClass().name]), self)

    def resolve_ListLiteral(self, literal):
        # self.logger.debug('resolve_ListLiteral', self, literal, literal.owner, literal.expectedType, literal.getOwnerFunc())
        if literal.getType() is None:
            for val in literal.values:
                val.visit(self)
            if literal.values:
                # assert not isinstance(literal.values[0].getType(), ast.ListType), literal.values[0]
                assert not isinstance(literal.values[0].getType(), ast.ClassDef), literal.values[0]
                # assert literal.values[0].getType(), literal.values[0]
                if literal.values[0].getType():
                    literal.setupType(ast.createListType(literal.values[0].getType().clone()), self)
            else:
                if literal.expectedType:
                    literal.setupType(literal.expectedType, self)
        else:
            for val in literal.values:
                val.visit(self)
            literal.getType().visit(self)
        return literal
    def resolve_TupleLiteral(self, literal):
        # self.logger.debug('resolve_TupleLiteral', self, literal, literal.owner, literal.getOwnerFunc())
        if literal.expectedType:
            assert isinstance(literal.expectedType, ast.UserType) and literal.expectedType.fullpath == 'Tuple' and isinstance(literal.expectedType.getTarget(), builtins.GenericTupleClassImpl), ('resolve_TupleLiteral', self, literal, literal.expectedType, literal.owner, literal.getOwnerFunc())
        for i in range(len(literal.values)):
            val = literal.values[i]
            if literal.expectedType:
                assert i < len(literal.expectedType.target.instantiation.genericArgs[0].types)
                val.setExpectedType(literal.expectedType.target.instantiation.genericArgs[0].types[i])
            val.visit(self)
            if val.getType() is None:
                assert literal.expectedType and isinstance(literal.expectedType, ast.UserType), ('resolve_TupleLiteral invalid type', literal.values, val, literal.expectedType, literal.getOwnerFunc())
        if literal.getType() is None:
            literal.setupType(ast.makeType(tuple([val.getType() for val in literal.values])), self)
    def resolve_ListComprehensionFor(self, expr):
        # self.logger.debug('ListComprehensionFor.resolve', self, expr)
        expr.source.visit(self)
        assert expr.source.getType().getItemType(), ('ListComprehensionFor.resolve', expr, expr.source, expr.source.getType())
        if expr.variable.getType() is None:
            expr.variable.setupType(expr.source.getType().getItemType(), self)
        # self.logger.debug('ListComprehensionFor.resolve before visit var', self, expr, expr.variable, expr.variable.getType())
        expr.variable.visit(self)
        assert expr.variable.getType(), (expr.variable)
        assert expr.variable.getTarget().getType(), (expr.variable)
        if expr.condition:
            expr.condition.visit(self)
    def resolve_ListComprehension(self, expr):
        # self.logger.debug('resolve_ListComprehension', expr, expr.getType(), expr.getOwnerFunc())
        if expr.getType() is None:
            for xfor in expr.fors:
                xfor.visit(self)
            expr.expr.visit(self)
            assert expr.expr.getType(), (expr.expr)
            assert expr.expr.getTypeClass(), (expr.expr)
            expr.setupType(ast.createListType(expr.expr.getType().clone()) if expr.expr.getType() else expr.expectedType, self)
        else:
            for xfor in expr.fors:
                xfor.visit(self)
            expr.expr.visit(self)
        assert expr.getTypeClass(), (expr, expr.getType())
    def resolve_CaseEntryExpr(self, expr):
        expr.expr.setExpectedType(expr.getOwnerFunc().spec.returnType)
        expr.visitChildren(self)
    def resolve_IfElseExpr(self, expr):
        # self.logger.debug('resolve_IfElseExpr', expr.condition, expr.truePart, expr.truePart.getType(), expr.falsePart, expr.falsePart.getType())
        if expr.truePart.getType() is None:
            # self.logger.debug('resolve_BinaryOp set left', expr.condition, expr.truePart, expr.truePart.getType(), expr.falsePart, expr.falsePart.getType())
            expr.truePart.setExpectedType(expr.falsePart.getType())
        elif expr.falsePart.getType() is None:
            # self.logger.debug('resolve_BinaryOp set right', expr.condition, expr.truePart, expr.truePart.getType(), expr.falsePart, expr.falsePart.getType())
            expr.falsePart.setExpectedType(expr.truePart.getType())
        expr.condition.visit(self)
        expr.truePart.visit(self)
        if expr.falsePart.getType() is None:
            expr.falsePart.setExpectedType(expr.truePart.getType())
        expr.falsePart.visit(self)
        if expr.truePart.getType() is None:
            expr.truePart.setExpectedType(expr.falsePart.getType())
        elif expr.falsePart.getType() is None:
            expr.falsePart.setExpectedType(expr.truePart.getType())
        assert expr.truePart.getType() and expr.truePart.getTypeClass(), (expr.truePart, expr.truePart.getType(), expr.truePart.getTypeClass())
        assert expr.falsePart.getType() and expr.falsePart.getTypeClass(), (expr.falsePart, expr.falsePart.getType(), expr.falsePart.getTypeClass())
    def resolve_BinaryOp(self, expr):
        # self.logger.debug('resolve_BinaryOp', expr.op, expr.left, expr.left.getType(), expr.right, expr.right.getType())
        if expr.op == '%':
            pass
        elif expr.left.getType() is None:
            # self.logger.debug('resolve_BinaryOp set left', expr.op, expr.left, expr.left.getType(), expr.right, expr.right.getType())
            expr.left.setExpectedType(expr.right.getType())
        elif expr.right.getType() is None:
            # self.logger.debug('resolve_BinaryOp set right', expr.op, expr.left, expr.left.getType(), expr.right, expr.right.getType())
            expr.right.setExpectedType(expr.left.getType())
        expr.left.visit(self)
        if expr.right.getType() is None and expr.op != '%':
            expr.right.setExpectedType(expr.left.getType())
        expr.right.visit(self)
        if expr.op == '%':
            pass
        elif expr.left.getType() is None:
            expr.left.setExpectedType(expr.right.getType())
        elif expr.right.getType() is None:
            expr.right.setExpectedType(expr.left.getType())
        assert expr.left.getType() and expr.left.getTypeClass(), (expr.left, expr.right, expr.op, expr.left.getType(), expr.left.getTypeClass())
        assert expr.right.getType() and expr.right.getTypeClass(), (expr.left, expr.right, expr.op, expr.right.getType(), expr.right.getTypeClass())
    def resolve_Closure(self, closure):
        expectedType = closure.expectedType
        assert expectedType, ('resolve_Closure', closure, closure.getOwner())
        assert isinstance(expectedType, ast.FuncSpec), (closure)
        if closure.spec is None:
            closure.spec = expectedType.clone()
            self.setupNewItem(closure.spec, closure, False)
        # self.logger.debug('resolve_Closure', closure, closure.getOwnerFunc(), expectedType, closure.spec, closure.getType().params)
        closure.visitChildren(self)
    def resolve_ArgumentPlaceholder(self, param):
        # self.logger.debug('resolve_ArgumentPlaceholder', param, param.sequence, param.getType(), param.owner, param.closure, param.getOwnerFunc())
        if param.closure is None:
            param.closure = param.getOwnerClosure()
        assert param.getType() and param.getTypeClass(), ('resolve_ArgumentPlaceholder', param, param.getOwnerClosure(), param.type, param.type.getTypeClass() if param.type else None, param.expectedType, param.getOwnerFunc(), param.owner, param.owner.owner)
        param.visitChildren(self)
    def resolve_TypeDef(self, typeexpr):
        # self.logger.debug('resolve_TypeDef', typeexpr.name, typeexpr, typeexpr.elementType)
        typeexpr.target.visit(self)
        # self.logger.debug('resolve_TypeDef end', typeexpr.name, typeexpr, typeexpr.elementType, typeexpr.getTypeClass())
    def resolve_UserType(self, ut):
        owner = ut.owner
        assert owner, (ut, self, ut.getOwnerFunc(), ut.getOwnerClass())
        # self.logger.debug('resolve_UserType', ut, ut.getTypeClass(), ut.getTarget(), owner, ut.getOwnerFunc())
        if ut.getTypeClass() and ut.getTarget():
            return
        ut.visitChildren(self)
        # self.logger.debug('resolve_UserType', ut.path, ut)
        target = owner.resolveSymbol(ut.path)
        # self.logger.debug('resolve_UserType1', ut, ut.path, target)
        if target is not None:
            ut.setTarget(target)
        # self.logger.debug('resolve_UserType target', ut, ut.path, ut.getTypeClass())

