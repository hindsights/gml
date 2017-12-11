
import ast
import parser

class OwnerInitializer(ast.AstVisitor):
    def __init__(self):
        ast.AstVisitor.__init__(self)
        self.opname = 'initializeOwner'
        self.name = 'ownerInitializer'
        self.project = None
        # self.logger.debug('OwnerInitializer.init')
    def previsit(self, node):
        # self.logger.debug('OwnerInitializer.previsit', node, self)
        self.autoVisit(node, self.visitChild)
    def visitChild(self, node, owner):
        # self.logger.debug('OwnerInitializer.visitChild', node, owner)
        assert owner
        node.setOwner(owner)
        # node.visit(self)
        self.autoVisit(node, self.visitChild)
    def visit(self, astree):
        # self.logger.debug('OwnerInitializer.visit', astree.name, self, len(astree.definitions), astree.imports)
        self.ast = astree
        astree.visit(self)

class PreExpander(ast.AstVisitor):
    def __init__(self):
        ast.AstVisitor.__init__(self)
        self.opname = 'preexpand'
        self.name = 'preexpander'
        self.project = None
        # self.logger.debug('PreExpander.init')
    def visit(self, astree):
        # self.logger.debug('PreExpander.visit', self, len(astree.definitions), astree.imports)
        self.ast = astree
        self.contexts = []
        astree.visit(self)
    def preexpand_CaseClassDef(self, casecls):
        cls = ast.ClassDef(casecls.scripts, casecls.name, casecls.genericParams, [ast.UserType([casecls.owner.name])], casecls.fields, casecls.definitions, ast.ClassType.normal)
        assert casecls.owner.owner
        clsOwner = casecls.owner.owner.getOwnerFullContext()
        clsOwner.definitions.append(cls)
        self.setupNewItem(cls, clsOwner, False)
    def preexpand_FuncDef(self, func):
        if func.receiver:
            extdef = ast.ExtensionDef(func.receiver.fullpath, [func])
            func.owner.definitions.append(extdef)
            extdef.setOwner(func.owner)
            func.owner.definitions.remove(func)
            func.setOwner(extdef)
            # self.logger.debug('preexpand_FuncDef', func.name, func, func.receiver, extdef)
            func.receiver = None
            return

class ScriptProcessor(ast.AstVisitor):
    '''analyzations before names are analyzed
    '''
    def __init__(self):
        ast.AstVisitor.__init__(self)
        self.opname = 'processScript'
        self.name = 'scriptProcessor'
        # self.logger.debug('ScriptProcessor.init')
    def visit(self, astree):
        # self.logger.debug('ScriptProcessor.visit', astree.name, self)
        self.ast = astree
        self.ast.visit(self)
    def processScript_Script(self, script):
        # self.logger.debug('processScript_Script', script, script.caller.path)
        sfunc = self.ast.project.findScript(script.caller.path)
        # self.logger.debug('processScript_Script func', script, script.caller.path, sfunc)
        script.caller.target = sfunc
        script.setTarget(sfunc)
        script.sfunc = sfunc
        sfunc.processScript(self, script)
    def processScript_ClassDef(self, cls):
        # self.logger.debug('processScript_ClassDef', cls, cls.name, cls.getTypeClass(), len(cls.definitions), len(cls.scripts), len(cls.bases), cls.script_processed)
        if cls.script_processed:
            return
        if cls.isProtoType():
            for p in cls.genericParams[:]:
                p.visit(self)
            return
        cls.script_processed = True
        owner = cls.owner
        # self.logger.debug('processScript_ClassDef type_class', cls, cls.name, cls.getTypeClass())
        for s in cls.scripts:
            # self.logger.debug('processScript_ClassDef script', s)
            s.visit(self)
        for b in cls.bases:
            # self.logger.debug('processScript_ClassDef base', cls.name, cls, b, len(b.getTarget().scripts))
            assert b.getTarget(), ('processScript_ClassDef base', cls.name, cls, b)
            b.getTarget().visit(self)
            for s in b.getTarget().scripts:
                if s.getTarget().inherit:
                    # self.logger.debug('processScript_ClassDef base script', cls.name, b, s, s.caller, s.args, len(cls.scripts), len(b.getTarget().scripts), cls, '0x%08x' % id(cls.scripts))
                    s2 = ast.Script(s.caller.path, s.args, s.namedArgs)
                    cls.scripts.append(s2)
                    assert len(cls.scripts) < 50
                    s2.setOwner(cls)
                    self.visitNewItem(s2)
                    s2.visit(self)
        # cls.visitChildren(self)
    def processScript_FuncDef(self, func):
        for script in func.scripts:
            script.visit(self)
    def processScript_SingleVarDef(self, var):
        pass


class NameCacher(ast.AstVisitor):
    def __init__(self):
        ast.AstVisitor.__init__(self)
        self.opname = 'cacheName'
        self.name = 'nameCacher'
        # self.logger.debug('NameCacher.init', super(NameCacher, self), super(NameCacher, self).__init__, ast.AstNode.__init__, ast.AstNode)
    def expandImports(self):
        newImports = []
        for imp in self.ast.imports:
            if imp.names:
                for name in imp.names:
                    # self.logger.debug('cacheName_ imports', imp.path, name)
                    newImports.append(ast.Import(imp.path + [name]))
            else:
                newImports.append(imp)
        # self.logger.debug('expandImports', self.ast.imports, newImports, len(self.ast.imports), len(newImports))
        self.ast.imports = newImports
    def visit(self, astree):
        self.ast = astree
        assert self.ast.definitions, astree.name
        # self.logger.debug('NameCacher.visit', self.ast.name, len(self.ast.definitions), self.ast.pkg, self.ast.imports)
        self.expandImports()
        astree.visit(self)
    def cacheName_TypeDef(self, typedef):
        typedef.owner.addSymbol(typedef)
    def cacheName_ClassDef(self, cls):
        # self.logger.debug('cacheName_ClassDef', cls, cls.owner, cls.instantiator, cls.instantiation)
        owner = cls.owner
        assert not owner.hasSymbol(cls.name)
        assert not isinstance(owner, ast.StatementBlock)
        if cls.isProtoType():
            owner.addSymbol(cls)
            for p in cls.genericParams[:]:
                p.visit(self)
            return
        if cls.isSimpleClass():
            owner.addSymbol(cls)
        cls.destructor = None
        for d in cls.definitions:
            # self.logger.debug('cacheName_ClassDef def', cls.name, d, cls)
            assert not cls.isProtoType() or cls.isInstantiation(), (cls.name, cls, d)
            d.visit(self)
        for script in cls.scripts:
            script.visit(self)
        if len(cls.constructors) == 0:
            cons = ast.FuncDef([], cls.name, ast.FuncSpec([], None), ast.StatementBody([]))
            # self.logger.debug('cacheName_ClassDef add constructor', cls.name, cons, cls)
            cons.info.type = ast.FuncType.constructor
            cls.constructors.append(cons)
            cls.definitions.append(cons)
            self.setupNewItem(cons, cls, True)
    def cacheName_ConstSpec(self, var):
        # self.logger.debug('cacheName_ConstSpec', var.name, var, var.getType(), var.initial, var.initial.getType() if var.initial else None)
        assert False
    def cacheName_FuncProto(self, func):
        # self.logger.debug('cacheName_FuncProto', func, func.name, func.owner)
        assert not isinstance(func.owner, ast.FuncDef), (func)
        if func.spec.returnType is None:
            func.spec.returnType = ast.makePrimitiveType('void')
            func.spec.returnType.setOwner(func.spec)
        func.visitChildren(self)
        func.owner.functions.append(func)
        func.owner.addSymbol(func)
        assert func.name != 'StringTypeClass' or isinstance(func.owner, ast.ClassDef)
    def cacheName_FuncDef(self, func):
        # self.logger.debug('cacheName_FuncDef', func.name, func, func.owner)
        owner = func.owner
        if isinstance(func.owner, ast.ClassDef):
            if func.name == func.owner.name:
                # self.logger.debug('cacheName_FuncDef constructor', func.name, func, func.owner)
                assert func.name != 'GenericTypeClass' or func.owner.isInstantiation(), (func.name, func, func.owner)
                func.info.type = ast.FuncType.constructor
                func.owner.constructors.append(func)
            elif func.name == "~" + func.owner.name:
                # self.logger.debug('initializeOwner_FuncDef destructor', func, func.name)
                func.info.type = ast.FuncType.destructor
                func.owner.destructor = func
        assert func.owner, (func.name, func)
        # self.logger.debug('cacheName_FuncDef', func.name, func, func.info.type, func.getOwnerFullContext())
        assert not owner.hasSymbol(func.name), (func.name, func, owner, func.info.type, owner.definitions, owner.symbols[func.name])
        for param in func.spec.params:
            func.addSymbol(param)
        if func.info.type == ast.FuncType.normal:
            if isinstance(owner, ast.ExtensionDef):
                # self.logger.debug('cacheName_FuncDef inject', func.name, func, owner, owner.cls)
                owner.addSymbol(func)
            else:
                assert func.name != owner.name, (func, owner)
                owner.addFunc(func)
        for script in func.scripts:
            script.visit(self)
        func.body.visit(self)
        if func.cls is None and isinstance(owner, ast.ClassDef):
            func.cls = owner
        # self.logger.debug('cacheName_FuncDef ok', func.name, func, func.info.type)
        return func
    def cacheName_EnumDef(self, enumdef):
        # self.logger.debug('cacheName_EnumDef', enumdef.name, enumdef)
        assert enumdef.getOwnerFullContext() == enumdef.owner
        enumdef.owner.addSymbol(enumdef)
        enumdef.visitChildren(self)
        return enumdef
    def cacheName_SingleVarDef(self, var):
        owner = var.getOwnerBlockContext()
        # self.logger.debug('cacheName_SingleVarDef', var.name, var, var.owner, var.getType(), var.initial, var.initial.getType() if var.initial else None, owner)
        assert not owner.hasSymbol(var.name), (var.name, owner.symbols, var, owner, var.owner)
        owner.addVar(var)
        assert var.cls is None
        if isinstance(owner, ast.ClassDef):
            var.cls = owner
        if var.initial:
            var.initial.visit(self)
    def cacheName_VarTag(self, tag):
        if tag.name:
            tag.getOwnerBlockContext().addSymbol(tag)
        tag.visitChildren(self)


def convert_string_literal(text):
    # process string evaluation
    # print('convert_string_literal', text)
    pos = text.find('$')
    if pos >= 0:
        # check if it's preceded by a backslash
        if pos == 0 or text[pos-1] != '\\':
            if pos + 1 < len(text):
                nexttag = text[pos+1]
                if nexttag == '{':
                    endpos = text.find('}', pos+1)
                    if endpos >= 0:
                        exprstr = text[pos+2:endpos]
                        expr = parser.exprParser.parse(exprstr)
                        newtext = text[:pos] + "%s" + text[endpos+1:]
                        # print('convert_string_literal brace part', text, exprstr, expr, newtext)
                        realtext, exprs = convert_string_literal(newtext)
                        return realtext, [expr] + exprs
                elif nexttag == '_' or nexttag.isalpha():
                    idname = nexttag
                    i = pos + 2
                    while i < len(text):
                        ch = text[i]
                        if ch == '_' or ch.isalpha():
                            idname += ch
                        else:
                            break
                    # print('convert_string_literal idname', idname, text)
                    expr = ast.Identifier(idname)
                    newtext = text[:pos] + "%s" + text[i:]
                    realtext, exprs = convert_string_literal(newtext)
                    return realtext, [expr] + exprs
    return text, []

class NameResolver(ast.AstVisitor):
    def __init__(self):
        ast.AstVisitor.__init__(self)
        self.opname = 'resolveName'
        self.name = 'nameResolver'
        # self.logger.debug('NameResolver.init', super(NameResolver, self), super(NameResolver, self).__init__, ast.AstNode.__init__, ast.AstNode)
    def visit(self, astree):
        # self.logger.debug('NameResolver.visit', astree)
        self.ast = astree
        self.resolveImports()
        assert(self.ast.definitions)
        # self.logger.debug('NameResolver.visit', self.ast.name, len(self.ast.definitions), astree.imports)
        astree.visit(self)
        # self.logger.debug('NameResolver.visit ok', astree.name, len(self.ast.definitions))
    def resolveImports(self):
        # self.logger.debug('resolveImports')
        newImports = []
        for imp in self.ast.imports:
            # self.logger.debug('resolveimports2', imp.path)
            newimport = self.analyzeImport(imp)
            if newimport:
                newImports.append(newimport)
        self.ast.imports = newImports
        # self.logger.debug('resolveName imports', self.ast.imports, newImports)
    def analyzeImport(self, i):
        # self.logger.debug("analyzeImport", i, i.path)
        item = self.ast.project.pkg.resolveSymbol(i.path)
        # self.logger.debug('analyzeImport dir', i.path, item)
        if item is None:
            target = self.ast.project.resolveSymbol(i.path)
            if target:
                i.setTarget(target)
                self.ast.addSymbol(target)
                # self.logger.debug('analyzeImport project', i.path, target)
            else:
                # self.logger.debug('analyzeImport project failed', i.path, target)
                assert False, ('analyzeImport', i.path, self.ast.name)
            return i
        i.setTarget(item)
        self.ast.addSymbol(item)
        # self.logger.debug('analyzeImport dir2', i.path, item, i.getTarget())
        return i
    def resolveName_Import(self, i):
        # self.logger.debug("resolveName_Import", i, i.path)
        item = self.ast.project.pkg.resolveSymbol(i.path)
        # self.logger.debug('resolveName_Import dir', i.path, item)
        i.setTarget(item)
        # self.logger.debug('resolveName_Import dir2', i.path, item, i.getTarget())
        assert(item)
    def resolveName_Script(self, script):
        # self.logger.debug('resolveName_Script', script.caller.path, script)
        sfunc = self.ast.project.findScript(script.caller.path)
        script.setTarget(sfunc)
        if sfunc != script:
            sfunc.visit(self, script)
    def resolveName_Call(self, callinfo):
        callinfo.caller.visit(self)
        # self.logger.debug('resolveName_Call caller', callinfo.caller, callinfo.caller.getTarget())
        if callinfo.caller.getTarget():
            callinfo.caller.getTarget().resolveNameRef(self, callinfo)
        for arg in callinfo.args:
            arg.visit(self)
        for arginfo in callinfo.namedArgs:
            assert isinstance(arginfo.value, ast.AstNode), (arginfo, callinfo.args, callinfo.namedArgs)
            arginfo.visit(self)
    def resolveName_ClassDef(self, cls):
        # self.logger.debug('resolveName_ClassDef', cls, cls.name, len(cls.definitions))
        if cls.type_name_resolved:
            return
        if cls.isProtoType():
            for p in cls.genericParams[:]:
                # self.logger.debug('resolveName_ClassDef genericParam', cls, p)
                p.visit(self)
            return
        cls.type_name_resolved = True
        # self.logger.debug('resolveName_ClassDef type_class', cls, cls.name, cls.getTypeClass())
        for script in cls.scripts:
            script.visit(self)
        for b in cls.bases:
            b.visit(self)
            assert b.getTarget()
            # self.logger.debug('resolveName_ClassDef base', cls.name, b)
            b.getTarget().subclasses.append(cls)
        for d in cls.definitions:
            # self.logger.debug('resolveName_ClassDef def', cls.name, d)
            d.visit(self)
    def resolveName_ExtensionDef(self, extdef):
        # self.logger.debug('resolveName_ExtensionDef', extdef.name, extdef, len(extdef.definitions))
        cls = extdef.owner.findSymbol(extdef.name)
        assert cls, (extdef.name, extdef, self)
        extdef.cls = cls
        extdef.visitChildren(self)
    def resolveName_FuncDef(self, func):
        # self.logger.debug('resolveName_FuncDef', func.name, func, func.owner)
        if isinstance(func.owner, ast.ExtensionDef):
            func.cls = func.owner.cls
            func.owner.cls.addSymbol(func)
        owner = func.owner
        if func.info.type == ast.FuncType.constructor:
            # self.logger.debug('resolveName_FuncDef constructor returnType', func.name, func, func.owner)
            assert func.spec.returnType is None
            func.spec.returnType = ast.UserType([func.cls.name])
            self.setupNewItem(func.spec.returnType, func.spec, False)
        assert isinstance(owner, ast.ClassDef) or isinstance(owner, ast.CodeUnit) or isinstance(owner, ast.ExtensionDef), 'resolveName_FuncDef owner is invalid: %s %s' % (owner, func)

        if func.info.type == ast.FuncType.constructor:
            for var in func.owner.vars:
                if var.initial:
                    stmt = ast.Assignment([ast.Identifier(var.name)], '=', [var.initial])
                    func.body.statements.insert(0, stmt)
                    # self.logger.debug('resolveName_FuncDef initialize var', func.name, stmt, var, var.initial)
                    self.setupNewItem(stmt, func.body, False)
        func.visitChildren(self)
    def resolveName_SingleVarDef(self, var):
        # self.logger.debug('resolveName_SingleVarDef', var.name, var, var.owner)
        owner = var.owner.owner if isinstance(var.owner, ast.MultipleVarDef) else var.owner
        if isinstance(owner, ast.ExtensionDef):
            var.cls = owner.cls
            owner.cls.addSymbol(var)
            owner.cls.vars.append(var)
        var.visitChildren(self)
    def resolveName_Identifier(self, expr):
        owner = expr.owner
        target = expr.owner.findSymbol(expr.name)
        # self.logger.debug('resolveName_Identifier', expr.name, expr, owner, target, owner.getOwnerBlockContext(), owner.getOwnerFullContext())
        expr.target = target
    def resolveName_UserType(self, ut):
        if ut.getTarget():
            return
        # self.logger.debug('resolveName_UserType', ut.path, ut, ut.genericArgs, ut.getOwner())
        ut.visitChildren(self)
        target = ut.owner.resolveSymbol(ut.path)
        if ut.genericArgs:
            # self.logger.debug('resolveName_UserType with genericArgs', ut, ut.genericArgs, target)
            target = target.instantiate(ut.genericArgs, self)
            # self.logger.debug('resolveName_UserType with genericArgs result', ut, ut.genericArgs, target)
        # self.logger.debug('resolveName_UserType result', ut, ut.path, ut.genericArgs, target)
        if target is not None:
            ut.setTarget(target)
        # self.logger.debug('resolveName_UserType target', ut, ut.path, ut.getTypeClass())
    def resolveName_StringEvaluation(self, se):
        # self.logger.debug('resolveName_StringEvaluation convert', se.literal)
        text, exprs = convert_string_literal(se.literal.value)
        if len(exprs) == 0:
            return
        # self.logger.debug('resolveName_StringEvaluation convert', text, exprs)
        formatstr = ast.StringLiteral(text)
        if len(exprs) == 1:
            se.evaluation = ast.BinaryOp("%", formatstr, exprs[0])
        else:
            se.evaluation = ast.BinaryOp("%", formatstr, TupleLiteral(exprs))
        se.evaluation.setOwner(se)
        self.visitNewItem(se.evaluation)
        se.evaluation.visit(self)
