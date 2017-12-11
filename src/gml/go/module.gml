package gml.go

import gml.go.libs.loadLib
import gml.go.scripts.loadAllScripts
import sys.go.GoDoc

class Storage {
    func formatParamUserType(formatter: AstFormatter, t: UserType) => string = t.fullpath
}

class ValueStorage : Storage {
}

class RefStorage : Storage {
    func formatParamUserType(formatter: AstFormatter, t: UserType) => string = "*" + t.fullpath
}

class InterfaceStorage : Storage {
}

@singleton
class StorageFactory {
    var storages: {string: Storage}
    var valueStorage: Storage
    var refStorage: Storage

    func StorageFactory() {
        valueStorage = ValueStorage()
        refStorage = RefStorage()
        storages["value"] = valueStorage
        storages["ref"] = refStorage
        storages["interface"] = InterfaceStorage()
    }
    func get(name: string) => Storage {
        return storages.get(name, refStorage)
    }
}

class UserTypeClass : TypeClass {
	var cls: ClassDef
    var storage: Storage
    func resolve(visitor: Resolver) {
    }
	func resolveAttr(attr: AttrRef) = cls.resolveAttr(attr)
    func createDefaultValue() => Expression {
        return Nil()
    }
}

class GoUnitHandler : UnitHandler {
    var unit: AstNode
    var deps: {string}
    func addDep(dep: string) {
        deps.add(dep)
    }
    func resolveUserType(visitor: AstVisitor, path: [string]) => AstNode {
        // do assert false, "GoUnitHandler.resolveUserType", path
        // Log.event("GoUnitHandler.resolveUserType", path, unit, deps)
        if path.size() <= 1 {
            return nil
        }
        var pkgpath = path[:-1]
        var pkgstr = ".".join(pkgpath)
        addDep(pkgstr)
        var pkg = GoLibLoader.instance().loadPackage(visitor, pkgpath)
        var symbol = pkg.resolveTypeSymbol(path[1:])
        // Log.event("GoUnitHandler.resolveUserType ok", path, unit, deps, pkgstr, pkg, symbol)
        return symbol
    }
}

// dyanmic go lib loader
@singleton
@mixin(AstBlockContext, context, getContext, node=this)
class GoLibLoader : SimpleNode {
    var project : Project
    // var units: [LibUnit]

    func init(proj: Project) {
        project = proj
    }

    func loadClass(visitor: AstVisitor, pkgpath: [string], name: string) => AstNode {
        Log.event("GoLibLoader.loadClass", pkgpath, name)
        var pkg = loadPackage(visitor, pkgpath)
        var symbol = pkg.findLocalSymbol(name)
        return symbol
    }
    func loadPackage(visitor: AstVisitor, pkgpath: [string]) => Package {
        Log.event("GoLibLoader.loadPackage", pkgpath, project.libUnits.size())
        var pkg = project.rootPackage.resolveSymbol(pkgpath) as Package
        if pkg != nil {
            return pkg
        }
        // generate a temporary CodeUnit, analyze it, then discard it
        var unit = GoDoc.getPackageInfo(pkgpath)
        unit.init(project.rootPackage)
        Log.event("GoLibLoader.loadPackage add", pkgpath, unit, unit.definitions.size())
        visitor.setupNewItem(unit, project, true)
        // do assert unit.name not in units
        project.libUnits.append(unit)
        return unit.pkg
    }
}

class GoModule : LangModule {
    var project: Project
    var goBuiltinUnit: CodeUnit
    var goLibLoader: GoLibLoader
    var libUnits: [CodeUnit]

    func GoModule() {
        name = "go"
        goLibLoader = GoLibLoader.instance()
    }

    func init() {
        PrimitiveTypeClassFactory.instance().init()
    }

    func createGenerator(config: GeneratorConfig) => AstVisitor {
        return Generator(config=config)
    }
    func createVisitors(project: Project) => [AstVisitor] {
        return [DeepAnalyzer(project=project), DeepTransformer(project=project)]
    }
    func createPreVisitors(project: Project) => [AstVisitor] {
        return [GoPreVisitor(project=project), GoPreTransformer(project=project)]
    }

    func loadGoBuiltin() {
        var clsError = ClassDef(name="error", bases=[], definitions=[#{func Error() => string}])
        clsError.typeClass = UserTypeClass(cls=clsError, storage=StorageFactory.instance().get("interface"))
        var defs : [Definition] = [clsError]
        var unit = createLibUnit("builtin", defs)
        unit.init(project.rootPackage)
        unit.setOwner(project)
        Log.event("GoLibLoader.loadBuiltin", unit)
        goBuiltinUnit = unit
        return unit
    }

    func loadLibrary(proj: Project) => [CodeUnit] {
        project = proj
        goLibLoader.init(proj)
        libUnits.extend(loadTypes())
        libUnits.extend(loadLib())
        var builtinUnit = loadGoBuiltin()
        libUnits.append(builtinUnit)
        for unit in libUnits {
            Log.event("loadLibrary", unit)
            do assert unit, "loadLibrary unit"
        }
        return libUnits
    }
    func addFunc(rootpkg: Package, f: LibFunc) {
        var pkg = rootpkg.getPackage(f.pkg)
        Log.event("GoModule.addFunc", rootpkg, f)
        pkg.addSymbol(f.name, f)
    }
    func loadPreludes() {
        loadPrelude(project, "sys.println")
        Log.event("GoModule.loadBuiltin", goBuiltinUnit)
        goBuiltinUnit.pkg.eachSymbol({
            project.addSymbol($0, $1)
            // Log.event("GoModule.loadPreludes add", $0, $1)
        })
        var langpkg = project.rootPackage.getPackage("sys.lang")
        langpkg.eachSymbol({
            project.addSymbol($0, $1)
            // Log.event("GoModule.loadPreludes lang", $0, $1, project)
        })
        var builtinpkg = project.rootPackage.getPackage("sys.builtin")
        builtinpkg.eachSymbol({
            project.addSymbol($0, $1)
            // Log.event("GoModule.loadPreludes builtin", $0, $1, project)
        })
    }
    func loadPrelude(proj: Project, fullpath: string) {
        var path = fullpath.split(".")
        var node = proj.rootPackage.resolveSymbol(path)
        Log.event("loadPrelude", path[-1], node)
        proj.addSymbol(path[-1], node)
    }
    func loadScripts(rootScriptPackage: Package) {
        loadAllScripts(rootScriptPackage)
    }
    func createUserTypeClass(cls: ClassDef) => TypeClass {
        return UserTypeClass(cls=cls)
    }
    func initializeOwner() {
        Log.event("GoModule.initializeOwner")
        do assert false
        goBuiltinUnit.initializeOwner()
    }
    func cacheName(visitor: NameCacher) {
        Log.event("GoModule.cacheName")
        do assert false
        visitChildren(visitor)
        loadPreludes()
    }
    func visitInternalLibs(visitor: AstVisitor) {
        goBuiltinUnit.visit(visitor)
    }
    func visitExternalLibs(visitor: AstVisitor) {
        if visitor.getClassName() == "DeepTransformer" {
            return
        }
        // goLibLoader.visit(visitor)
    }
	func createTypeClass(node: AstNode) => TypeClass {
        return Types.createTypeClass(node, this)
    }
    func getBinaryOpHandler(op: string) => BinaryOpHandler {
        return BinaryOpHandlerFactory.instance().get(op)
    }
}
