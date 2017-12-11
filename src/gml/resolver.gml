package gml

class OwnerInitializer: AstVisitor {
    func visit(node: AstNode) {
        // Log.debug("OwnerInitializer.visit", node)
        node.initializeOwner()
    }
}

class Preprocessor: AstVisitor {
    func visit(node: AstNode) {
        // Log.debug("Preprocessor.visit", node)
        node.preprocess(this)
    }
    func AstNode.preprocess(visitor: Preprocessor) {
        // Log.debug("AstNode.preprocess", toString(), visitor)
        visitChildren(visitor)
    }
    func CodeUnit.preprocess(visitor: OwnerInitializer) {
        // Log.debug("CodeUnit.preprocess", name, definitions.size(), definitions)
        visitChildren(visitor)
    }
    func AstNode.replaceDefinition(def: Definition, newdef: Definition) {
        do match {
            case AstNode:
                do assert false, "AstNode.removeDefinition", toString(), def.toString(), newdef.toString()
            case CodeUnit:
                // Log.debug("CodeUnit.replaceDefinition", def, newdef, definitions.size())
                definitions.remove(def)
                definitions.append(newdef)
            case LibUnit:
                // Log.debug("LibUnit.replaceDefinition", def, newdef, definitions.size())
                definitions.remove(def)
                definitions.append(newdef)
            case ClassDef:
                // Log.debug("ClassDef.replaceDefinition", def, newdef, definitions.size())
                definitions.remove(def)
                definitions.append(newdef)
        }
    }
    func getReceiverTypeName(node: AstNode) => string =
        do match node {
            AstNode => "getReceiverTypeName:%s" % node.toString()
            UserType => node.fullpath
            PointerType => getReceiverTypeName(node.elementType)
        }
    func FuncDef.preprocess(visitor: Preprocessor) {
        if receiver != nil and not injected {
            injected = true
            var extdef = ExtensionDef(name=visitor.getReceiverTypeName(receiver), definitions=[this])
            getOwner().replaceDefinition(this, extdef)
            // Log.debug("FuncDef.preprocess add to extension", toString(), receiver, getOwner())
            visitor.setupNewItem(extdef, getOwner(), true)
            return
        }
        visitChildren(visitor)
    }
    func FuncProto.preprocess(visitor: Preprocessor) {
        if receiver != nil and not injected {
            injected = true
            var extdef = ExtensionDef(name=visitor.getReceiverTypeName(receiver), definitions=[this])
            getOwner().replaceDefinition(this, extdef)
            // Log.debug("FuncProto.preprocess extension", toString(), receiver, getOwner())
            visitor.setupNewItem(extdef, getOwner(), true)
            return
        }
        visitChildren(visitor)
    }
}

class NameCacher: AstVisitor {
    func visit(node: AstNode) {
        // Log.debug("NameCacher.visit", node)
        node.cacheName(this)
    }

    func AstNode.cacheName(visitor: NameCacher) {
        //Log.debug("AstNode.cacheName", toString())
        visitChildren(visitor)
    }
    func FuncSpec.cacheName(visitor: NameCacher) {
        // Log.debug("FuncSpec.cacheName", toString(), getOwner())
        if returnType == nil {
            returnType = createVoidType()
            visitor.setupNewItem(returnType, this, false)
        }
        visitChildren(visitor)
    }
    func FuncDef.cacheName(visitor: NameCacher) {
        var owner = getOwner()
        var context = owner.getFullContext()
        //do assert context.node == owner, ("FuncDef.cacheName", owner, context) 
        // Log.debug("FuncDef.cacheName", toString(), owner)
        var ownercls = getClassDef()
        if owner == ownercls {
            cls = ownercls
            if name == ownercls.name {
                ownercls.constructors.append(this)
                info.type = FuncType.constructor
                // ? default constructor may be unnecessary
                Log.debug("FuncDef.cacheName add constructor", this, spec, spec.returnType, ownercls, info.type, FuncType.constructor, FuncType.normal)
            } elseif name == "~" + ownercls.name {
                //Log.debug("FuncDef.cacheName destructor", this, ownercls, ownercls.destructor)
                ownercls.destructor = this
                info.type = FuncType.constructor
            } else {
                info.type = FuncType.normal
            }
        } else {
            info.type = FuncType.normal
        }
        if info.type == FuncType.normal {
            // Log.debug("FuncDef.cacheName add normal func symbol", this, name, ownercls)
            owner.addSymbol(name, this)
        }
        context.functions.append(this)
        visitChildren(visitor)
        var unit = getCodeUnit()
        if owner == unit {
            if name == "runMain" {
                Log.debug("FuncDef.cacheName has main", name, unit)
                unit.hasMain = true
            }
            if info.type == FuncType.normal {
                //unit.pkg.addSymbol(name, this)
            }
        }
    }
    func FuncProto.cacheName(visitor: NameCacher) {
        var owner = getOwner()
        var context = owner.getFullContext()
        //do assert context.node == owner, ("FuncProto.cacheName", owner, context) 
        // Log.debug("FuncProto.cacheName", toString(), owner)
        var ownercls = getClassDef()
        if owner == ownercls {
            cls = ownercls
            info.type = FuncType.normal
        } else {
            info.type = FuncType.normal
        }
        if info.type == FuncType.normal {
            // Log.debug("FuncProto.cacheName add normal func symbol", this, name, owner, ownercls)
            owner.addSymbol(name, this)
        }
        if context != nil {
            context.functions.append(this)
        }
        visitChildren(visitor)
    }
    func SingleVarDef.cacheName(visitor: NameCacher) {
        var owner = getOwner()
        var ownercls = getClassDef()
        // Log.debug("SingleVarDef.cacheName start", name, toString(), owner, ownercls)
        if owner == ownercls {
            cls = ownercls
        }
        var context = owner.getFullContext()
        //assert context == owner, ("SingleVarDef.cacheName", owner, context) 
        // Log.debug("SingleVarDef.cacheName", toString(), owner, context)
        owner.addSymbol(name, this)
        if context != nil and context.node == owner {
            context.vars.append(this)
        }
        visitChildren(visitor)
    }
    func TypeDef.cacheName(visitor: NameCacher) {
        var owner = getOwner()
        var context = owner.getFullContext()
        //assert context == owner, ("SingleVarDef.cacheName", owner, context) 
        // Log.debug("TypeDef.cacheName", toString(), owner, context)
        owner.addSymbol(name, this)
        visitChildren(visitor)
    }
    func ClassDef.cacheName(visitor: NameCacher) {
        var owner = getOwner()
        if isProtoType() {
            owner.addSymbol(name, this)
            return
        }
        if not isGenericInstantiation() {
            owner.addSymbol(name, this)
        }
        // Log.debug("ClassDef.cacheName start", toString(), owner, owner, owner.getContext())
        var context = owner.getFullContext()
        Log.debug("ClassDef.cacheName", name, toString(), owner)
        if context {
            do assert context, ("ClassDef.cacheName context is nil", this, owner)
            do assert context.node == owner, ("ClassDef.cacheName", this, owner, context, context.node)
            context.classes.append(this)
        }
        //Log.debug("ClassDef.cacheName create type class", toString())
        if typeClass == nil {
            typeClass = visitor.project.targetModule.createTypeClass(this)
        }
        visitChildren(visitor)
        if constructors.empty() and classType == ClassType.normal {
            //Log.debug("ClassDef.cacheName add default constructor", name, this)
            var body = StatementBody(statements=[])
            var spec = FuncSpec(params=[], returnType=UserType(path=[name], fullpath=name))
            var f = FuncDef(name=name, spec=spec, body=body)
            definitions.append(f)
            visitor.setupNewItem(f, this, true)
            //Log.debug("ClassDef.cacheName add default constructor is", name, this, constructors[0].spec.returnType)
        }
        var unit = getCodeUnit()
        if owner == unit {
            Log.debug("ClassDef.cacheName add into package", name, this, unit.pkg.fullpath)
            //unit.pkg.addSymbol(name, this)
        }
    }
    func CodeUnit.cacheName(visitor: NameCacher) {
        var owner = getOwner()
        Log.debug("CodeUnit.cacheName", name, owner, pkg, definitions.size())
        do assert owner, ("CodeUnit.cacheName", toString(), visitor, name)
        var imports: [Import]
        for imp in this.imports {
            imports.extend(imp.unfold())
        }
        //Log.debug("CodeUnit.cacheName imports", this.imports.size(), imports.size())
        this.imports = imports
    	visitChildren(visitor)
    }
    func Param.cacheName(visitor: NameCacher) {
        // Log.debug("Param.cacheName", toString(), getOwner())
        if name != "" {
            getOwner().addSymbol(name, this)
        }
        visitChildren(visitor)
    }
}

func foo() {
}

class Resolver: AstVisitor {
    var level: int
    func visit(node: AstNode) {
        // Log.error("Resolver.visit", node, node.getOwner())
        return node.resolve(this)
    }
    func AstNode.resolve(visitor: Resolver) {
        visitChildren(visitor)
    }
    func CodeUnit.resolve(visitor: Resolver) {
        visitChildren(visitor)
    }
    func Script.resolve(visitor: Resolver) {
        Log.debug("Script.resolve", caller, args, namedArgs)
        if target == nil {
            target = visitor.project.findScript(caller.path)
            do assert target, "Script.resolve no target", caller.path
            target.resolveScript(visitor, this)
        }
    }
    func Import.resolve(visitor: Resolver) {
        if target != nil {
            return
        }
        var owner = getOwner()
        var unit = getCodeUnit()
        do assert owner, ("Import.resolve owner", toString())
        Log.debug("Import.resolve", fullpath, toString(), owner)
        do assert names.empty(), ("Import.resolve empty names", fullpath, names)
        var node = owner.resolveSymbol(path)
        if node == nil {
            node = visitor.project.rootPackage.resolveSymbol(path)
        }
        do assert node, ("Import.resolve", fullpath, toString(), owner, unit.name)
        Log.debug("Import.resolve ok", fullpath, toString(), owner, node, unit.name, visitor.level)
        target = node
        unit.addSymbol(path[-1], node)
    }
    func FuncDef.resolve(visitor: Resolver) {
        var extdef = getOwner() as ExtensionDef
        if extdef != nil {
            cls = extdef.cls
            cls.addSymbol(name, this)
        }
        visitChildren(visitor)
    }
    func ExtensionDef.resolve(visitor: Resolver) {
        // Log.debug("ExtensionDef.resolve", name, this, visitor)
        if cls == nil {
            cls = getOwner().findSymbol(name)
            do assert cls != nil, "ExtensionDef.resolve class not found", name
            visitChildren(visitor)
        }
        // Log.debug("ExtensionDef.resolve", name, toString(), cls)
    }
    func BuiltinType.resolve(visitor: Resolver) {
        // Log.debug("BuiltinType.resolve", toString())
        if typeClass == nil {
            typeClass = visitor.project.targetModule.createTypeClass(this)
        }
        do assert typeClass, ("BuiltinType.resolve", toString())
        visitChildren(visitor)
    }
    func AstNode.resolveUserType(visitor: AstVisitor, path: [string]) => AstNode {
        do match {
            case AstNode:
                var owner = getOwner()
                // Log.debug("AstNode.resolveUserType", toString(), path, owner)
                if owner == nil {
                    do assert "AstNode.resolveUserType", path, toString()
                    return nil
                }
                return owner.resolveUserType(visitor, path)
            case CodeUnit:
                // Log.debug("CodeUnit.resolveUserType", toString(), path, handler)
                if handler == nil {
                    do assert false, "CodeUnit.resolveUserType", toString(), path, handler
                    return nil
                }
                return handler.resolveUserType(visitor, path)
            case LibUnit:
                // Log.debug("LibUnit.resolveUserType", toString(), path, handler)
                if handler == nil {
                    do assert false, "LibUnit.resolveUserType", toString(), path, handler
                    return nil
                }
                return handler.resolveUserType(visitor, path)
        }
    }
    func UserType.resolve(visitor: Resolver) {
        // Log.debug("UserType.resolve start", fullpath, this, genericInstance, target, target.getTypeClass() if target else nil, getOwner(), getOwner().getOwner(), getFuncDef(), getClassDef(), getCodeUnit(), getUnit())
        visitChildren(visitor)
        if target == nil {
            target = resolveTypeSymbol(path)
            // Log.debug("UserType.resolve target", fullpath, this, genericArgs, target, getOwner(), getOwner().getOwner(), getFuncDef(), getClassDef(), getCodeUnit())
            // Log.debug("UserType.resolve target type", fullpath, this, target, target.getTypeClass() if target else nil, getOwner(), getFuncDef(), getClassDef(), getCodeUnit())
            if target != nil and genericArgs.size() > 0 {
                var inst, newInst = target.instantiate(genericArgs, visitor)
                target = inst
                if newInst {
                    genericInstance = inst
                    // Log.debug("UserType.resolve instantiate", fullpath, this, target, getOwner(), genericArgs, inst)
                    visitor.setupNewItem(genericInstance, this, true)
                    // Log.debug("UserType.resolve instantiate", fullpath, this, target, getOwner(), genericArgs, inst)
                }
                do assert target, ("UserType.resolve", toString(), getOwner(), getFuncDef(), getCodeUnit())
            } elseif target == nil {
                // Log.debug("UserType.resolve try in code unit", this, fullpath, target)
                target = resolveUserType(visitor, path)
                // Log.debug("UserType.resolve in code unit", this, fullpath, target)
            }
            // Log.debug("UserType.resolve target", this, fullpath, target)
            do assert target or visitor.level == 1 or (getCodeUnit() != nil and getCodeUnit().language != "gml"), ("UserType.resolve", toString(), getOwner(), getFuncDef(), getCodeUnit())
        }
        // Log.debug("UserType.resolve start end", fullpath, this, genericInstance, target, target.getTypeClass() if target else nil, getOwner(), getOwner().getOwner(), getFuncDef(), getClassDef(), getCodeUnit(), getUnit())
    }
    func BinaryOp.resolve(visitor: Resolver) {
        if handler == nil {
            handler = visitor.targetModule.getBinaryOpHandler(op)
        }
        visitChildren(visitor)
    }
    func TupleVarDef.resolve(visitor: Resolver) {
        // Log.debug("TupleVarDef.resolve", toString(), vars[0].name, type, initial)
        if type == nil {
            do assert initial != nil, "TupleVarDef.resolve nil initial", vars[0].name
            initial.resolve(visitor)
            type = initial.getType()
            // Log.debug("TupleVarDef.resolve initial", toString(), vars[0].name, type, initial)
        }
        if type != nil and vars[0].type == nil {
            type.getTypeClass().resolveTupleVar(this, visitor)
        }
        if type != nil {
            type.resolve(visitor)
            vars.size().times({vars[$0].resolve(visitor)})
        }
    }
    func SingleVarDef.resolve(visitor: Resolver) {
        // Log.debug("SingleVarDef.resolve", toString())
        var extdef = getOwner() as ExtensionDef
        if extdef != nil {
            cls = extdef.cls
            cls.addSymbol(name, this)
        }
        var unit = getCodeUnit()
        if type != nil {
            // Log.debug("SingleVarDef.resolve type", toString(), type, type.toString(), getOwner())
            type.resolve(visitor)
        }
        if initial != nil {
            if unit != nil and unit.language == "gml" {
                // Log.debug("SingleVarDef.resolve initial resolve", toString(), initial, initial.getType(), getOwner())
                initial.resolve(visitor)
            }
            if type == nil {
                // Log.debug("SingleVarDef.resolve initial prepare type", toString(), initial, initial.getType(), getOwner())
                type = initial.getType()
                if type != nil {
                    // Log.debug("SingleVarDef.resolve resolve initial type", toString(), type, getOwner())
                    type.resolve(visitor)
                }
                // Log.debug("SingleVarDef.resolve initial prepare type result", toString(), type, getOwner())
            }
        }
    }
    func Identifier.resolve(visitor: Resolver) {
        // Log.debug("Identifier.resolve", toString(), target, getType(), getTypeClass(), getOwner(), getCodeUnit())
        if target == nil {
            target = findSymbol(name)
            do assert target or visitor.level == 1 or (getCodeUnit() != nil and getCodeUnit().language != "gml"), ("Identifier.resolve no target", visitor.level, toString(), target, getOwner(), getFuncDef(), getCodeUnit())
            if target {
                target.resolveType(visitor)
            }
        } else {
            if target.getTypeClass() == nil {
                target.resolveType(visitor)
            }
        }
        // Log.debug("Identifier.resolve ok", toString(), getType(), getTypeClass(), target, getFuncDef(), getOwner(), target.getOwner())
        do assert target or visitor.level == 1 or (getCodeUnit() != nil and getCodeUnit().language != "gml"), ("Identifier.resolve", toString(), target, getOwner())
        if target as UserType {
            do assert visitor.level == 1 or target.getTypeClass(), ("Identifier.resolve type class", toString(), target)
        }
        //do assert false, ("Identifier.resolve", toString(), target)
    }
    func AttrRef.resolve(visitor: Resolver) {
        // Log.debug("AttrRef.resolve", toString(), target)
        object.resolve(visitor)
        // Log.debug("AttrRef.resolve object", toString(), target, object, object.getType(), object.getTypeClass(), visitor.level)
        if target == nil {
            target = object.resolveAttr(this)
            // Log.debug("AttrRef.resolve ok", toString(), target, object, visitor.level)
            do assert target or visitor.level == 1, ("AttrRef.resolve", toString(), ref, object, target, getFuncDef(), getCodeUnit())
        }
        //do assert false, ("AttrRef.resolve", toString(), target)
    }
    func AstNode.resolveAttr(attr: AttrRef) => AstNode {
        // Log.debug("AstNode.resolveAttr", toString(), attr, attr.toString(), attr.ref, attr.object, getType(), getTypeClass())
        return do match {
            AstNode => getTypeClass().resolveAttr(attr) if getTypeClass() else nil
            Identifier => target.resolveAttr(attr) if target else nil
            SingleVarDef => type.resolveAttr(attr) if type else nil
            UserType => target.resolveAttr(attr) if target else nil
            TypeDef => target.resolveAttr(attr)
            PointerType => elementType.resolveAttr(attr)
            ClassDef => findLocalSymbol(attr.ref)
            Package => findLocalSymbol(attr.ref)
        }
    }
    func AstNode.resolveType(visitor: Resolver) {
        do match {
            case AstNode:
                foo()
            case Param:
                type.visit(visitor)
                // Log.debug("Param.resolveType", this, type.getTypeClass())
        }
    }
    func Call.resolve(visitor: Resolver) {
        caller.visit(visitor)
        var spec = caller.getSpec()
        // Log.debug("Call.resolve set arg type", caller.toString(), args, namedArgs, spec, spec.returnType if spec != nil else nil)
        if spec != nil and spec.params.size() == args.size() {
            //args.size().times({args[$0].expectedType = spec.params[$0].type})
            args.size().times({
                // Log.debug("Call.resolve set arg expected type", args[$0], spec.params[$0], spec.params[$0].type)
                args[$0].expectedType = spec.params[$0].type
                })
        }
        // Log.debug("Call.resolve set arg type stage 1", args, spec, caller)
        args.each({$0.visit(visitor)})
        // Log.debug("Call.resolve set arg type stage 2", args, spec, caller)
        namedArgs.each({$0.visit(visitor)})
        // Log.debug("Call.resolve set arg type stage 3", args, spec, caller)
    }
    func getOwnerClosure(node: AstNode) => Closure =
        do match node {
            AstNode => getOwnerClosure(node.getOwner()) if node.getOwner() != nil else nil
            Closure => node
        }
    func ArgumentPlaceholder.resolve(visitor: Resolver) {
        visitChildren(visitor)
        var closure = visitor.getOwnerClosure(this)
        var spec = closure.getSpec() if closure else nil
        // Log.debug("ArgumentPlaceholder.resolve closure", visitor.level, getFuncDef(), getType(), expectedType, closure, closure.spec if closure else nil, closure.expectedType if closure else nil, spec.toString() if spec else nil, getOwner(), getFuncDef(), getClassDef(), getCodeUnit())
        do assert spec or visitor.level == 1, "ArgumentPlaceholder.resolve spec", visitor.level, getFuncDef(), closure, spec
        // do assert closure.spec.params, "ArgumentPlaceholder.resolve spec.params", visitor.level, getFuncDef(), closure, closure.spec, closure.spec.params
        do assert closure != nil, "ArgumentPlaceholder.resolve closure", toString(), closure
        if spec != nil {
            // Log.debug("ArgumentPlaceholder.resolve closure spec", visitor.level, getFuncDef(), getType(), expectedType, closure, spec, getOwner(), getFuncDef(), getClassDef(), getCodeUnit())
            do assert sequence >= 0 and sequence < spec.params.size(), "ArgumentPlaceholder.resolve param", toString(), spec.params
            targetParam = spec.params[sequence]
            if closure.args.size() > 0 and targetArg == nil and false {
                do assert sequence >= 0 and sequence < closure.args.size(), "ArgumentPlaceholder.resolve arg", toString(), spec.params, sequence, closure.args
                var arg = closure.args[sequence].clone() as Identifier
                targetArg = arg
                // Log.debug("ArgumentPlaceholder.resolve targetArg", sequence, targetParam, targetParam.name, targetParam.getType(), toString(), closure, targetArg, arg.getType(), arg.target)
            }
            // Log.debug("ArgumentPlaceholder.resolve param", sequence, target, target.name, target.type, toString(), closure)
        }
    }
}
