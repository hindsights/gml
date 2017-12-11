package gml

import sys (Path, System)
import sys.Strings
import sys.util (SimpleProgramOptions)
import sys (FileSystem, FileInfo, Logging, Logger, Console)
import sys (File, StructuredWriter, createXmlWriter, Reader, Writer)
import gml.grammar (GmlLexer, GmlParser)


//var g_translationUnit: CodeUnit

class Compiler
{

}

class GeneratorConfig {
    var outputDir: string
}

var testabc: string = "hello"

class CodeUnitParser {
    @static_method
    func parseFile(filename: string) => GmlParser {
        println("parseFile", filename)
        var fin = File.createReader(filename)
        var lex = GmlLexer(fin)
        //lex.setFilename(filename)
        var parser = GmlParser(lex)
        //parser.setFilename(filename)
        parser.parse()
        return parser
    }

    @static_method
    func parseString(s: string) => GmlParser {
        var sin = Strings.createReader(s)
        var lex = GmlLexer(sin)
        var parser = GmlParser(lex)
        parser.parse()
        return parser
    }

    @static_method
    func parseVar(s: string) => SingleVarDef {
        var sin = Strings.createReader(s)
        var lex = GmlLexer(sin)
        var parser = GmlParser(lex)
        return parser.parseVar()
    }

    @static_method
    func parseFuncProto(s: string) => FuncProto {
        println("CodeUnitParser.parseFuncProto", s)
        var sin = Strings.createReader(s)
        var lex = GmlLexer(sin)
        var parser = GmlParser(lex)
        return parser.parseFuncProto()
    }
}

func globFiles(dir: string, matcher: func (string) => bool) => [string] {
    println("globFiles: start", dir)
    var files: [string]
    if not dir.empty() {
        FileSystem.walk(dir, {
            var filepath = $0
            var fileinfo = $1
            var name = Path.getFileName(filepath)
            println("globFiles item:", filepath, fileinfo, fileinfo.isDir())
            if fileinfo.isDir() {
                println("globFiles: search dir", filepath)
                files.extend(globFiles(filepath, matcher))
            } else {
                println("globFiles: check file", filepath, name)
                if matcher(name) {
                    println("globFiles: add file", filepath, name)
                    files.append(filepath)
                }
            }
        })
    }
    println("globFiles: end", dir, files)
    return files
}

func runMain(args: [string]) {
	println("gml compiler args", args.size(), args)
    Console.println("gml start", args)
    var logger = Logging.getLogger("gml")
    Logging.initLogging(Logging.WARNING)
    Console.println("gml log", args)
    logger.event("hello", "test", args)
    Log.event("run gml", args)
    var testvars : string[2]
    testvars[0] = "1"
    testvars[1] = "2"
    var i = 0
    for arg in args {
        println("gml compiler arg", i, arg)
        i += 1
    }
    var opts = SimpleProgramOptions()
    opts.loadStrings(args[1:])
    var libdirs = opts.getOption("-l", "").split(':')
    var outdir = opts.getOption("-o", ".")
    var indir = opts.getOption("-i", "")
    println("gml indir=", indir)
    println("gml compiler:", "outdir=", outdir, "indir=", indir, indir.size(), "libdirs=", libdirs, "files=", opts.getFiles())
    if indir.size() > 0 {
    }
    var libfiles = [globFiles(libdir, {return $0.endsWith(".gml")}) for libdir in libdirs].flatten()
    println("libfiles:", libfiles, libdirs)
    LangManager.instance().load()
    var targetModule = LangManager.instance().findModule("go")
    targetModule.init()
    var lib = Library()
    var proj = Project()
    proj.targetModule = targetModule
    proj.rootPackage = lib.rootPackage
    proj.lib = lib
    proj.rootPackage.setOwner(proj)
    // proj.setOwner(proj.rootPackage)
    proj.libUnits = targetModule.loadLibrary(proj)
    proj.loadScripts()
    for unit in proj.libUnits {
        unit.setOwner(proj)
        unit.init(proj.rootPackage)
    }

    var units: [CodeUnit]
    var allfiles = opts.getFiles() + libfiles
    println("all gml files", opts.getFiles(), libfiles, allfiles)
    for srcfile in allfiles {
        println("parse file", srcfile)
        var parser = CodeUnitParser.parseFile(srcfile)
        //var parser1 = CodeUnitParser.parseFile srcfile
        var unit = parser.getCodeUnit()
        do assert unit, "unit is nil"
        unit.project = proj
        unit.name = Path.getBaseName(srcfile)
        do assert unit.name != "path", unit, srcfile
        unit.sourceFilePath = srcfile
        unit.init(proj.rootPackage)
        // unit.setOwner(proj)
        units.append(unit)
    }
    println("all units:", units)
    var nameCacher = NameCacher(project=proj)
    var visitors: [AstVisitor]
    var preVisitors: [AstVisitor] = [OwnerInitializer(project=proj), PreTransformer(project=proj), Preprocessor(project=proj)]
    var analyzeVisitors: [AstVisitor] = [nameCacher,
        Resolver(project=proj, level=1), ScriptProcessor(project = proj), Resolver(project=proj, level=2)]
    visitors.extend(preVisitors)
    visitors.extend(targetModule.createPreVisitors(proj))
    visitors.extend(analyzeVisitors)
    //visitors.append(PreTransformer(project = proj))
    visitors.extend(targetModule.createVisitors(proj))
    proj.visitors[0] = []
    for visitor in visitors {
        println("visit translation unit", visitor, proj.targetModule)
        visitor.targetModule = proj.targetModule
        visitor.project = proj
        // proj.targetModule.visitInternalLibs(visitor)
        if visitor == nameCacher {
            // proj.targetModule.loadPreludes()
        }
        // visitor.visit(proj.lib)
        proj.visitors[0].append(visitor)
    }
    proj.visitors[0] = []
    for visitor in visitors {
        println("visit code unit", visitor, units)
        // proj.targetModule.visitExternalLibs(visitor)
        for unit in proj.libUnits[:] {
            do assert unit, "visit lib unit"
            var startTime = System.getEpochSecond()
            visitor.visit(unit)
            println("visit lib unit", unit.name, unit.pkg, visitor.getClassName(), System.getEpochSecond() - startTime)
        }
        if visitor == nameCacher {
            proj.targetModule.loadPreludes()
            lib.loadInternalLibs(proj)
        }
        for unit in units {
            var startTime = System.getEpochSecond()
            visitor.visit(unit)
            println("visit code unit", unit.name, unit.scripts, visitor.getClassName(), System.getEpochSecond() - startTime)
        }
        proj.visitors[0].append(visitor)
    }
    var config = GeneratorConfig()
    config.outputDir = outdir
    var generator = proj.targetModule.createGenerator(config)
    for unit in units {
        generator.visit(unit)
        println("visit generator unit", unit.name)
    }
}
