package gml

import gml.go.GoModule

class LangModule(name: string): SimpleNode {
	// func getPrimitiveTypeClass(name: string) => TypeClass {
	// 	return nil
	// }
	func init() {
	
	}

	func createClass(node: AstNode) => TypeClass {
        return nil
    }
    func createGenerator(config: GeneratorConfig) => AstVisitor {
        return nil
    }
    func createVisitors(project: Project) => [AstVisitor] {
        return []
    }
    func createPreVisitors(project: Project) => [AstVisitor] {
        return []
    }
    func loadLibrary(proj: Project) => [CodeUnit] {
    }
    func loadPreludes() {
    }
    func loadScripts(rootScriptPackage: Package) {
    }
    func createUserTypeClass(cls: ClassDef) => TypeClass {
        return nil
    }
    func visitInternalLibs(visitor: AstVisitor) {
    }
    func visitExternalLibs(visitor: AstVisitor) {
    }
	func createTypeClass(node: AstNode) => TypeClass = nil
    func getBinaryOpHandler(op: string) => BinaryOpHandler = nil
}

class UnitHandler: SimpleNode {
    func addDep(dep: string) {
    }
    func resolveUserType(visitor: AstVisitor, path: [string]) => AstNode {
        return nil
    }
}

@singleton
class LangManager {
    var modules: {string: LangModule}
    func LangManager() {
    }
    func load() {
        addModule(GoModule())
    }
    func addModule(module: LangModule) {
        do assert module.name not in modules, ("LangManager.addModule duplicate", module.name)
        Log.debug("LangManager.addModule", module.name, module)
        modules[module.name] = module
    }
    func findModule(name: string) => LangModule {
        return modules.get(name)
    }
}
