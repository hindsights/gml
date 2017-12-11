package gml

import sys.StructuredWriter

@name
@logger
class AstVisitor {
    var project: Project
    var targetModule: LangModule
    func visit(node: AstNode) {
        node.visitChildren(this)
    }
    func toString = "AstVisitor:%s:0x%08x" % (getClassName(), this)
    func setupNewItem(item: AstNode, owneritem: AstNode, useCurrentVisitor: bool) {
        project.setupNewItem(item, owneritem, this if useCurrentVisitor else nil)
    }
}

class TransformerStatementContext {
    var currentStatement: Statement
    var statements: [Statement]
}

class TransformerDefinitionContext {
    var currentDefinition: Definition
    var definitions: [Definition]
}

class AstTransformer: AstVisitor {
    var statementContexts: [TransformerStatementContext]
    var definitionContexts: [TransformerDefinitionContext]

    func pushStatementContext(stmt: Statement) => TransformerStatementContext {
        var ctx = TransformerStatementContext(currentStatement=stmt)
        statementContexts.insert(0, ctx)
        return ctx
    }
    func popStatementContext() {
        statementContexts.removeAt(0)
    }
    func getStatementContext(index: int) => TransformerStatementContext {
        return statementContexts[index]
    }
    func getCurrentStatementContext() => TransformerStatementContext {
        return getStatementContext(0)
    }

    func pushDefinitionContext(def: Definition) => TransformerDefinitionContext {
        var ctx = TransformerDefinitionContext(currentDefinition=def)
        definitionContexts.insert(0, ctx)
        return ctx
    }
    func popDefinitionContext() {
        definitionContexts.removeAt(0)
    }
    func getDefinitionContext(index: int) => TransformerDefinitionContext {
        return definitionContexts[index]
    }
    func getCurrentDefinitionContext() => TransformerDefinitionContext {
        return getDefinitionContext(0)
    }
}

@name
@tree
class AstNode {
    func addSymbol(name: string, node: AstNode) {
        // println("AstNode.addSymbol", name, toString(), node)
        do assert false, "AstNode.addSymbol failed"
    }
    func findMember(name: string) => AstNode {
        // println("AstNode.findMember", name, toString())
        do assert false, "AstNode.findMember failed", name, toString()
        return nil
    }
    func findLocalSymbol(name: string) => AstNode {
        // println("AstNode.findLocalSymbol", name, toString())
        do assert false, "AstNode.findLocalSymbol failed", name, toString()
        return nil
    }
    func clone() => AstNode {
        do assert false, "AstNode.clone failed"
        return nil
    }
    func dump(writer: StructuredWriter) {
    }
    func dumpCode(writer: StructuredWriter, depth: int) {
    }
    func resolveSymbol(path: [string]) => AstNode {
        return nil
    }
    func resolveTypeSymbol(path: [string]) => AstNode {
        return nil
    }
    func resolveTypeSymbols(path: [string]) => AstNode {
        return nil
    }
    func findSymbol(name: string) => AstNode {
        // println("AstNode.findChild", name, toString(), owner_)
        do assert false, "AstNode.findSymbol failed"
        return nil
    }
    func getOwner() => AstNode {
        // println("AstNode.getOwner", toString())
        do assert false, "AstNode.getOwner failed"
        return nil
    }
    func setOwner(owner: AstNode) {
        // println("AstNode.setOwner", toString(), owner)
        do assert false, "AstNode.setOwner failed"
    }
    func formatId() => string = "0x%08x" % this

    func visit(visitor: AstVisitor) {
        // println("AstNode.visit", toString(), owner if owner else "owner(nil)", visitor)
        // visitor.visit(this)
        visitor.visit(this)
    }

    func visitChildren(visitor: AstVisitor) {
        // println("AstNode.visitChildren", toString(), owner if owner else "owner(nil)")
    }
    func toString() => string {
        return "%s:0x%08x" % (getClassName(), this)
    }
    func initializeOwner() {
        // do assert false, "AstNode.initializeOwner", toString()
        // println("AstNode.initializeOwner", toString())
    }
    func getContext() => AstSimpleContext {
        return nil
    }
}

@mixin(AstSimpleContext, context, getContext, node=this)
class SimpleNode: AstNode {
    case Param(name: string, type: AstNode)
    case IfBranch(condition: Expression, body: StatementBody)
    @mixin(AstBlockContext, context, getContext, node=this)
    case StatementBody(statements: [Statement])

    case IdPath(path: [string], fullpath: string)
    case Script(caller: IdPath, args: [Expression], namedArgs: [NamedExpressionItem]) {
        var target: ScriptFunc
    }
    case NamedTypeItem(name: string, type: AstNode)
    case NamedExpressionItem(name: string, value: Expression)
    case DictItem(key: Expression, value: Expression)
    case ListComprehensionFor(variable: VarDef, source: Expression, condition: Expression)
    @mixin(AstBlockContext, context, getContext, node=this)
    case CaseEntryStmt(pattern: Expression, body: StatementBody)
    case CaseEntryExpr(pattern: Expression, expr: Expression)
    @mixin(AstBlockContext, context, getContext, node=this)
    case CaseEntry(value: Expression, body: StatementBody)

}

class GenericParam: SimpleNode {
    case GenericTypeParam(name: string)
    case GenericLiteralParam(type: Type)
    case GenericVariadicTypeParam(name: string)
}

class GenericArg: SimpleNode {
    func register(owner: AstNode, param: GenericParam) {
    }
    case GenericTypeArg(type: Type) {
        func toString() = "GenericTypeArg(type=%s,%s,id=0x%08x)" % (type.toString(), type, this)
        func register(owner: AstNode, param: GenericTypeParam) {
            // do assert false, "GenericTypeArg.reigster", toString(), owner, param
            owner.addSymbol(param.name, this)
        }
    }
    case GenericLiteralArg(literal: Literal) {
        func register(owner: AstNode, param: GenericLiteralParam) {
            do assert false, "GenericLiteralArg.reigster", toString(), owner, param
        }
    }
    case GenericVariadicTypeArg(types: [Type]) {
        func toString() = "GenericVariadicTypeArg(%s,id=0x%08x)" % (types, this)
        func register(owner: AstNode, param: GenericVariadicTypeParam) {
            // do assert false, "GenericVariadicTypeArg.reigster", toString(), owner, param
            owner.addSymbol(param.name, this)
        }
    }
}

class TypeClass: SimpleNode {
    func init() {
    }
    func createDefaultValue() => Expression {
        do assert false, "TypeClass.createDefaultValue", toString()
        return nil
    }
    func resolveTupleVar(v: TupleVarDef, visitor: AstVisitor) {
        do assert false, "resolveTupleVar", v, visitor, this
    }
}

class Type: SimpleNode {
    case UserType(path: [string], fullpath: string, genericArgs: [GenericArg], genericInstance: AstNode) {
        var target: AstNode
    }
}

enum FuncType {
    normal,
    constructor,
    destructor
}

enum ClassType {
    normal,
    interface,
    trait
}

class FuncModifiers {
    var isStatic: bool = false
}

class FuncInfo {
    var type: FuncType = FuncType.normal
    var modifiers: FuncModifiers = FuncModifiers()
}

class BuiltinType: Type {
    var typeClass: TypeClass
    case PointerType(elementType: Type)
    case FuncSpec(params: [Param], returnType: Type)
}

class Expression: SimpleNode
{
    var type: Type
    var expectedType: Type

    case Identifier(name: string) {
        var target: AstNode
    }
    case UnaryOp(op: string, operand: Expression) {
        var handler: UnaryOpHandler
    }
    case BinaryOp(op: string, left: Expression, right: Expression) {
        var handler: BinaryOpHandler
    }
    case AttrRef(object: Expression, ref: string) {
        var target: AstNode
    }
    case Subscript(collection: Expression, key: Expression)
    case Slicing(collection: Expression, start: Expression, stop: Expression, step: Expression)
    case Call(caller: Expression, args: [Expression], namedArgs: [NamedExpressionItem])
    case This
    case EmbeddedCode(code: StringEvaluation)
    case StringEvaluation(literal: StringLiteral, evaluation: BinaryOp)
    case EmbeddedStatement(statement: Statement) {
        func visitChildren(visitor: AstVisitor) {}
    }
    case EmbeddedExpr(expression: Expression) {
        func visitChildren(visitor: AstVisitor) {}
    }
    case ExprEvaluation(expression: Expression)
    case Closure(spec: FuncSpec, body: StatementBody) {
        var args: [Identifier]
    }
    case ArgumentPlaceholder(sequence: int) {
        var targetParam: Param
        var targetArg: AstNode
    }
    @mixin(AstBlockContext, context, getContext, node=this)
    case ListComprehension(expr: Expression, fors: [ListComprehensionFor])
    case TypeCast(source: Expression, type: Type)
    case IfElseExpr(condition: Expression, truePart: Expression, falsePart: Expression)
    case CaseBlock(entries: [AstNode])
}

class BinaryOpHandler {
    func getType(expr: BinaryOp) => AstNode = nil
}

class UnaryOpHandler {
    func getType(expr: UnaryOp) => AstNode = nil
}

class Literal: Expression
{
    var type: AstNode
    // case PrimitiveLiteral(name: string, typeName: string)
    case IntLiteral(text: string, value: long)
    case FloatLiteral(text: string, value: double)
    case CharLiteral(text: string, value: char)
    case StringLiteral(text: string, value: string)
    case BoolLiteral(text: string, value: bool)
    case Nil
    case ListLiteral(values: [Expression])
    case TupleLiteral(values: [Expression])
    case DictLiteral(values: [DictItem])
    case SetLiteral(values: [Expression])
}

class Statement: SimpleNode
{
    case CallStatement(call: Call)
    case Return(value: Expression)
    case Assignment(targets: [Expression], values: [Expression], op: string)
    case Break
    case Continue
}

@mixin(AstBlockContext, context, getContext, node=this)
class CompoundStatement: Statement
{
    case StatementBlock(body: StatementBody)
    case SwitchCaseStatement(entries: [CaseEntry])
    case IfStatement(branches: [IfBranch], elseBranch: StatementBlock)
    case ForStatement(init: Statement, condition: Expression, step: Statement, body: StatementBody)
    case ForEachStatement(item: VarDef, collection: Expression, body: StatementBody)
    case ForEachDictStatement(key: VarDef, val: VarDef, collection: Expression, body: StatementBody)
    case UsingStatement(variable: VarDef, body: StatementBody)
}

class GenericClassInstantiator {
	var classes: [AstNode]

    func find(args: [GenericArg]) => AstNode {
        // println("GenericClassInstantiator.find start", args, classes)
        classes.each({
            var cls = $0
            do assert cls, "GenericClassInstantiator.find", args, cls
            // println("GenericClassInstantiator.find", args, cls)
            if checkGenericArgsMatch(cls.getGenericArgs(), args) {
                return cls
            }
        })
        // println("GenericClassInstantiator.find failed", args)
        // return nil
    }
    func cache(cls: AstNode) {
        classes.append(cls)
    }
    // func visit(visitor: AstVisitor) {
    //     // classes.each({$0.visit(visitor)})
    // }
}

class GenericClassInstantiation: SimpleNode {
    var params: [GenericParam]
    var args: [GenericArg]
	// var namedArgs: {string: GenericArg}
    func registerTypes(owner: AstNode) {
        // println("GenericClassInstantiation.register", args, params)
        do assert args.size() == params.size(), ("GenericClassInstantiation.register", args, params)
        args.each({
            $0.register(owner, params[$1])
        })
    }
}

class ClassHandler {
}

class Definition: Statement
{
    @mixin(AstSimpleContext, context, getContext, node=this)
    case ConstSpec(name: string, type: AstNode, initial: Expression)

    @mixin(AstBlockContext, context, getContext, node=this)
    case EnumDef(name: string, items: [NamedExpressionItem])

    @mixin(AstSimpleContext, context, getContext, node=this)
    case TypeDef(name: string, target: Type)

    @mixin(AstFullContext, context, getContext, node=this)
    case ClassDef(name: string, genericParams: [GenericParam], bases: [UserType], definitions: [Definition], classType: ClassType) {
        var instantiator: GenericClassInstantiator
        var instantiation: GenericClassInstantiation
        var constructors: [FuncDef]
        var destructor: FuncDef
        var handler: ClassHandler
        var typeClass: TypeClass
    }

    case CaseClassDef(name: string, definitions: [Definition])

    @mixin(AstBlockContext, context, getContext, node=this)
    case FuncDef(name: string, spec: FuncSpec, body: StatementBody, receiver: Type) {
        var cls: ClassDef
        var info: FuncInfo = FuncInfo()
        var injected = false
    }

    @mixin(AstBlockContext, context, getContext, node=this)
    case FuncProto(name: string, spec: FuncSpec, receiver: Type) {
        var cls: ClassDef
        var info: FuncInfo = FuncInfo()
        var injected = false
    }

    @mixin(AstBlockContext, context, getContext, node=this)
    case ExtensionDef(name: string, definitions: [Definition]) {
        var cls: ClassDef
        func findLocalSymbol(symbolname: string) => AstNode {
            // println("ExtensionDef.findLocalSymbol", symbolname, name, cls)
            var symbol = cls.findLocalSymbol(symbolname) if cls != nil else nil
            if symbol != nil {
                // println("AstBlockContext.findLocalSymbol found in class:", symbolname, toString(), symbol.toString())
                return symbol
            }
            return getContext().findLocalSymbol(symbolname)
        }
    }
}

class VarDef: Definition {
    case SingleVarDef(name: string, type: AstNode, initial: Expression) {
        var cls: ClassDef
    }
    case MultipleVarDef(vars: [SingleVarDef])
    case TupleVarDef(vars: [SingleVarDef], type: AstNode, initial: Expression)
}

@mixin(AstBlockContext, context, getContext, node=this)
class GoPackageInfo(fullpath: string, path: [string], declarations: [AstNode]): SimpleNode {
}

extension ClassDef {
    func isProtoType() => bool {
        return genericParams.size() > 0 and instantiator == nil
    }
    func isInstantiation() => bool {
        return instantiator != nil
    }
    func isGenericInstantiation() => bool {
        return genericParams.size() > 0 and isInstantiation()
    }
    func findLocalSymbol(symbolname: string) => AstNode {
        var symbol = context.findLocalSymbol(symbolname)
        if symbol != nil {
            // println("ClassDef.findLocalSymbol found:", symbolname, toString(), symbol.toString())
            return symbol
        }
        // println("ClassDef.findLocalSymbol in bases", symbolname, bases)
        for b in bases {
            symbol = b.target.findLocalSymbol(symbolname) if b.target != nil else nil
            if symbol != nil {
                // println("ClassDef.findLocalSymbol found:", symbolname, toString(), symbol.toString())
                return symbol
            }
        }
        return nil
    }
    func findMember(symbolname: string) => AstNode {
        // println("ClassDef.findMember", symbolname, toString())
        return findLocalSymbol(symbolname)
    }
    func visitChildren(visitor: AstVisitor) {
        if isProtoType() {
            genericParams.each({$0.visit(visitor)})
            return
        }
        genericParams.each({$0.visit(visitor)})
        bases.each({$0.visit(visitor)})
        definitions.each({$0.visit(visitor)})
    }
    func instantiate(genericArgs: [GenericArg], visitor: AstVisitor) => (AstNode, bool) {
        checkGenericArgsCompatible(genericParams, genericArgs)
        if instantiator == nil {
            instantiator = GenericClassInstantiator()
        }
        var cls = instantiator.find(genericArgs)
        if cls != nil {
            return cls, false
        }
        var gencls = clone() as ClassDef
        gencls.instantiation = GenericClassInstantiation(params=genericParams, args=genericArgs)
        instantiator.cache(gencls)
        // visitor.project.setupNewItem(cls, this, visitor)
        return gencls, true
    }
}

extension UserType {
    func toString = "UserType(%s,id=%s)" % (fullpath, formatId())
}

extension AttrRef {
    func toString = "AttrRef(%s.%s,id=%s)" % (object.toString(), ref, formatId())
}

func getReturnType(call: Call) => Type {
    var rettype = call.caller.getSpec().returnType
    // println("getReturnType", call, rettype)
    return rettype
}

func AstNode.getType() => Type =
    do match {
        AstNode => nil
        Literal => type
        Param => type
        Subscript => Types.getSubscriptType(collection.getType(), key) if collection.getType() != nil else nil
        Call => caller.getSpec().returnType if caller.getSpec() else nil
        Closure => spec if spec else expectedType
        Identifier => target.getType() if target else nil
        ClassDef => this
        SingleVarDef => type
        ArgumentPlaceholder => targetParam.getType() if targetParam else nil
        AttrRef => target.getType() if target else nil
    }

func AstNode.getTargetRealType(ut: UserType) => Type =
    do match {
        AstNode => ut
        UserType => getRealType()
        TypeDef => target.getRealType()
        FuncSpec => this
    }

func AstNode.getRealType() => Type =
    do match {
        AstNode => getType().getRealType() if getType() else nil
        UserType => target.getTargetRealType(this) if target else this
        Closure => spec if spec else (expectedType.getRealType() if expectedType else nil)
        FuncSpec => this
    }

func AstNode.getTypeClass() => TypeClass =
    do match {
        AstNode => getType().getTypeClass() if getType() else nil
        BuiltinType => typeClass
        UserType => target.getTypeClass() if target else nil
        TypeDef => target.getTypeClass()
        ClassDef => typeClass
        TypeClass => this
    }

func getClassSpec(cls: ClassDef) => FuncSpec {
    // println("getClassSpec", cls, cls.constructors[0].spec, cls.constructors[0].spec.returnType)
    return cls.constructors[0].spec
}

func isSameType(x: AstNode, y: AstNode) {
    // println("isSameType", x, y, x.toString(), y.toString(), x.getTypeClass(), y.getTypeClass())
    do assert x.getTypeClass() != nil and y.getTypeClass() != nil, ("isSameType", x, y, x.toString(), y.toString(), x.getTypeClass(), y.getTypeClass())
    return x.getTypeClass() == y.getTypeClass()
}

func AstNode.getSpec() => FuncSpec = 
    do match {
        AstNode => nil
        FuncDef => spec
        FuncProto => spec
        Closure => spec if spec else (expectedType.getRealType() if expectedType else nil)
        ClassDef => constructors[0].spec
        //ClassDef => getClassSpec(this)
        Identifier => target.getSpec() if target else nil
        AttrRef => target.getSpec() if target else nil
        Call => caller.getSpec()
    }

class Types {
    @static_method
    func getIntegerValue(node: AstNode) => int =
        match(node, {
            AstNode => -1
            IntLiteral => node.value
        })
    @static_method
    func getSubscriptType(node: AstNode, key: Expression) => Type {
        // println("getSubscriptType", node, key)
        return match(node, {
            AstNode => nil
            UserType => node.target.getSubscriptType()
            // ArrayType => node.elementType
            // ListType => node.elementType
            // TupleType => node.elementTypes[getIntegerValue(key)]
            // DictType => node.valueType
        })
    }
    func AstNode.getSubscriptType() => Type {
        return nil
    }
}
