package gml

import sys.StructuredWriter

@mixin(AstBlockContext, context, getContext, node=this)
class Project: AstNode
{
    var rootPackage: Package
    var scriptPackage = createRootPackage()
    var lib: Library
    var targetModule: LangModule
    var visitors: [[AstVisitor]] = [[]]
    var libUnits: [CodeUnit]

    func setupNewItem(item: AstNode, owner: AstNode, currentVisitor: AstVisitor) {
        do assert item != nil, "Project.setupNewItem", item, owner, currentVisitor
        // Log.debug("setupNewItem start", item, owner, visitors.size(), visitors[0].size())
        // Log.debug("setupNewItem", item, owner, currentVisitor)
        if owner != nil {
            item.setOwner(owner)
            item.initializeOwner()
        }
        var latestVisitors = visitors[0]
        //var emptyVisitors : [AstVisitor]
        visitors.insert(0, [])
        for visitor in latestVisitors {
            // Log.debug("setupNewItem visit", item, owner, visitor)
            item.visit(visitor)
            visitors[0].append(visitor)
        }
        if currentVisitor != nil {
            // Log.debug("setupNewItem current", item, owner, currentVisitor)
            item.visit(currentVisitor)
        }
        visitors.removeAt(0)
    }
    func loadScripts() {
        targetModule.loadScripts(scriptPackage.getPackage("go"))
    }
    func findScript(path: [string]) => ScriptFunc {
        return scriptPackage.resolveSymbol(path) as ScriptFunc
    }
}

class Import(fullpath: string, path: [string], names: [string]): SimpleNode {
    var target: AstNode
    func unfold() => [Import]
    {
        if names.empty() {
            return [this]
        }
        //Log.debug("Import.unfold", path.full, names.size())
        var imports = [createImport(fullpath + "." + name, []) for name in names]
        return imports
    }
    func toString() => string = "Import:%s:%s" % (fullpath, formatId())
}


class PackageDef(path: [string], fullpath: string): SimpleNode
{
}

@mixin(AstBlockContext, context, getContext, node=this)
class Package(path: [string], fullpath: string): AstNode
{
    var packages: { string: Package }

    func toString = "Package:%s:0x%08x" % (fullpath, this)
    func visitChildren(visitor: AstVisitor)
    {
        // Log.debug("Package.visitChildren", fullpath, packages.size())
        for name, node in context.symbols {
            node.visit(visitor)
        }
    }
    func initializeOwner() {
        for name, node in context.symbols {
            node.setOwner(this)
            node.initializeOwner()
        }
    }

    func findMember(symbolname: string) => AstNode {
        // Log.debug("findMember", symbolname, toString())
        return findLocalSymbol(symbolname)
    }
    func getPackage(pathstr: string) => Package
    {
        // Log.debug("Package.getPackage", pathstr, fullpath)
        do assert pathstr.size() > 0, ("Package.getPackage", pathstr, fullpath)
        var pathlist = pathstr.split(".")
        return getPackageByList(pathlist)
    }
    func getPackageByList(pathlist: [string]) => Package
    {
        if pathlist.empty() {
            // Log.debug("getPackageByList this", toString(), this)
            return this
        }
        var p = pathlist[0]
        do assert p.size() > 0
        if p in packages {
            return packages.get(p).getPackageByList(pathlist[1:])
        }
        var pkg = createPackage(p if fullpath.empty() else fullpath + "." + p, path + [p])
        do assert pkg, "getPackageByList: pkg is nil"
        packages[p] = pkg
        addSymbol(p, pkg)
        pkg.setOwner(this)
        Log.debug("Package.getPackageList create package", pkg.fullpath, fullpath, p, toString(), pkg)
        return pkg.getPackageByList(pathlist[1:])
    }
    func formatPrefix() => string {
        return " ".join(["namespace " + p + " {" for p in path])
    }
    func formatSuffix() => string {
        return " ".join(["}" for p in path])
    }
}

class Library: SimpleNode
{
    var rootPackage = createRootPackage()

    func Library()
    {
    }

    func visitChildren(visitor: AstVisitor) {
    }
    func initializeOwner() {
        Log.debug("Library.initializeOwner")
    }

    func analyzeImport(imp: Import, unit: CodeUnit) {

    }

    func loadPrelude(proj: Project, fullpath: string) {
        var path = fullpath.split(".")
        var node = proj.rootPackage.resolveSymbol(path)
        Log.debug("loadPrelude", path[-1], node)
        proj.addSymbol(path[-1], node)
    }
    func addFunc(rootpkg: Package, f: LibFunc) {
        var pkg = rootpkg.getPackage(f.pkg)
        Log.debug("Library.addFunc", rootpkg, f)
        pkg.addSymbol(f.name, f)
    }
    func loadLibs(dirpath: [string]) {
        Log.debug("loadLibs", dirpath.size(), dirpath[0])
        return
    }
    func loadInternalLibs(proj: Project) {
        Log.debug("loadInternalLibs")
    }
}

@mixin(AstFullContext, context, getContext, node=this)
class CodeUnit(name: string, language: string, packageDef: PackageDef, scripts: [Script], imports: [Import], definitions: [Definition]): AstNode
{
    var sourceFilePath: string
    var project: Project
    var pkg: Package
    var handler: UnitHandler

    var typeRefs: {string: UserType}
    var headerDeps: {string}
    var sourceDeps: {string}

    var hasMain: bool = false

    func getHeaderPath() => string {
        return "\"" + "/".join(pkg.path + [name]) + ".hpp\""
    }

    func addSymbol(name: string, node: AstNode) {
        // Log.debug("CodeUnit.addSymbol", name, node, toString(), pkg, pkg.fullpath)
        context.addSymbol(name, node)
        pkg.addSymbol(name, node)
    }

    func init(rootpkg: Package) {
        Log.debug("CodeUnit.init name=", name, "pkgpath=", packageDef.path)
        pkg = rootpkg.getPackageByList(packageDef.path)
        //getContext().owner = pkg
        var items = [imp.unfold() for imp in imports].flatten()
        imports = items
        setOwner(pkg)
    }
    func addTypeRef(ut: UserType) {
        Log.debug("addTypeRef", ut.fullpath)
        do assert ut.fullpath != "StringTable"
        do assert not ut.fullpath.endsWith("StringTable")
        do assert not ut.fullpath.endsWith("string_table")
        typeRefs[ut.fullpath] = ut
    }
    func addHeaderDep(dep: string) {
        Log.debug("addHeaderDep", dep, getHeaderPath())
        if dep == getHeaderPath() {
            return
        }
        headerDeps.add(dep)
    }
    func addSourceDep(dep: string) {
        Log.debug("addSourceDep", dep)
        sourceDeps.add(dep)
    }
    func addHeaderDeps(deps: [string]) {
        Log.debug("addHeaderDeps", deps.size())
        deps.each({addHeaderDep($0)})
    }
    func addSourceDeps(deps: [string]) {
        Log.debug("addSourceDeps", deps.size())
        deps.each({sourceDeps.add($0)})
    }
}

func createImport(fullpath: string, names: [string]) => Import
{
    //Log.debug("createImport", (path as IdList).full)
    return Import(fullpath = fullpath, path = fullpath.split("."), names = names)
}

func createPackageDef(path: [string], fullpath: string) => PackageDef
{
    return PackageDef(path = path, fullpath = fullpath)
}

func createCodeUnit(name: string, language: string, packageDef: AstNode, scripts: [AstNode], imports: [AstNode], definitions: [AstNode]) => CodeUnit
{
    Log.debug("createCodeUnit", name, language, imports.size(), definitions.size(), scripts.size())
    do assert packageDef, "packageDef shouldn't be nil"
    do assert name != "path", "unit name shouldn't not be path"
    return CodeUnit(name = name, language = language, packageDef = (packageDef as PackageDef), imports = imports as [Import], definitions = definitions as [Definition], scripts = scripts as [Script])
    //Log.debug("createCodeUnit result", unit.imports.size(), unit.definitions.size())
    //return unit
}
