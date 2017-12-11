package gml.go.scripts

import gml

class GoImportScript : ScriptFunc {
    func GoImportScript() {
        name = "import"
    }
    func visitChildren(visitor: AstVisitor) {
    }
    func AstNode.handleGoImportScript(visitor: Resolver, script: Script, unit: CodeUnit, sfun: GoImportScript) {
        Log.event("AstNode.handleGoImportScript", script.caller, script.args, unit.name)
        do match {
            case AstNode:
                do assert false, "AstNode.handleGoImportScript", script.args
            case StringEvaluation:
                if script.args.size() == 1 {
                    // do assert false, "invalid literal.value type and argument count", literal.value
                    sfun.importPackage(visitor, unit, literal.value.split("/"))
                } elseif script.args.size() == 2 {
                    script.args[1].handleGoImportClasses(visitor, script, unit, sfun, literal.value.split("/"))
                } else {
                    do assert false, "StringEvaluation.handleGoImportScript invalid args", script.args
                }
            case ListLiteral:
                for name in values {
                    var nameliteral = name as StringEvaluation
                    if nameliteral != nil {
                        sfun.importPackage(visitor, unit, nameliteral.literal.value.split("/"))
                    }
                }
        }
    }
    func AstNode.handleGoImportClasses(visitor: Resolver, script: Script, unit: CodeUnit, sfun: GoImportScript, pkgpath: [string]) {
        Log.event("AstNode.handleGoImportClasses", script.caller, script.args, unit.name, pkgpath)
        do match {
            case AstNode:
                do assert false, "AstNode.handleGoImportClasses", toString(), script.args
            case Identifier:
                sfun.importClass(visitor, unit, pkgpath, name)
            case ListLiteral:
                for identifier in values {
                    var nameid = identifier as Identifier
                    if nameid != nil {
                        sfun.importClass(visitor, unit, pkgpath, nameid.name)
                    }
                }
        }
    }

    func importPackage(visitor: Resolver, unit: CodeUnit, pkgpath: [string]) {
        Log.event("GoImportScript.importPackage", pkgpath)
        var gopkg = GoLibLoader.instance().loadPackage(visitor, pkgpath)
        Log.event("GoImportScript.importPackage add package to unit", gopkg, unit, gopkg.path, unit.name)
        unit.addSymbol(pkgpath[-1], gopkg)
    }
    func importClass(visitor: Resolver, unit: CodeUnit, pkgpath: [string], name: string) {
        Log.event("GoImportScript.importClass", pkgpath, name)
        var cls = GoLibLoader.instance().loadClass(visitor, pkgpath, name)
        unit.addSymbol(name, cls)
    }
    func resolveScript(visitor: Resolver, script: Script) {
        var unit = script.getCodeUnit()
        Log.event("GoImportScript.resolve", visitor, script, script.caller.fullpath, script.args, unit.name)
        script.args[0].handleGoImportScript(visitor, script, unit, this)
    }
    func deepAnalyzeScript(visitor: DeepAnalyzer, script: Script) {
        var unit = script.getCodeUnit()
        Log.event("GoImportScript.deepAnalyzer", visitor, script, script.caller.fullpath, script.args, unit.name)
        script.args[0].addGoDep(unit)
    }
    func AstNode.addGoDep(unit: CodeUnit) => void {
        do match {
            case AstNode:
                do assert false, "AstNode.addGoDep", toString()
            case StringEvaluation:
                if literal.value != "builtin" {
                    unit.handler.addDep(literal.value)
                }
            case ListLiteral:
                values.each({$0.addGoDep(unit)})
        }
    }
    func formatScript(visitor: AstFormatter, script: Script) {

    }
}

func loadAllScripts(pkg: Package) {
    pkg.addSymbol("import", GoImportScript())
}
