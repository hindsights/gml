package gml.go

func getIntegerTypeNames() => [string] {
	return ["int", "long", "short", "byte", "uint", "ulong", "ushort", "int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "uintptr", "rune"]
}

func getIntegerTypes() => [Definition] {
	var names = getIntegerTypeNames()
	return [IntegerTypeClass(name) for name in names]
}

func loadTypes() => LibUnit {
	var simpletypes = [AnyRefTypeClass(), StringTypeClass(), CharTypeClass(), BoolTypeClass(), VoidTypeClass(), FloatingTypeClass("float"), FloatingTypeClass("double")] + getIntegerTypes()
	var generictypes = [
		template GenericTypeClass<ArrayTypeClassImpl>(name="Array", genericParams=[GenericTypeParam(name="ElementType"), GenericLiteralParam(type=createPrimitiveType("int"))]), 
		template GenericTypeClass<ListTypeClassImpl>(name="List", genericParams=[GenericTypeParam(name="ElementType")]),
		template GenericTypeClass<DictTypeClassImpl>(name="Dict", genericParams=[GenericTypeParam(name="KeyType"), GenericTypeParam(name="ValueType")]), 
		template GenericTypeClass<SetTypeClassImpl>(name="Set", genericParams=[GenericTypeParam(name="ElementType")]),
		template GenericTypeClass<TupleTypeClassImpl>(name="Tuple", genericParams=[GenericVariadicTypeParam(name="ElementTypes")])]
    return [createLibUnit("sys.builtin", simpletypes + generictypes)]
}

class Types {
    @static_method
	func createTypeClass(node: AstNode, targetModule: LangModule) => TypeClass =
		match(node, {
			AstNode => nil
			ClassDef => targetModule.createUserTypeClass(node)
			FuncSpec => FunctionTypeClass(node)
			PointerType => PointerTypeClass(node)
		})
}

class SimpleBuiltinTypeClass: BuiltinTypeClass {
	var name: string

	func formatParamType(visitor: AstFormatter) => string {
		return name
	}
    func formatParamUserType(formatter: AstFormatter, ut: UserType) => string {
		return name
	}
	func formatStorageType(visitor: AstFormatter) => string {
		return name
	}
	func formatReturnType(visitor: AstFormatter) => string {
		return name
	}
	func formatType(visitor: AstFormatter) => string {
		return name
	}
	func cacheName(visitor: NameCacher) {
		// Log.debug("SimpleBuiltinTypeClass.cacheName", name)
		getOwner().addSymbol(name, this)
		visitChildren(visitor)
	}
    func visitChildren(visitor: AstVisitor) {
        // Log.debug("SimpleBuiltinTypeClass.visitChildren", this, visitor)
        definitions.each({$0.visit(visitor)})
    }
}

class VoidTypeClass: SimpleBuiltinTypeClass {
	func VoidTypeClass() {
		name = "void"
	}
	func formatType(visitor: AstFormatter) => string {
		return ""
	}
	func formatParamType(visitor: AstFormatter) => string {
		return ""
	}
    func formatParamUserType(formatter: AstFormatter, ut: UserType) => string {
		return ""
	}
    func createDefaultValue() => Expression {
		do assert false, "VoidTypeClass.createDefaultValue"
        return nil
    }
}

class FunctionTypeClass: TypeClass {
	var spec: FuncSpec
	func FunctionTypeClass(fspec: FuncSpec) {
		spec = fspec
	}
}

class PointerTypeClass: TypeClass {
	var type: PointerType
	func PointerTypeClass(t: PointerType) {
		type = t
	}
}

class AnyRefTypeClass: SimpleBuiltinTypeClass {
	func AnyRefTypeClass() {
		name = "AnyRef"
	}
}

func AstNode.getTypeName() =
	do match {
		AstNode => "nil(AstNode)"
		UserType => fullpath
	}

class StringTypeClass: SimpleBuiltinTypeClass {
	var elementType: Type
	
	func StringTypeClass() {
		Log.debug("StringTypeClass.init")
		name = "string"
		elementType = createUserType("char")
		addCustomFuncEntries([LibFuncInfo(proto=`func size() => int`, generator=generate_size)])
	}
	func getSubscriptType() => AstNode {
		return elementType
	}

	func generate_size(writer: SourceWriter, call: Call, attr: AttrRef) {
		writer.writer.writeInlineBlockExpression("len(", ")", {attr.object.writeSource(writer)})
	}

    func formatStorageType(visitor: AstFormatter) => string {
    	return "string"
    }
    func createDefaultValue() => Expression {
        return StringLiteral()
    }
}

class NumberTypeClass: SimpleBuiltinTypeClass {
    func writeBinaryOp(writer: SourceWriter, bexpr: BinaryOp) {
		bexpr.left.writeSource(writer)
		writer.writer.write(" %s " % bexpr.op)
		bexpr.right.writeSource(writer)
    }
}

class FloatingTypeClass: SimpleBuiltinTypeClass {
	func FloatingTypeClass(typename: string) {
		name = typename
	}
    func createDefaultValue() => Expression {
        return FloatLiteral(text="0.0", value=0.0)
    }
}

class IntegerTypeClass: NumberTypeClass {
	func IntegerTypeClass(n: string) {
		name = n
	}
    func createDefaultValue() => Expression {
        return IntLiteral(text="0", value=0)
    }
}

class BoolTypeClass: SimpleBuiltinTypeClass {
	func BoolTypeClass() {
		name = "bool"
	}
    func formatUnaryOp(visitor: AstFormatter, uexpr: UnaryOp) => string {
    	do assert uexpr.op == "not"
    	return "!%s" % uexpr.operand.format(visitor)
    }
    func createDefaultValue() => Expression {
        return BoolLiteral(text="false", value=false)
    }
}

class CharTypeClass: SimpleBuiltinTypeClass {
	func CharTypeClass() {
		name = "char"
		addCustomFuncEntries([LibFuncInfo(proto=`func isDigit() => bool`, generator=generate_isDigit, packages=["unicode"])])
		addCustomFuncEntries([LibFuncInfo(proto=`func isLetter() => bool`, generator=generate_isLetter, packages=["unicode"])])
		addCustomFuncEntries([LibFuncInfo(proto=`func isLower() => bool`, generator=generate_isLower, packages=["unicode"])])
		addCustomFuncEntries([LibFuncInfo(proto=`func isUpper() => bool`, generator=generate_isUpper, packages=["unicode"])])
	}

	func generate_isDigit(writer: SourceWriter, call: Call, attr: AttrRef) {
		writer.writer.writeInlineBlockExpression("unicode.IsDigit(", ")", {attr.object.writeSource(writer)})
	}
	func generate_isLetter(writer: SourceWriter, call: Call, attr: AttrRef) {
		writer.writer.writeInlineBlockExpression("unicode.IsLetter(", ")", {attr.object.writeSource(writer)})
	}
	func generate_isLower(writer: SourceWriter, call: Call, attr: AttrRef) {
		writer.writer.writeInlineBlockExpression("unicode.isLower(", ")", {attr.object.writeSource(writer)})
	}
	func generate_isUpper(writer: SourceWriter, call: Call, attr: AttrRef) {
		writer.writer.writeInlineBlockExpression("unicode.isUpper(", ")", {attr.object.writeSource(writer)})
	}
    func createDefaultValue() => Expression {
        return CharLiteral(text="\0", value=0)
    }
}

@singleton
class IntegerTypeClassFactory {
	var types: {string:TypeClass}
	var int8Type: TypeClass
	var uint8Type: TypeClass
	var int16Type: TypeClass
	var uint16Type: TypeClass
	var int32Type: TypeClass
	var uint32Type: TypeClass
	var int64Type: TypeClass
	var uint64Type: TypeClass
	var intType: TypeClass
	var uintType: TypeClass
	var longType: TypeClass
	var ulongType: TypeClass
	var shortType: TypeClass
	var ushortType: TypeClass
	var byteType: TypeClass
	var uintptrType: TypeClass
	var runeType: TypeClass

	func IntegerTypeClassFactory() {
	}
	func init() {
		int8Type = addTypes(["int8", "sbyte"], "int8")
		uint8Type = addTypes(["uint8", "byte"], "uint8")
		int16Type = addType("int16", "int16")
		uint16Type = addType("uint16", "uint16")
		int32Type = addTypes(["int32", "rune"], "int32")
		uint32Type = addType("uint32", "uint32")
		int64Type = addTypes(["int64", "long"], "int64")
		uint64Type = addTypes(["uint64", "ulong", "uintptr"], "uint64")
		intType = addType("int", "int")
		uintType = addType("uint", "uint")
		shortType = addType("short", "int16")
		ushortType = addType("ushort", "uint16")
		byteType = uint8Type
		longType = int64Type
		ulongType = uint64Type
		uintptrType = uint64Type
		runeType = int32Type
	}
	func addType(name: string, realname: string) {
		Log.debug("IntegerTypeClassFactory.addType", name, realname)
		var tc = IntegerTypeClass(realname)
		types.set(name, tc)
		return tc
	}
	func addTypes(names: [string], realname: string) {
		Log.debug("IntegerTypeClassFactory.addTypes", realname)
		var tc = IntegerTypeClass(realname)
		for name in names {
			Log.debug("IntegerTypeClassFactory.addTypes one", name, realname)
			types.set(name, tc)
		}
		return tc
	}
}

@singleton
class PrimitiveTypeClassFactory: SimpleNode {
	var typeClasses: {string: TypeClass}

	func get(name: string) => TypeClass {
		var tc = typeClasses.get(name, nil)
		do assert tc, ("PrimitiveTypeClassFactory.get: type not found", name)
		return tc
	}
	func add(name: string, tc: TypeClass) {
		typeClasses.set(name, tc)
	}
	func addIntegers() {
		for name, tc in IntegerTypeClassFactory.instance().types {
			add(name, tc)
		}
	}
	func PrimitiveTypeClassFactory() {
	}
	func init() {
		Log.debug("PrimitiveTypeClassFactory start", this)
	}
	func visitChildren(visitor: AstVisitor) {
		typeClasses.each({$1.visit(visitor)})
	}
}

class BasicBinaryOpHandler: BinaryOpHandler {
}
class LogicalResultBinaryOpHandler: BasicBinaryOpHandler {
	func getType(expr: BinaryOp) = createPrimitiveType("bool")
}

class ArithmeticBinaryOpHandler: BasicBinaryOpHandler {
	func getType(expr: BinaryOp) = expr.left.getType()
}

class LogicalBinaryOpHandler: LogicalResultBinaryOpHandler {
}

class ComparisonBinaryOpHandler: LogicalResultBinaryOpHandler {
}

class BitwiseBinaryOpHandler: BasicBinaryOpHandler {
	func getType(expr: BinaryOp) = expr.left.getType()
}

class MembershipBinaryOpHandler: LogicalResultBinaryOpHandler {
}

@singleton
class BinaryOpHandlerFactory {
	var handlers: {string: BinaryOpHandler}

	func get(name: string) => BinaryOpHandler = handlers.get(name)
	func add(name: string, handler: BinaryOpHandler) {
		handlers[name] = handler
	}
	func BinaryOpHandlerFactory() {
		init()
	}
	func init() {
		var arithmetic = ArithmeticBinaryOpHandler()
		var logical = LogicalBinaryOpHandler()
		var comparison = ComparisonBinaryOpHandler()
		var bitwise = BitwiseBinaryOpHandler()
		var membership = MembershipBinaryOpHandler()
		["+", "-", "*", "/", "%"].each({add($0, arithmetic)})
		["and", "or", "xor"].each({add($0, logical)})
		["&", "|", "^"].each({add($0, bitwise)})
		["==", "!=", ">", "<", ">=", "<="].each({add($0, comparison)})
		["in", "not-in"].each({add($0, membership)})
	}
}

class ArrayTypeClassImpl: GenericTypeClassImpl {
	var elementType: Type
	var size: int
	func ArrayTypeClassImpl(inst: GenericClassInstantiation) {
		instantiation = inst
		name = "Array"
	}
    func needDefaultValue() = false
	// func formatDefaultValue(formatter: AstFormatter) = "make(%s)" % type.formatType(formatter)
}

class ListTypeClassImpl: GenericTypeClassImpl {
	var elementType: Type
	func ListTypeClassImpl(inst: GenericClassInstantiation) {
		instantiation = inst
		name = "List"
		elementType = (instantiation.args[0] as GenericTypeArg).type
		Log.debug("ListTypeClassImpl constructor addCustomFuncs", toString())
		addCustomFuncEntries([LibFuncInfo(proto=#{func size() => int}, generator=generate_size)])
	}
	func formatType(formatter: AstFormatter) = "[]%s" % elementType.formatType(formatter)

	func formatDefaultValue(formatter: AstFormatter) = "make(%s, 0, 10)" % formatType(formatter)
    func needDefaultValue() = true
	func getSubscriptType() => Type {
		return getElementType()
	}
	func getElementType() => Type {
		return elementType
	}

	func generate_size(writer: SourceWriter, call: Call, attr: AttrRef) {
		writer.writer.writeInlineBlockExpression("len(", ")", {attr.object.writeSource(writer)})
	}
}

class GenericDictGetFunc: LibFunc {
	var collectionType: DictTypeClassImpl
    func GenericDictGetFunc(dt: DictTypeClassImpl) {
		var proto = `func get(key: KeyType, defval: ValueType) => ValueType`
        name = proto.name
        spec = proto.spec
		collectionType = dt
    }
    func deepTransformAttrCall(visitor: DeepTransformer, call: Call, attr: AttrRef) {
    	Log.debug("DictGetFunc.deepTransformAttrCall", call.caller, call.getOwner(), call.getCodeUnit(), attr.toString(), call.getCodeUnit(), collectionType.valueType, collectionType.valueType.getTypeClass())
		var owner = call.getOwner()
		var unit = call.getCodeUnit()
		var ctx = visitor.getCurrentStatementContext()
		var vardef = TupleVarDef(vars=[SingleVarDef(name="itemval"), SingleVarDef(name="ok")], initial=Call(caller=AttrRef(object=attr.object, ref="getOptional"), args=[call.args[0]]))
		var itemval: AstNode
		if call.args.size() == 1 {
    		Log.debug("DictGetFunc.deepTransformAttrCall before create default arg", call.caller, call.getOwner(), call.getCodeUnit(), attr.toString(), call.getCodeUnit(), collectionType.valueType, collectionType.valueType.getTypeClass())
			itemval = collectionType.valueType.getTypeClass().createDefaultValue()
    		Log.debug("DictGetFunc.deepTransformAttrCall after create default arg", call.caller, call.getOwner(), call.getCodeUnit(), attr.toString(), call.getCodeUnit(), collectionType.valueType, collectionType.valueType.getTypeClass(), itemval)
		} else {
			itemval = call.args[1]
		}
		// var itemval = Identifier("item")
		var ifstmt = IfStatement(branches=[IfBranch(condition=UnaryOp(op="not", operand=Identifier(name="ok")), body=StatementBody(statements=[Assignment(targets=[Identifier(name="itemval")], values=[itemval], op="=")]))])
		ctx.statements.extend([vardef, ifstmt])
		visitor.setupNewItem(vardef, ctx.currentStatement.getOwner(), true)
		visitor.setupNewItem(ifstmt, ctx.currentStatement.getOwner(), true)
		var proxyvar = Identifier(name="itemval")
		visitor.setupNewItem(proxyvar, owner, true)
		return proxyvar
    }
}

class GenericDictEachFunc: LibFunc {
	var collectionType: DictTypeClassImpl
    func GenericDictEachFunc(dt: DictTypeClassImpl) {
		var proto = `func each(fn: func(key: KeyType, defval: ValueType))`
        name = proto.name
        spec = proto.spec
		collectionType = dt
    }
}

class DictTypeClassImpl: GenericTypeClassImpl {
	var keyType: Type
	var valueType: Type
	func DictTypeClassImpl(inst: GenericClassInstantiation) {
		instantiation = inst
		name = "Dict"
		keyType = (instantiation.args[0] as GenericTypeArg).type
		valueType = (instantiation.args[1] as GenericTypeArg).type
		Log.debug("DictTypeClassImpl constructor addCustomFuncs", toString(), keyType, valueType, keyType.toString(), valueType.toString())
		// addCustomFuncEntries([LibFuncInfo(proto=#{func size() => int}, generator=generate_size)])
		// addCustomFuncEntries([LibFuncInfo(proto=`func get(name: KeyType, defval: ValueType) => ValueType`, generator=generate_get, packages=["sys"])])
		// addCustomFuncEntries([LibFuncInfo(proto=FuncProto(name="each", spec=FuncSpec(params=[Param(name="fn", type=FuncSpec(params=[Param(name="key", type=type.keyType), Param(name="value", type=type.valueType)], returnType=VoidType()))], returnType=VoidType())), generator=generate_each)])
		// addCustomFuncEntries([LibFuncInfo(proto=`func each(fn: func (key: KeyType, value: ValueType))`, generator=generate_each)])
		addCustomFuncEntries([LibFuncInfo(proto=`func size() => int`, generator=generate_size)])
		// addCustomFuncEntries([LibFuncInfo(proto=`func getOptional(key: KeyType, defval: ValueType) => (ValueType, bool)`, generator=generate_getOptional)])
		// var testproto = #{func getOptional(key: ${dt.keyType}, defval: ${dt.valueType}) => (${dt.valueType}, bool)}
		addCustomFuncEntries([LibFuncInfo(proto=`func getOptional(key: KeyType, defval: ValueType) => (ValueType, bool)`, generator=generate_getOptional)])
		addFunc(GenericDictGetFunc(this))
		addFunc(GenericDictEachFunc(this))
	}
	func formatType(formatter: AstFormatter) = "map[%s]%s" % (keyType.formatParamType(formatter), valueType.formatParamType(formatter))

	func getSubscriptType() => Type {
		return getValueType()
	}
    func needDefaultValue() = true
	func formatDefaultValue(formatter: AstFormatter) = "make(%s)" % formatType(formatter)

	func getKeyType() => Type {
		return keyType
	}
	func getValueType() => Type {
		Log.debug("DictTypeClassImpl getValueType", toString(), keyType, valueType, keyType.toString(), valueType.toString())
		return valueType
	}
	func generate_get(writer: SourceWriter, call: Call, attr: AttrRef) {
		Log.debug("generate_get", attr, call, attr.object, attr.ref)
		do assert call.args.size() == 1 or call.args.size() == 2, "DictTypeClass.generate_get invalid arg count", call, call.args, attr
		writer.writer.write("sys.Maps.Get(")
		attr.object.writeSource(writer)
		writer.writer.write(", ")
		call.args[0].writeSource(writer)
		if call.args.size() == 2 {
			writer.writer.write(", ")
			call.args[1].writeSource(writer)
		} else {
			writer.writer.write(", nil")
		}
		writer.writer.write(")")
	}
	func generate_size(writer: SourceWriter, call: Call, attr: AttrRef) {
		writer.writer.writeInlineBlockExpression("len(", ")", {attr.object.writeSource(writer)})
	}
	func generate_getOptional(writer: SourceWriter, call: Call, attr: AttrRef) {
		attr.object.writeExpression(writer)
		writer.writer.writeInlineBlockExpression("[", "]", {call.args[0].writeSource(writer)})
	}
	func generate_each(writer: SourceWriter, call: Call, attr: AttrRef) => string {
		do assert call.args.size() == 1, "DictTypeClass.generate_each invalid arg count", call, call.args, attr
		var closure = call.args[0] as Closure
		Log.debug("generate_each", attr, call, call.args, closure, attr.object, attr.ref)
		var keyname = "key"
		var valuename = "value"
		do assert keyname != "" and valuename != "", "DictTypeClass.generate_each: empty param name", call.getSpec()
		writer.writer.write("for %s, %s := range " % (keyname, valuename))
		attr.object.writeExpression(writer)
		if closure != nil {
        	writer.writer.writeBlockExpression("{\n", "}", {closure.body.writeSource(writer)})
		} else {
			do assert false, "DictTypeClass.generate_each: not Closure", call.args[0]
			return "for %s, %s := range %s { %s(%s, %s) }" % (keyname, valuename, attr.object.format(writer.formatter), call.args[0].format(writer.formatter), keyname, valuename)
		}
	}
    func writeBinaryOp(writer: SourceWriter, expr: BinaryOp) {
		if expr.op == "in" {
			writer.writer.write("_, ok := %s[%s]; ok" % (expr.right.format(writer.formatter), expr.left.format(writer.formatter)))
		}
		if expr.op == "not-in" {
			writer.writer.write("_, ok := %s[%s]; !ok" % (expr.right.format(writer.formatter), expr.left.format(writer.formatter)))
		}
	}
    func createDefaultValue() => Expression {
        return DictLiteral()
    }
}

class GenericSetEachFunc: LibFunc {
	var collectionType: SetTypeClassImpl
    func GenericSetEachFunc(colltype: SetTypeClassImpl) {
		var proto = `func each(fn: func (elem: ElementType))`
        name = proto.name
        spec = proto.spec
		collectionType = colltype
    }
    func writeAttrCall(writer: SourceWriter, call: Call, attr: AttrRef) {
		do assert call.args.size() == 1, "SetTypeClass.generate_each invalid arg count", call, call.args, attr
		var closure = call.args[0] as Closure
		Log.debug("generate_each", attr, call, call.args, closure, attr.object, attr.ref)
		var itemname = "elem"
		writer.writer.write("for %s, _ := range " % itemname)
		attr.object.writeExpression(writer)
		if closure != nil {
			do assert itemname != "", "SetClaSetTypeClassss.generate_each: empty param name", call.getSpec()
        	writer.writer.writeBlockExpression("{\n", "}", {closure.body.writeSource(writer)})
		} else {
			do assert false, "SetTypeClass.generate_each: not Closure", call.args[0]
        	//writer.writeBlockExpression("{\n", "}", {closure.body.writeSource(writer)})
			return "for %s, _ := range %s { %s(%s) }" % (itemname, attr.object.format(writer.formatter), call.args[0].format(writer.formatter), itemname)
		}
    }
}

class SetTypeClassImpl: GenericTypeClassImpl {
	var elementType: Type
	func SetTypeClassImpl(inst: GenericClassInstantiation) {
		instantiation = inst
		name = "Set"
		elementType = (instantiation.args[0] as GenericTypeArg).type
		Log.debug("SetTypeClassImpl constructor addCustomFuncs", toString())
		addCustomFuncEntries([LibFuncInfo(proto=`func add(elem: ElementType)`, generator=generate_add)])
		// addCustomFuncEntries([LibFuncInfo(proto=`func each(fn: func (elem1: ElementType))`, generator=generate_each)])
		addCustomFuncEntries([LibFuncInfo(proto=`func size() => int`, generator=generate_size)])
		addFunc(GenericSetEachFunc(this))
	}

	func formatType(formatter: AstFormatter) = "map[%s]int" % elementType.formatType(formatter)
    func needDefaultValue() = true
	func formatDefaultValue(formatter: AstFormatter) = "make(%s)" % formatType(formatter)

	func getSubscriptType() => Type {
		return getElementType()
	}
	func getElementType() => Type {
		return elementType
	}

	func generate_size(writer: SourceWriter, call: Call, attr: AttrRef) {
		writer.writer.writeInlineBlockExpression("len(", ")", {attr.object.writeSource(writer)})
	}
	func generate_add(writer: SourceWriter, call: Call, attr: AttrRef) {
		writer.writer.write("%s[%s] = 1" % (attr.object.format(writer.formatter), call.args[0].format(writer.formatter)))
	}
	func generate_each(writer: SourceWriter, call: Call, attr: AttrRef) => string {
		do assert call.args.size() == 1, "SetTypeClass.generate_each invalid arg count", call, call.args, attr
		var closure = call.args[0] as Closure
		Log.debug("generate_each", attr, call, call.args, closure, attr.object, attr.ref)
		var itemname = "item"
		writer.writer.write("for %s, _ := range " % itemname)
		attr.object.writeExpression(writer)
		if closure != nil {
			do assert itemname != "", "SetClaSetTypeClassss.generate_each: empty param name", call.getSpec()
        	writer.writer.writeBlockExpression("{\n", "}", {closure.body.writeSource(writer)})
		} else {
			do assert false, "SetTypeClass.generate_each: not Closure", call.args[0]
        	//writer.writeBlockExpression("{\n", "}", {closure.body.writeSource(writer)})
			return "for %s, _ := range %s { %s(%s) }" % (itemname, attr.object.format(writer.formatter), call.args[0].format(writer.formatter), itemname)
		}
	}
    func createDefaultValue() => Expression {
        return SetLiteral()
    }
}

class TupleTypeClassImpl: GenericTypeClassImpl {
	func TupleTypeClassImpl(inst: GenericClassInstantiation) {
		instantiation = inst
		name = "Tuple"
		Log.debug("TupleTypeClassImpl constructor addCustomFuncs", toString())
		// addCustomFuncEntries([LibFuncInfo(proto=#{func size() => int}, generator=generate_size)])
	}
    func needDefaultValue() = true
    func resolveTupleVar(v: TupleVarDef, visitor: AstVisitor) {
        Log.debug("TupleTypeClassImpl.resolveTupleVar", v, visitor, this, instantiation, instantiation.args)
		var tupletype = instantiation.args[0] as GenericVariadicTypeArg
		v.vars.size().times({v.vars[$0].type = tupletype.types[$0]})
    }
}
