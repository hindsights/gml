package gml

func createNil() => Nil {
	return Nil()
}

func createThis() => This {
	return This()
}

func createCharLiteral(text: string) => CharLiteral {
	// println("createCharLiteral", text)
	return CharLiteral(text = text)
}

func createStringLiteral(text: string) => StringLiteral {
	return StringLiteral(text = text)
}

func createIntLiteral(text: string) => IntLiteral {
	return IntLiteral(text = text, value=int.parse(text, -1))
}

func createFloatLiteral(text: string) => FloatLiteral {
	return FloatLiteral(text = text)
}

func createBoolLiteral(text: string) => Identifier {
	do assert text == "true" or text == "false", "createBoolLiteral", text
    return BoolLiteral("bool", true if text == "true" else false)
}

func createPrimitiveLiteral(text: string, typename: string) => Literal {
	// println("createPrimitiveLiteral", text, typename)
	if typename in ["int", "uint", "long", "ulong"] {
		return createIntLiteral(text)
	}
	if typename in ["float", "double"] {
		return createFloatLiteral(text)
	}
	if typename in ["string", "cstring"] {
		return createStringLiteral(text)
	}
	if typename == "char" {
		return createCharLiteral(text)
	}
	if typename == "bool" {
		do assert text == "true" or text == "false", "createPrimitiveLiteral bool", text, typename
		return BoolLiteral(text=text, value=text=="true")
	}
	do assert false, "createPrimitiveLiteral:text=%s,typename=%s" % (text, typename)
}

func createIdentifier(name: string) => Identifier {
    return Identifier(name = name)
}

func createPackage(fullpath: string, path: [string]) => Package {
    // println("createPackage", fullpath, path.size(), path[0])
    do assert not fullpath.empty(), "createPackage"
	do assert not path.empty(), "createPackage"
    return Package(path=path, fullpath=fullpath)
}

func createPackageByString(path: string) => Package {
    do assert not path.empty(), "createPackageByString"
    // println("createPackageByString", path)
    return Package(fullpath=path, path=path.split("."))
}

func createPackageByPath(path: [string]) => Package {
    // println("createPackageByPath", path.size(), path[0])
    return Package(fullpath=".".join(path), path=path)
}

func createRootPackage() => Package {
    // println("createRootPackage")
    return Package()
}

func createVoidType() => UserType {
    // return VoidType()
	return createPrimitiveType("void")
}

func createUserType(fullpath: string) => UserType {
    // var qn = path as IdList
    // println("createUserType", qn.names.size(), qn.full, qn.names[0])
    // assert qn.full != "void" and qn.full != "cstring"
    return UserType(path=fullpath.split("."), fullpath=fullpath)
}

func createPrimitiveType(name: string) => Type {
	return createUserType(name)
}

