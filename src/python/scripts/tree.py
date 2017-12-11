import ast

class TreeFunction(ast.ScriptFunction):
    def __init__(self):
        ast.ScriptFunction.__init__(self)
        self.cls = None
        self.inherit = False
    def processScript(self, visitor, owner):
        cls = owner.owner
        # visitor.logger.debug('TreeFunction.processScript', cls.name, cls, owner)
        assert isinstance(cls, ast.ClassDef), (cls, owner, self, visitor)
        self.insertTreeFunctions(cls, cls, visitor)
    def insertTreeFunctions(self, cls, basecls, visitor):
        self.insertInitializeOwner(cls, basecls, visitor)
        self.insertClone(cls, basecls, visitor)
        self.insertVisitChildren(cls, basecls, visitor)
        # self.insertDump(cls, basecls, visitor)
        # self.insertDumpCode(cls, basecls, visitor)
        self.insertToString(cls, basecls, visitor)
        # self.insertToSimpleString(cls, basecls, visitor)
        for subcls in cls.subclasses:
            # visitor.logger.debug('TreeFunction.processScript subcls', cls, subcls)
            self.insertTreeFunctions(subcls, basecls, visitor)
    def generateInitializeOwnerCall(self, cls, basecls, basefunc, field):
        # print('generateInitializeOwnerCall', basefunc.name, cls, field, basefunc)
        # msgstmt = ast.Call(ast.Identifier('println'), [ast.makeLiteral('generate initializeOwner start ' + field.name),
        #         ast.Identifier(field.name),
        #         ast.Call(ast.Identifier('toString'), [])])
        body = ast.StatementBody([
            # ast.Call(ast.Identifier('println'), [ast.makeLiteral('generate initializeOwner ' + field.name),
            #     ast.Identifier(field.name),
            #     ast.Call(ast.Identifier('toString'), [])]),
            ast.Call(ast.AttrRef(ast.Identifier(field.name), 'setOwner'), [ast.This()]), 
            self.generateSimpleFieldCall(cls, basecls, basefunc, field, 'initializeOwner')])
        branch = ast.IfBranch(ast.BinaryOp('!=', ast.Identifier(field.name), ast.Nil()), body) 
        # return ast.StatementBody([msgstmt, ast.IfStatement([branch], None)])
        return ast.IfStatement([branch], None)
    def insertInitializeOwner(self, cls, basecls, visitor):
        if cls.primaryVars:
            # visitor.logger.debug('insertInitializeOwner', cls, basecls, visitor)
            self.insertFunc(cls, basecls, visitor, 'initializeOwner', self.generateInitializeOwnerCall, self.generateStatements)
    def insertClone(self, cls, basecls, visitor):
        self.insertSimpleFunc(cls, basecls, visitor, 'clone', 'clone', self.generateCloneStatements)
    def insertVisitChildren(self, cls, basecls, visitor):
        if cls.primaryVars:
            self.insertSimpleFunc(cls, basecls, visitor, 'visitChildren', 'visit', self.generateStatements)
    def insertDump(self, cls, basecls, visitor):
        self.insertSimpleFunc(cls, basecls, visitor, 'dump', 'dump', self.generateStatements)
    def insertDumpCode(self, cls, basecls, visitor):
        self.insertSimpleFunc(cls, basecls, visitor, 'dumpCode', 'dumpCode', self.generateStatements)
    def insertToString(self, cls, basecls, visitor):
        # visitor.logger.debug('insertToString', cls, basecls)
        name = 'toString'
        if name not in cls.symbols:
            # visitor.logger.debug('insertToString do', cls, basecls)
            clsname = ast.Call(ast.Identifier('getClassName'), [])
            thisptr = ast.Call(ast.Identifier('formatId'), [])
            expr = None
            if 'name' in cls.symbols:
                # visitor.logger.debug('insertToString with name', cls, basecls, clsname, thisptr)
                expr = ast.BinaryOp('%', ast.makeLiteral('%s(name=%s,id=%s)'), ast.TupleLiteral([clsname, ast.Identifier('name'), thisptr]))
            else:
                # visitor.logger.debug('insertToString without name', cls, basecls, clsname, thisptr)
                expr = ast.BinaryOp('%', ast.makeLiteral('%s(id=%s)'), ast.TupleLiteral([clsname, thisptr]))
            func = ast.FuncDef([], name, ast.FuncSpec([], ast.makePrimitiveType('string')), ast.StatementBody([ast.Return(expr)]))
            # visitor.logger.debug('insertFunc ok', name, cls, basecls, cls.primaryVars, func)
            cls.definitions.append(func)
            func.setOwner(cls)
            visitor.visitNewItem(func)
    def generateCloneStatements(self, cls, basecls, visitor, stmts):
        # visitor.logger.debug('generateCloneStatements', visitor, basecls)
        assert len(stmts) <= len(cls.primaryVars)
        newfields = [ast.NamedExpressionItem(cls.primaryVars[i].name, stmts[i]) for i in range(len(cls.primaryVars))]
        return [ast.Return(ast.Call(ast.Identifier(cls.name), [], newfields))]
    def generateStatements(self, cls, basecls, visitor, stmts):
        # visitor.logger.debug('generateStatements', cls, basecls, visitor, stmts)
        assert len(stmts) <= len(cls.primaryVars)
        # newfields = [(cls.primaryVars[i].name, stmts[i]) for i in range(len(cls.primaryVars))]
        # return [ast.Return(ast.Call(ast.Identifier(cls.name), [], newfields))]
        return stmts
    def generateExprs(self, cls, basecls, visitor, stmts):
        # visitor.logger.debug('generateExprs', cls, basecls, visitor)
        assert len(stmts) <= len(cls.primaryVars)
        # newfields = [(cls.primaryVars[i].name, stmts[i]) for i in range(len(cls.primaryVars))]
        # return [ast.Return(ast.Call(ast.Identifier(cls.name), [], newfields))]
    def generateSimpleFieldCall(self, cls, basecls, basefunc, field, invokeFuncName):
        callinfo = ast.Call(ast.AttrRef(ast.Identifier(field.name), invokeFuncName), [ast.Identifier(param.name) for param in basefunc.spec.params]) 
        # teststmts = [ast.CallStatement(ast.Call(ast.Identifier('println'), [ast.makeLiteral('GenerateTreeFunc check ' + basefunc.name + ' ' + field.name), 
        #             ast.Identifier(field.name), 
        #             ast.Call(ast.Identifier('toString'), [])]))]
        teststmts = []
        isStatement = basefunc.spec.returnType is None or (isinstance(basefunc.spec.returnType, ast.UserType) and basefunc.spec.returnType.fullpath == 'void')
        if isStatement:
            body = ast.StatementBody([
                # ast.Call(ast.Identifier('println'), [ast.makeLiteral('GenerateTreeFunc ' + basefunc.name + ' ' + field.name), 
                #     ast.Call(ast.AttrRef(ast.Identifier(field.name), 'toString'), []), 
                #     ast.Call(ast.Identifier('toString'), [])]),
                callinfo])
            branch = ast.IfBranch(ast.BinaryOp('!=', ast.Identifier(field.name), ast.Nil()), body) 
            return ast.StatementBody(teststmts + [ast.IfStatement([branch], None)])
        return ast.IfElseExpr(ast.BinaryOp('!=', ast.Identifier(field.name), ast.Nil()), callinfo, ast.Nil())
    def getFieldCallGenerator(self, invokeFuncName):
        return lambda cls, basecls, basefunc, field: self.generateSimpleFieldCall(cls, basecls, basefunc, field, invokeFuncName)
    def insertSimpleFunc(self, cls, basecls, visitor, name, invokeFuncName, stmtsGen):
        return self.insertFunc(cls, basecls, visitor, name, self.getFieldCallGenerator(invokeFuncName), stmtsGen)
    def insertFunc(self, cls, basecls, visitor, name, fieldExprGen, stmtsGen):
        basefunc = basecls.symbols[name]
        if name not in cls.symbols:
            # visitor.logger.debug('insertFunc', name, cls, basecls, cls.primaryVars)
            stmts = [self.generateFieldExpr(cls, basecls, basefunc, fieldExprGen, visitor, field) for field in cls.primaryVars]
            stmts = [stmt for stmt in stmts if stmt is not None]
            stmts = stmtsGen(cls, basecls, visitor, stmts)
            func = ast.FuncDef([], name, basefunc.spec.clone(), ast.StatementBody(stmts))
            # visitor.logger.debug('insertFunc ok', name, cls, basecls, cls.primaryVars, func, stmts)
            cls.definitions.append(func)
            func.setOwner(cls)
            visitor.visitNewItem(func)
            # visitor.logger.debug('insertFunc visit ok', name, cls, basecls, cls.primaryVars, func, stmts)
    def generateFieldExpr(self, cls, basecls, basefunc, fieldExprGen, visitor, field):
        # visitor.logger.debug('generateFieldExpr', basefunc.name, cls, basecls, visitor, field, field.getType(), fieldExprGen)
        isStatement = basefunc.spec.returnType is None or (isinstance(basefunc.spec.returnType, ast.UserType) and basefunc.spec.returnType.fullpath == 'void')
        vartype = field.getType()
        assert isinstance(vartype, ast.Type), (field, field.name, vartype)
        assert vartype, (visitor, field)
        if isinstance(vartype, ast.UserType) and vartype.fullpath == 'List':
            fvar = None
            collcopy = ast.Slicing(ast.Identifier(field.name), None, None, None)
            # visitor.logger.debug('generateFieldExpr ListType', basefunc.name, cls, field)
            if isinstance(vartype.genericArgs[0].type, ast.UserType) and vartype.genericArgs[0].type.fullpath == 'Tuple':
                varnames = [field.name + '_item' + str(i) for i in range(len(vartype.genericArgs[0].type.elementTypes))]
                fvar = ast.createTupleVarDef(varnames, vartype.genericArgs[0].type.clone(), None)
                fvar.type.setTarget(vartype.genericArgs[0].type.getTarget())
            else:
                fvar = ast.SingleVarDef(field.name + '_item', vartype.genericArgs[0].type.clone(), None)
                fvar.type.setTarget(vartype.genericArgs[0].type.getTarget())
            if isStatement:
                stmts = self.generateFieldExpr(cls, basecls, basefunc, fieldExprGen, visitor, fvar)
                if stmts is None:
                    # assert basefunc.name != 'visitChildren', (cls, basecls, basefunc, field, isStatement, field.getType())
                    return None
                if not isinstance(stmts, list):
                    stmts = [stmts]
                else:
                    stmts = [stmt for stmt in stmts if stmt is not None]
                return ast.ForEachStatement(fvar, collcopy, ast.StatementBody(stmts)) if stmts else None
            else:
                listfor = ast.ListComprehensionFor(fvar, collcopy, None)
                # visitor.logger.debug('generateFieldExpr add ListComprehension', basefunc, cls, field)
                assert basefunc.name not in ['visitChildren', 'dump', 'dumpCode'], basefunc
                stmt = ast.ListComprehension(self.generateFieldExpr(cls, basecls, basefunc, fieldExprGen, visitor, fvar), [listfor])
                # visitor.logger.debug('generateFieldExpr ListComprehension', basefunc.name, stmt, cls, basecls, basefunc, field, listfor)
                return stmt
        if isinstance(vartype, ast.UserType) and vartype.fullpath == 'Tuple':
            assert isinstance(field, ast.TupleVarDef), (basecls, visitor, field)
            exprs = [self.generateFieldExpr(cls, basecls, basefunc, fieldExprGen, visitor, itemvar) for itemvar in field.vars]
            return exprs if isStatement else ast.TupleLiteral(exprs) 
        varcls = vartype.getTypeClass()
        if ast.isSubClass(varcls, basecls):
            callinfo = fieldExprGen(cls, basecls, basefunc, field)
            if isStatement:
                stmts = [ast.CallStatement(c) if isinstance(c, ast.Call) else c for c in callinfo] if isinstance(callinfo, list) else ast.CallStatement(callinfo) if isinstance(callinfo, ast.Call) else callinfo
                # visitor.logger.debug('generateFieldExpr ok', basefunc.name, cls, basecls, visitor, field, stmts)
                return stmts
            return callinfo
        # visitor.logger.debug('generateFieldExpr none', basefunc.name, isStatement, vartype, cls, basecls, visitor, field, varcls, ast.isSubClass(varcls, basecls))
        return None if isStatement else ast.Identifier(field.name)

def loadAll():
    return TreeFunction()
