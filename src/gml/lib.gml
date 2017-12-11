package gml

import gml.go.SourceWriter
import gml.go.DeepAnalyzer

class AstFormatter: AstVisitor {
}

@mixin(AstBlockContext, context, getContext, node=this)
class LibFunc(name: string, spec: FuncSpec, pkg: string): SimpleNode {
    var packages: [string]
    func getType() => FuncSpec = getSpec()
    func getSpec() => FuncSpec = spec

    func cacheName(visitor: NameCacher) {
        // Log.debug("LibFunc.cacheName", name, pkg, this, getOwner())
        getOwner().addSymbol(name, this)
        visitChildren(visitor)
    }
}

class LibClass : SimpleNode {
    
}

@mixin(AstBlockContext, context, getContext, node=this)
class ScriptFunc(name: string): SimpleNode {
    func resolveScript(visitor: Resolver, script: Script) {
        do assert false, "ScriptFunc.resolveScript unimplemented", script
    }
}

class SimpleLibFunc: LibFunc {
    var generator: func(writer: SourceWriter, call: Call) => string
    func SimpleLibFunc(proto: FuncProto) {
        name = proto.name
        spec = proto.spec
    }
    func writeCall(writer: SourceWriter, call: Call) => string {
    	return generator(writer, call)
    }
}

class CustomLibFunc: LibFunc {
	var generator: func(writer: SourceWriter, call: Call, attr: AttrRef) => void
    func CustomLibFunc(proto: FuncProto) {
        name = proto.name
        spec = proto.spec
    }
    func writeAttrCall(writer: SourceWriter, call: Call, attr: AttrRef) => void {
        generator(writer, call, attr)
    }
    func formatObjectCall() {
    }
    func resolveCallType(visitor: Resolver, call: Call) {
    	// Log.debug("CustomLibFunc.resolveCallType", toString(), call)
    	//call.spec = spec
    }
    func analyzeDependency(visitor: DeepAnalyzer, unit: CodeUnit) {
    	// Log.debug("CustomLibFunc.analyzeDependency", name, unit.name, packages)
    	//visitor.unit.addSourceDeps(headers)
        packages.each({unit.handler.addDep($0)})
    }
    func initializeOwner() {
        // Log.debug("CustomLibFunc.initializeOwner", name, this, spec)
        spec.setOwner(this)
        // Log.debug("CustomLibFunc.initializeOwner ok", name, this, spec, spec.getOwner())
        spec.initializeOwner()
    }
    func visitChildren(visitor: AstVisitor) {
        spec.visit(visitor)
    }
}

@mixin(AstBlockContext, context, getContext, node=this)
class LibUnit(name: string, packageDef: PackageDef, definitions: [Definition]): AstNode {
    var pkg: Package
    var handler: UnitHandler

    func addSymbol(name: string, node: AstNode) {
        // Log.debug("LibUnit.addSymbol", name, node, toString(), pkg, pkg.fullpath)
        context.addSymbol(name, node)
        pkg.addSymbol(name, node)
    }

    func init(rootpkg: Package) {
        // Log.debug("LibUnit.init name=", name, "pkgpath=", packageDef.path)
        pkg = rootpkg.getPackageByList(packageDef.path)
        //getContext().owner = pkg
        setOwner(pkg)
    }
}

@mixin(AstBlockContext, context, getContext, node=this)
class BuiltinTypeClass(definitions: [AstNode]): TypeClass {
	typedef CustomGenerateFunc = func (writer: SourceWriter, call: Call, attr: AttrRef) => string

    func resolveAttr(attr: AttrRef) => AstNode = findSymbol(attr.ref)
	func addFunc(f: LibFunc) {
		// Log.debug("addFunc", f.name, f, toString())
		definitions.append(f)
		// addSymbol(f.name, f)
	}
	func addCustomFuncEntries(entries: [LibFuncInfo]) {
		Log.debug("addCustomFuncEntries", entries.size(), toString(), entries)
		for entry in entries {
			var f = CustomLibFunc(entry.proto)
			f.generator = entry.generator
			f.packages = entry.packages
			addFunc(f)
		}
	}

	func addCustomFuncsByProto(protos: [FuncProto]) {
		Log.debug("addCustomFuncsByProto", protos)
		var entries = [LibFuncInfo(proto=proto, generator=#"generate_${proto.name}") for proto in protos]
		addCustomFuncEntries(entries)
	}
	func addCustomFuncs(protostrs: [string]) {
		Log.debug("addCustomFuncs", protostrs)
		var protos = [CodeUnitParser.parseFuncProto(protostr) for protostr in protostrs]
		addCustomFuncsByProto(protos)
	}

	func addSimpleFunc(proto: FuncProto) {
		Log.debug("addSimpleFunc", proto.name)
		var cf = SimpleLibFunc()
		cf.name = proto.name
		cf.spec = proto.spec
		addFunc(cf)
	}
    func formatParamArg(visitor: AstFormatter, arg: AstNode) => string = arg.format(visitor)
}

class BasicTypeClass: BuiltinTypeClass {
	var name: string

	func cacheName(visitor: NameCacher) {
		getOwner().addSymbol(name, this)
		visitChildren(visitor)
	}
}

class GenericTypeClassImpl: BasicTypeClass {
	var instantiation: GenericClassInstantiation
    func visitChildren(visitor: AstVisitor) {
        // Log.debug("GenericTypeClassImpl.visitChildren", visitor.toString(), this)
        definitions.each({$0.visit(visitor)})
    }
    func initializeOwner() {
        definitions.each({
            $0.setOwner(this)
            $0.initializeOwner()
        })
    }
    func cacheName(visitor: NameCacher) {
		instantiation.registerTypes(this)
		visitChildren(visitor)
	}
}

func checkGenericTypeArg(arg: GenericArg, param: GenericTypeParam) => bool {
    do match arg {
        case GenericTypeArg:
            // Log.debug("checkGenericTypeArg ok", arg, param)
            return true
        default:
            do assert false, ("checkGenericTypeArg fail", arg, param)
            return false
    }
}

func checkGenericLiteralArg(arg: GenericArg, param: GenericTypeParam) => bool {
    do match arg {
        case GenericLiteralArg:
            // Log.debug("checkGenericLiteralArg ok", arg, param)
            return true
        default:
            do assert false, ("checkGenericLiteralArg fail", arg, param)
            return false
    }
}

func checkGenericVariadicTypeArg(arg: GenericArg, param: GenericTypeParam) => bool {
    do match arg {
        case GenericVariadicTypeArg:
            // Log.debug("checkGenericVariadicTypeArg ok", arg, param)
            return true
        default:
            do assert false, ("checkGenericVariadicTypeArg fail", arg, param)
            return false
    }
}

func checkGenericArgCompatible(param: GenericParam, arg: GenericArg) {
    do match param {
        case GenericTypeParam:
            do assert (arg as GenericTypeArg) != nil, ("checkGenericArgCompatible GenericTypeParam fail", arg, param)
        case GenericLiteralParam:
            var literalarg = arg as GenericLiteralArg
            do assert literalarg != nil, ("checkGenericArgCompatible GenericLiteralParam fail", arg, param, literalarg)
            do assert literalarg.literal != nil, ("checkGenericArgCompatible GenericLiteralParam nil literal", arg, param, literalarg)
        case GenericVariadicTypeParam:
            do assert (arg as GenericVariadicTypeArg) != nil, ("checkGenericArgCompatible GenericVariadicTypeParam fail", arg, param)
        default:
            do assert false, "checkGenericArgCompatible", param, arg
    }
}

func checkGenericArgsCompatible(params: [GenericParam], args: [GenericArg]) {
    do assert params.size() == args.size(), "checkGenericArgsCompatible", (params, args)
    params.each({checkGenericArgCompatible($0, args[$1])})
}

func isLiteralEqual(x: Literal, y: Literal) => bool {
    do match x {
        case Literal:
            return false
        case IntLiteral:
            var valuey = y as IntLiteral
            return x.value == valuey.value if valuey else false
        case StringLiteral:
            var valuey = y as StringLiteral
            return x.value == valuey.value if valuey else false
        case CharLiteral:
            var valuey = y as CharLiteral
            return x.value == valuey.value if valuey else false
        case FloatLiteral:
            var valuey = y as FloatLiteral
            return x.value == valuey.value if valuey else false
    }
}

func checkGenericArgMatch(x: GenericArg, y: GenericArg) => bool {
    do match x {
        case GenericTypeArg:
            var argy = y as GenericTypeArg
            // Log.debug("checkGenericArgMatch GenericTypeArg", x.type.toString(), argy.type.toString())
            return isSameType(x.type, argy.type) if argy != nil else false
        case GenericVariadicTypeArg:
            var argy = y as GenericVariadicTypeArg
            if argy == nil {
                return false
            }
            if x.types.size() != argy.types.size() {
                // do assert false, "checkGenericArgMatch count mismatch", x, y, argy, x.types, argy.types
                return false
            }
            var isSame = true
            x.types.each({
                if not isSameType($0, argy.types[$1]) {
                    isSame = false
                    return
                }
                isSame = true
            })
            return isSame
        case GenericLiteralArg:
            var argy = y as GenericLiteralArg
            return isLiteralEqual(x.literal, argy.literal) if argy != nil else false
    }
    return false
}

func AstNode.getGenericArgs() => [GenericArg] =
    do match {
        AstNode => []
        // ClassDef => instantiation.args if instantiation != nil else []
        ClassDef => instantiation.args
        GenericTypeClassImpl => instantiation.args
    }

func checkGenericArgsMatch(xargs: [GenericArg], yargs: [GenericArg]) => bool {
    do assert xargs.size() == yargs.size(), "checkGenericArgsMatch", xargs, yargs
    xargs.each({
        // Log.debug("checkGenericArgsMatch", $0, $1, yargs[$1], $0.toString(), yargs[$1].toString())
        if not checkGenericArgMatch($0, yargs[$1]) {
            // Log.debug("checkGenericArgsMatch false", $0, $1, yargs[$1], $0.toString(), yargs[$1].toString())
            return false
        }
    })
    return true
}

func AstNode.instantiate(genericArgs: [GenericArg], visitor: AstVisitor) => (AstNode, bool) {
    do assert false, "AstNode.instantiate", genericArgs, visitor
    return nil, false
}

class GenericTypeClass<ImplType>(name: string, genericParams: [GenericParam]): TypeClass {
    var instantiator = GenericClassInstantiator()

	func instantiate(genericArgs: [GenericArg], visitor: AstVisitor) => (AstNode, bool) {
        // Log.debug("GenericTypeClass.instantiate", name, genericParams, genericArgs, this, instantiator)
        checkGenericArgsCompatible(genericParams, genericArgs)
        var cls = instantiator.find(genericArgs)
        if cls != nil {
            return cls, false
        }
        // Log.debug("GenericTypeClass.instantiate create", name, genericParams, genericArgs, this)
        var gencls = ImplType(GenericClassInstantiation(params=genericParams, args=genericArgs))
        instantiator.cache(gencls)
        // visitor.setupNewItem(gencls, this, true)
        Log.debug("GenericTypeClass.instantiate ok", name, genericParams, genericArgs, this)
		return gencls, true
	}
	func cacheName(visitor: NameCacher) {
		getOwner().addSymbol(name, this)
		visitChildren(visitor)
	}
    func visitChildren(visitor: AstVisitor) {
        // Log.debug("GenericTypeClass.visitChildren", name, visitor.toString())
        // instantiator.visit(visitor)
    }
}

class LibFuncInfo(proto: FuncProto, generator: func (writer: SourceWriter, call: Call, attr: AttrRef) => string, packages: [string]) {

}

func createLibUnit(pkgstr: string, definitions: [AstNode]) => LibUnit {
    return LibUnit(name="$" + pkgstr, packageDef=PackageDef(path=pkgstr.split("."), fullpath=pkgstr), definitions=definitions)
}
