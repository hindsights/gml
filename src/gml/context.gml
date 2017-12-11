package gml

class AstSimpleContext {
    var owner: AstNode
    var node: AstNode

    func getOwner() => AstNode {
        return owner
    }
    func setOwner(owner1: AstNode) {
        //assert(node, "AstSimpleContext.setOwner", owner1.toString(), node)
        // println("AstSimpleContext.setOwner", node.toString(), owner1.toString())
        do assert owner1 != nil or owner == nil, ("AstSimpleContext.setOwner", node.toString(), owner1.toString())
        this.owner = owner1
    }
    func resolveMember(path: [string]) => AstNode {
        // println("AstSimpleContext.resolveMember", path, node.toString(), owner)
        return nil
    }
    func resolveSymbol(path: [string]) => AstNode {
        // println("AstSimpleContext.resolveSymbol", path, node.toString(), owner)
        do assert not path.empty(), "resolveSymbol: path should not be empty"
        var symbol = node.findLocalSymbol(path[0])
        if symbol != nil {
            if path.size() > 1 {
                // println("AstSimpleContext.resolveSymbol continue", path, node.toString(), owner, symbol.toString())
                return symbol.getContext().resolveMember(path[1:])
            } else {
                // println("AstSimpleContext.resolveSymbol found", path, node.toString(), owner, symbol.toString())
                return symbol
            }
        }
        if owner == nil {
            // println("AstSimpleContext.resolveSymbol failed:", path, node.toString(), owner, symbol)
            return nil
        }
        // println("AstSimpleContext.resolveSymbol in owner", path, node.toString(), owner)
        return owner.resolveSymbol(path) if owner else nil
    }
    func resolveTypeSymbols(path: [string]) => AstNode {
        return nil
    }
    func resolveTypeSymbol(path: [string]) => AstNode {
        // println("resolveTypeSymbol", path, node, owner)
        var symbol = resolveSymbol(path)
        if symbol == nil {
            return nil
        }
        // println("resolveTypeSymbol first", path, node, owner, symbol)
        // return symbol
        var ret = do match symbol {
            AstNode => owner.resolveTypeSymbol(path) if owner else nil
            ClassDef => symbol
            TypeDef => symbol
            Type => symbol
            TypeClass => symbol
            GenericTypeArg => symbol.type
        }
        // println("resolveTypeSymbol ret", path, node, owner, symbol, ret)
        return ret
    }
    func findSymbol(name: string) => AstNode {
        // println("findSymbol", name, node.toString(), owner)
        return owner.findSymbol(name) if owner else nil
    }
    func findLocalSymbol(name: string) => AstNode {
        // println("findLocalSymbol", name, node.toString(), owner)
        return nil
    }
    func addSymbol(name: string, symbol: AstNode) {
        // println("AstSimpleContext.addSymbol", name, node.toString(), symbol.toString())
        if owner {
            owner.addSymbol(name, symbol)
        }
    }
    func eachSymbol(f: func (name: string, symbol: AstNode) => void) {
    }
}

class AstBlockContext: AstSimpleContext {
    var symbols: {string: AstNode}
    // var types: {string: AstNode}

    func findLocalSymbol(name: string) => AstNode {
        var ret = symbols.get(name, nil)
        // println("AstBlockContext.findLocalSymbol", name, node, owner, ret)
        return ret
    }
    func addSymbol(name: string, symbol: AstNode) {
        // println("AstBlockContext.addSymbol", name, node.toString(), symbol)
        do assert symbol != nil and name not in symbols, "AstBlockContext.addSymbol symbol existed", name, symbol, node
        //do assert name != "FileInfo", "AstBlockContext.addSymbol symbol FileInfo", symbol, node
        symbols[name] = symbol
    }
    func resolveMember(path: [string]) => AstNode {
        // println("AstBlockContext.resolveMember", path, node.toString(), owner)
        do assert not path.empty(), "resolveMember: path should not be empty"
        var symbol = node.findMember(path[0])
        if symbol != nil and path.size() > 1 {
            return symbol.getContext().resolveMember(path[1:])
        }
        return symbol
    }
    func findSymbol(name: string) => AstNode {
        // println("AstBlockContext.findSymbol", name, node.toString(), owner)
        var symbol = findLocalSymbol(name)
        if symbol {
            // println("AstBlockContext.findSymbol found:", name, node.toString(), owner, symbol.toString())
            return symbol
        }
        if owner == nil {
            // println("AstBlockContext.findSymbol failed:", name, node.toString(), owner)
            return nil
        }
        // println("AstBlockContext.findSymbol in owner:", name, node.toString(), owner)
        return owner.findSymbol(name)
    }
    func eachSymbol(f: func (name: string, symbol: AstNode) => void) {
        symbols.each({f($0, $1)})
    }
}

//@db.index(addDefinition, [(functions, FuncDef), (classes, ClassDef), (vars, VarDef), (enums, EnumDef), (types, TypeDef)])
class AstFullContext: AstBlockContext {
    // var functionNames: { string: FuncDef }
    var functions: [FuncDef]
    // var classNames: { string: ClassDef }
    var classes: [ClassDef]
    // var varNames: { string: SingleVarDef }
    var vars: [SingleVarDef]
    // var constNames: { string: ConstSpec }
    var consts: [ConstSpec]

    // var enumNames: { string: EnumDef }
    var enums: [EnumDef]
    // var typeNames: { string: TypeDef }
    var types: [TypeDef]

    func addSymbol1(name: string, symbol: AstNode) => void {
        // println("AstFullContext.addSymbol", name, node.toString(), symbol)
        do assert symbol != nil and name not in symbols, "AstFullContext.addSymbol symbol existed", name, symbol, node
        //do assert name != "FileInfo", "AstFullContext.addSymbol symbol FileInfo", symbol, node
        cacheDefinition1(symbol)
    }
    func cacheDefinition1(symbol: AstNode) => void {
        // println("AstFullContext.cacheDefinition", symbol, node, owner)
        do match symbol {
            case AstNode:
                do assert false, "AstFullContext.cacheDefinition", symbol.toString(), owner.toString(), node.toString()
            case ClassDef:
                symbols[symbol.name] = symbol
                classes.append(symbol)
            case FuncDef:
                symbols[symbol.name] = symbol
                functions.append(symbol)
            case MultipleVarDef:
                symbol.vars.each({cacheDefinition1($0)})
            case SingleVarDef:
                symbols[symbol.name] = symbol
                vars.append(symbol)
        }
    }
}

extension AstSimpleContext { 
    func getFullContext() => AstFullContext {
        // println("AstSimpleContext.getFullContext", this, node, node.toString(), owner)
        return owner.getContext().getFullContext() if owner else nil
    }
    func getBlockContext() => AstBlockContext {
        //println("AstSimpleContext.getBlockContext", this, node, node.toString())
        return owner.getContext().getBlockContext() if owner else nil
    }
}

extension AstBlockContext { 
    func getFullContext() => AstFullContext {
        // println("AstBlockContext.getFullContext", this, node, node.toString(), owner)
        return owner.getContext().getFullContext() if owner else nil
    }
    func getBlockContext() => AstBlockContext {
        //println("AstBlockContext.getBlockContext", this, node, node.toString())
        return this
    }
}

extension AstFullContext { 
    func getFullContext() => AstFullContext {
        //println("AstFullContext.getFullContext", this, node, node.toString())
        return this
    }
    func getBlockContext() => AstBlockContext {
        //println("AstFullContext.getBlockContext", this, node, node.toString())
        return this
    }
}

extension AstNode { 
    func getFullContext() => AstFullContext {
        //println("AstNode.getFullContext", this, toString(), getContext())
        //assert(false, "AstNode.getFullContext")
        return getContext().getFullContext()
    }
    func getBlockContext() => AstBlockContext {
        //println("AstNode.getBlockContext", this, toString())
        return getContext().getBlockContext()
    }
    func getOwnerFullContext = getOwner().getFullContext()
    func getOwnerBlockContext = getOwner().getBlockContext()
    func getClassDef() => ClassDef =
        do match {
            ClassDef => this
            AstNode => getOwner().getClassDef() if getOwner() else nil
        }
    func getFuncDef() => FuncDef =
        do match {
            FuncDef => this
            AstNode => getOwner().getFuncDef() if getOwner() else nil
        }
    func getCodeUnit() => CodeUnit =
        do match {
            CodeUnit => this
            AstNode => getOwner().getCodeUnit() if getOwner() else nil
        }
    func getUnit() => AstNode =
        do match {
            CodeUnit => this
            LibUnit => this
            AstNode => getOwner().getUnit() if getOwner() else nil
        }
    func getUnitHandler() => UnitHandler =
        do match {
            CodeUnit => handler
            LibUnit => handler
            AstNode => getOwner().getUnitHandler() if getOwner() else nil
        }
}
