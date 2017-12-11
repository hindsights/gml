package gml.go

func ScriptFunc.deepAnalyzeScript(visitor: Resolver, script: Script) {
    do assert false, "ScriptFunc.deepAnalyzeScript unimplemented", script
}

class GoPreVisitor: AstVisitor {
    func visit(node: AstNode) {
        //Log.debug("DeepAnalyzer.visit", node, node.getOwner())
        node.goPreVisit(this)
    }
    func AstNode.goPreVisit(visitor: GoPreVisitor) {
        visitChildren(visitor)
    }
    func CodeUnit.goPreVisit(visitor: GoPreVisitor) {
        // Log.debug("CodeUnit.goPreVisit", name)
        handler = GoUnitHandler(unit=this)
        visitChildren(visitor)
    }
    func LibUnit.goPreVisit(visitor: GoPreVisitor) {
        // Log.debug("LibUnit.goPreVisit", name)
        handler = GoUnitHandler(unit=this)
        visitChildren(visitor)
    }
}

class GoPreTransformer: AstTransformer
{
    func visit(node: AstNode) => AstNode {
        // Log.debug("PreTransformer.visit", node, node.getOwner())
        return node.goPretransform(this)
    }
    func AstNode.goPretransform(visitor: GoPreTransformer) => AstNode {
        visitChildren(visitor)
        return this
    }
    func FuncDef.goPretransform(visitor: GoPreTransformer) => Definition {
        return this
    }
    func SingleVarDef.goPretransform(visitor: GoPreTransformer) => SingleVarDef {
        var handler = getUnitHandler()
        // maybe the owner or context should be checked before filtering
        return do match handler {
            AstNode => nil
            GoLibUnitHandler => visitor.goPretransformSingleVarDef(this)
        }
    }
    func goPretransformSingleVarDef(v: SingleVarDef) => SingleVarDef {
        // filter unexported var declaration
        var vtype = v.type
        return do match vtype {
            AstNode => v
            UserType => v if (vtype.path.size() != 1 or vtype.path[0][0].isUpper()) else nil // check if vtype is an unexported internal type
        }
    }
    func MultipleVarDef.goPretransform(visitor: GoPreTransformer) => MultipleVarDef {
        var newVars: [SingleVarDef]
        for v in vars {
            var newvar = v.goPretransform(this)
            if newvar != nil {
                newVars.append(newvar)
            }
        }
        vars = newVars
        return this
    }
    func goPretransformDefs(defs: [Definition]) => [Definition] {
        var newDefs: [Definition]
        for def in defs {
            var newdef = def.goPretransform(this)
            if newdef != nil {
                newDefs.append(newdef)
            }
        }
        return newDefs
    }
    func CodeUnit.goPretransform(visitor: GoPreTransformer) => CodeUnit {
        return this
    }
    func LibUnit.goPretransform(visitor: GoPreTransformer) => LibUnit {
        // Log.debug("LibUnit.goPretransform", name, definitions.size())
        definitions = visitor.goPretransformDefs(definitions)
        // Log.debug("LibUnit.goPretransform end", name, definitions.size())
        return this
    }
    func ClassDef.goPretransform(visitor: GoPreTransformer) => ClassDef {
        // Log.debug("ClassDef.goPretransform", toString(), getOwner())
        definitions = visitor.goPretransformDefs(definitions)
        return this
    }
}

class DeepAnalyzer: AstVisitor {
    func visit(node: AstNode) {
        //Log.debug("DeepAnalyzer.visit", node, node.getOwner())
        node.deepAnalyze(this)
    }
    func AstNode.deepAnalyze(visitor: DeepAnalyzer) {
        visitChildren(visitor)
    }
    func Script.deepAnalyze(visitor: DeepAnalyzer) {
        //Log.debug("Script.deepAnalyze", caller, args, namedArgs, target)
        target.deepAnalyzeScript(visitor, this)
    }
    func Import.deepAnalyze(visitor: DeepAnalyzer) {
        // Log.debug("Import.deepAnalyze", toString(), target)
        target.addImportDep(this, visitor)
    }
    func AstNode.addImportDep(imp: Import, visitor: DeepAnalyzer) {
        var unit = imp.getCodeUnit()
        do match {
            case AstNode: unit.handler.addDep("/".join(imp.path[:-1]))
            case Package: unit.handler.addDep("/".join(imp.path))
        }
    }
    func AstNode.analyzeDependency(visitor: DeepAnalyzer, unit: CodeUnit) {
    }
    func Identifier.deepAnalyze(visitor: DeepAnalyzer) {
        if target != nil {
            target.analyzeDependency(visitor, getCodeUnit())
        }
    }
    func AttrRef.deepAnalyze(visitor: DeepAnalyzer) {
        // Log.debug("AttrRef.deepAnalyze", toString(), object.toString(), target, getCodeUnit().name)
        if target != nil {
            target.analyzeDependency(visitor, getCodeUnit())
        }
        visitChildren(visitor)
    }
    func CodeUnit.deepAnalyze(visitor: DeepAnalyzer) {
        // Log.debug("CodeUnit.deepAnalyze", name)
        // handler = GoUnitHandler(unit = this)
        visitChildren(visitor)
    }
    func LibUnit.deepAnalyze(visitor: DeepAnalyzer) {
        // Log.debug("LibUnit.deepAnalyze", name, definitions.size())
        visitChildren(visitor)
    }
    func ClassDef.deepAnalyze(visitor: DeepAnalyzer) {
        if isProtoType() {
            return
        }
        visitChildren(visitor)
        visitor.setClassStorage(this, "ref" if classType == ClassType.normal else "interface")
    }
    func FuncSpec.deepAnalyze(visitor: DeepAnalyzer) {
        visitChildren(visitor)
        params.each({visitor.analyzeType($0.type)})
        do assert returnType != nil, ("FuncSpec.deepAnalyze returnType", toString(), getOwner())
        visitor.analyzeType(returnType)
    }
    func analyzeType(node: AstNode) => void {
        // Log.debug("analyzeType", node, node.toString(), node.getOwner(), node.getCodeUnit())
        if node.getCodeUnit() != nil and node.getCodeUnit().language != "go" {
            return
        }
        do match node {
            case AstNode:
                // pass
            case UserType:
                var cls = node.target as ClassDef
                if cls != nil {
                    setClassStorage(cls, "value")
                }
            case PointerType:
                var ut = node.elementType as UserType
                if ut != nil {
                    var cls = ut.target as ClassDef
                    if cls != nil {
                        setClassStorage(cls, "ref")
                    }
                }
        }
    }
    func setClassStorage(cls: ClassDef, stgname: string) {
        // Log.debug("setClassStorage", cls.name, cls, stgname, cls.typeClass)
        var gotypeclass = cls.typeClass as UserTypeClass
        if gotypeclass.storage == nil {
            gotypeclass.storage = StorageFactory.instance().get(stgname)
        }
    }
    func analyzeReceiverStorage(node: AstNode) => string =
        do match node {
            AstNode => "value"
            PointerType => "ref"
        }
    func FuncProto.deepAnalyze(visitor: DeepAnalyzer) {
        // Log.debug("FuncProto.deepAnalyze", receiver, toString(), cls)
        if receiver != nil and getCodeUnit() != nil and getCodeUnit().language == "go" {
            var extdef = getOwner() as ExtensionDef
            // Log.debug("FuncProto.deepAnalyze receiver", extdef.name, receiver, toString(), cls, extdef.name, extdef.cls)
            var targetcls = extdef.cls as ClassDef
            if targetcls != nil {
                visitor.setClassStorage(targetcls, visitor.analyzeReceiverStorage(receiver))
                // Log.debug("FuncProto.deepAnalyze receiver target", targetcls.name, receiver, toString(), cls, extdef.name, extdef.cls, targetcls)
                // do assert false, ("FuncProto.deepAnalyze receiver", receiver, toString(), cls)
            }
        }
        visitChildren(visitor)
    }
}

class DeepTransformer: AstTransformer {
    func visit(node: AstNode) {
        // Log.debug("DeepTransformer.visit", node, node.getOwner())
        node.deepTransform(this)
    }
    func AstNode.deepTransform(visitor: DeepTransformer) => AstNode {
        visitChildren(visitor)
        return this
    }
    func CodeUnit.deepTransform(visitor: DeepTransformer) => CodeUnit {
        // Log.debug("CodeUnit.deepTransform", name, definitions.size())
        var defs = [def.deepTransform(visitor) as Definition for def in definitions]
        definitions = defs
        return this
    }
    func ClassDef.deepTransform(visitor: DeepTransformer) => ClassDef {
        // Log.debug("ClassDef.deepTransform", definitions.size())
        if isProtoType() {
            return this
        }
        var defs = [def.deepTransform(visitor) as Definition for def in definitions]
        definitions = defs
        return this
    }
    func StatementBody.deepTransform(visitor: DeepTransformer) => StatementBody {
        // Log.debug("StatementBody.deepTransform", statements.size())
        var newStatements: [Statement]
        for stmt in statements {
            var ctx = visitor.pushStatementContext(stmt)
            var newstmt = stmt.deepTransform(visitor)
            newStatements.extend(ctx.statements)
            if newstmt != nil {
                newStatements.append(newstmt)
            }
            visitor.popStatementContext()
        }
        statements = newStatements
        return this
    }
    func Statement.deepTransform(visitor: DeepTransformer) => Statement {
        visitChildren(visitor)
        return this
    }
    func CallStatement.deepTransform(visitor: DeepTransformer) => Statement {
        // Log.debug("CallStatement.deepTransform", toString(), call.caller.toString())
        var newcall = call.deepTransform(visitor)
        if newcall != call {
            call = newcall
        }
        return this
    }
    func Call.deepTransform(visitor: DeepTransformer) => Expression {
        // Log.debug("Call.deepTransform", toString(), caller.toString())
        return caller.deepTransformCall(visitor, this)
    }
    func Return.deepTransform(visitor: DeepTransformer) => Statement {
        // Log.debug("Return.deepTransform", toString())
        if value != nil {
            var newval = value.deepTransform(visitor)
            if newval != value {
                value = newval
            }
        }
        return this
    }
    func SingleVarDef.deepTransform(visitor: DeepTransformer) => Definition {
        // Log.debug("SingleVarDef.deepTransform", toString())
        if initial != nil {
            var newval = initial.deepTransform(visitor)
            if newval != initial {
                initial = newval
            }
        }
        return this
    }

    func AstNode.deepTransformCall(visitor: DeepTransformer, call: Call) => Expression {
        return call
    }
    func AstNode.deepTransformAttrCall(visitor: DeepTransformer, call: Call, attr: AttrRef) => Expression {
        return call
    }
    func AttrRef.deepTransformCall(visitor: DeepTransformer, call: Call) => Expression {
        // Log.debug("AttrRef.deepTransformCall", toString(), call.caller.toString(), target)
        do assert target != nil, ("AttrRef.deepTransformCall", toString(), call.caller.toString(), target)
        return target.deepTransformAttrCall(visitor, call, this)
    }
}
