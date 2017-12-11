package gml

func formatHeaderFilePath(pkg: Package, name: string) = "\"" + "/".join(pkg.path) + "/" + name + ".hpp\""

class TypeRefAnalyzer: AstVisitor {

    func visit(node: AstNode)
    {
        return node.analyzeTypeRef(this)
    }
    func AstNode.analyzeTypeRef(visitor: TypeRefAnalyzer)
    {
        // println("AstNode.analyzeTypeRef", toString(), getOwner().toString(), visitor.toString())
        return visitChildren(visitor)
    }
    func UserType.analyzeTypeRef(node: UserType, visitor: TypeRefAnalyzer)
    {
    	// println("UserType.analyzeTypeRef", fullpath, getOwner().toString())
    	getCodeUnit().addTypeRef(node)
    	return node
    }
}

class PreTransformer: AstTransformer
{
    var typeRefAnalyzer = TypeRefAnalyzer()
    func visit(node: AstNode) => AstNode {
        // println("PreTransformer.visit", node, node.getOwner())
        return node.pretransform(this)
    }
    func AstNode.pretransform(visitor: PreTransformer) => AstNode {
        visitChildren(visitor)
        return this
    }
    func FuncDef.pretransform(visitor: PreTransformer) => Definition {
        return this
    }
    func pretransformDefs(defs: [Definition]) => [Definition] {
        var newDefs: [Definition]
        for def in defs {
            var ctx = pushDefinitionContext(def)
            var newdef = def.pretransform(this)
            // save newly pretransformed definitions in previous item's internal children(like CaseClassDef)
            newDefs.extend(ctx.definitions)
            if newdef != nil {
                newDefs.append(newdef)
            }
            popDefinitionContext()
        }
        return newDefs
    }
    func CodeUnit.pretransform(visitor: PreTransformer) => CodeUnit {
        println("CodeUnit.pretransform", name, definitions.size())
        definitions = visitor.pretransformDefs(definitions)
        return this
    }
    func ClassDef.pretransform(visitor: PreTransformer) => ClassDef {
        // println("ClassDef.pretransform", toString(), getOwner())
        definitions = visitor.pretransformDefs(definitions)
        return this
    }
    func CaseClassDef.pretransform(visitor: PreTransformer) => Definition {
        // do assert false, "CaseClassDef.pretransform", toString()
        var ownercls = getOwner() as ClassDef
        var ownerext = getOwner() as ExtensionDef
        var clsname = ownercls.name if ownercls != nil else ownerext.name
        // println("CaseClassDef.pretransform", toString(), getOwner(), ownercls, ownerext)
        var cls = ClassDef(name=name, bases=[UserType(path=[clsname], fullpath=clsname)], definitions=definitions)
        var ctx = visitor.getDefinitionContext(1)
        ctx.definitions.append(cls)
        visitor.setupNewItem(cls, ownercls.getOwner(), true)
        return nil
    }
}
