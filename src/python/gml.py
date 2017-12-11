import sys
import lex
from resolver import Resolver
from resolver import TypeMatcher
import re
import xutils
from xutils import Table, printException, initLogging, createLogger
from parser import codeparser
import os.path
from preprocessor import ScriptProcessor, PreExpander, OwnerInitializer
from preprocessor import NameCacher, NameResolver
from interpreter import Interpreter
import ast
import os
import scripts
import libs
import logging
import time

class ProjectConfig(object):
    def __init__(self):
        self.default_storage = 'ref'

class Project(ast.AstNode, ast.AstBlockContext):
    def __init__(self):
        print('Project.init', ast.formatId(self))
        ast.AstNode.__init__(self)
        ast.AstBlockContext.__init__(self)
        self.dep_types = {}
        self.pkg = ast.Package.getRoot()
        self.pkg.setOwner(self)
        self.config = ProjectConfig()
        self.scripts = {}
        self.visitorStack = [[]]
    def setupNewItem(self, item, owneritem, currentVisitor):
        assert item != None, ("Project.setupNewItem", item, owneritem, currentVisitor)
        if owneritem != None:
            item.setOwner(owneritem)
        self.visitNewItem(item, currentVisitor)
    def visitNewItem(self, item, currentVisitor=None):
        latestVisitors = self.visitorStack[0]
        self.visitorStack.insert(0, [])
        for visitor in latestVisitors:
            item.visit(visitor)
            self.visitorStack[0].append(visitor)
        if currentVisitor != None:
            item.visit(currentVisitor)
        del self.visitorStack[0]
    def loadLib(self):
        scripts.loadScripts(self)
        self.libUnits = libs.loadAll(self)
    def findScript(self, path):
        item = self.scripts
        for p in path:
            item = item[p]
        assert(item)
        return item
    def getPackage(self, path):
        return self.pkg.getPackage(path)
    def loadPackageToPrelude(self, preludepkg, pkg):
        pkg.eachSymbol(lambda k, v: preludepkg.addSymbol(v))
    def loadSymbolToPrelude(self, preludepkg, path):
        symbol = self.pkg.resolveSymbol(path.split('.'))
        assert symbol, ('loadSymbolToPrelude', preludepkg, path, symbol)
        preludepkg.addSymbol(symbol)
    def initPrelude(self):
        pkg = self.pkg.getPackage('sys.prelude')
        for p in ['sys.Console.println', 'sys.Console.print', 'sys.Console.printf']:
            self.loadSymbolToPrelude(pkg, p)
        self.loadPackageToPrelude(pkg, self.pkg.getPackage('sys.lang'))
    def loadPrelude(self):
        pkg = self.pkg.getPackage('sys.prelude')
        print('Project.loadPrelude', pkg)
        pkg.eachSymbol(lambda k, v: self.addSymbol(v))
        print('Project.loadPrelude ok', pkg, self.symbols)

def process(opts):
    print('start with files', opts.filename)
    project = Project()
    project.loadLib()
    project.opts = opts
    codeunits = []
    gmlparser = codeparser
    print('opts.gmllib', opts.gmllib)
    typeMatcher = TypeMatcher()
    astInterpreter =  Interpreter()
    astInterpreter.project = project
    visitors = []
    visitors.append(OwnerInitializer())
    visitors.append(PreExpander())
    visitors += [NameCacher(), NameResolver(), ScriptProcessor(), Resolver()]
    for filename in opts.filename:
        print('try parse file', filename)
        codeunit = Table()
        codeunits.append(codeunit)
        codeunit.filename = filename
        codeunit.parser = gmlparser
        print('codeunit parse', filename, codeunit.filename)
        ast = codeunit.parser.parse(open(filename).read(), filename)
        print('codeunit parse ok', filename, ast)
        ast.pkg = project.getPackage(ast.packageDef.path)
        ast.lib = None
        ast.project = project
        ast.basename = os.path.splitext(os.path.basename(filename))[0]
        ast.filename = filename
        ast.name = ast.basename
        assert ast.name, filename
        codeunit.name = ast.basename
        codeunit.ast = ast
        setattr(codeunit.ast, typeMatcher.name, typeMatcher)
        codeunit.ast.visitors = []
        astDir = os.path.join(opts.outputdir, *ast.packageDef.path) if ast.packageDef.path else opts.outputdir
        codeunit.ast.package_directory = astDir
        codeunit.ast.package_path = '/'.join(codeunit.ast.packageDef.path)
        # print('codeunit astDir=%s' % astDir, ast.pkg.path, ast.name)
        if not os.path.exists(astDir):
            os.makedirs(astDir)
        codeunit.ast.setOwner(codeunit.ast.pkg)
    for unit in project.libUnits:
        unit.project = project
        unit.pkg = project.getPackage(unit.packageDef.path)
        unit.setOwner(unit.pkg)
    project.visitorStack[0] = []
    i = 0
    analyzeStartTime = time.time()
    for i in range(len(visitors)):
        visitor = visitors[i]
        j = 0
        visitor.project = project
        for unit in project.libUnits:
            startTime = time.time()
            visitor.visit(unit)
            usedTime = time.time() - startTime
            print('visit lib unit ok', unit.name, usedTime, unit)
        for codeunit in codeunits:
            j += 1
            # print('visit ast', visitor.name, codeunit.ast.name, codeunit.ast.filename, i, j, codeunit.name)
            assert(codeunit.ast.filename == codeunit.filename)
            assert(codeunit.ast.name == codeunit.name)
            startTime = time.time()
            visitor.visit(codeunit.ast)
            usedTime = time.time() - startTime
            print('visit code unit ok', codeunit.ast.name, usedTime, codeunit.ast)
            # print('visit ast ok.', codeunit.ast.name, codeunit.ast.filename, visitor, codeunit, i, j, codeunit.name, codeunit, codeunit.ast)
            assert(codeunit.ast.filename == codeunit.filename)
            assert(codeunit.ast.name == codeunit.name)
            astfilename = os.path.join(codeunit.ast.package_directory, '%s.%s.txt' % (codeunit.ast.name, visitor.opname))
            # print('open file astfilename', astfilename, codeunit.ast.package_directory, codeunit.ast.name)
        if visitor.opname == 'cacheName':
            project.initPrelude()
            project.loadPrelude()
        project.visitorStack[0].append(visitor)
    print('analyze ok', time.time() - analyzeStartTime)
    if opts.interpreter:
        evalStartTime = time.time()
        astInterpreter.evaluateGlobalVar(codeunits)
        ret = astInterpreter.execute('gml.runMain'.split('.'), sys.argv[:])
        print('evaluate ok', time.time() - evalStartTime)
        return ret
    return True

def globExtRecursively(rootdir, ext):
    # print('globExtRecursively', rootdir, ext)
    allfiles = os.listdir(rootdir)
    files = []
    for filename in allfiles:
        filepath = os.path.join(rootdir, filename)
        if os.path.isdir(filepath):
            files.extend(globExtRecursively(filepath, ext))
        else:
            assert os.path.isfile(filepath)
            if filename.endswith(ext):
                files.append(filepath)
    return files


def getConfig():
    rootdir = os.path.dirname(__file__)
    config = Table()
    config.classpath = os.path.join(rootdir, '../gml')
    # config.libpath = os.path.join(rootdir, 'cpp/lib')
    config.gmllib = os.path.join(rootdir, '../libs/gml')
    config.filename = globExtRecursively(config.classpath, '.gml')
    config.gmllibfiles = globExtRecursively(config.gmllib, '.gml')
    config.lib_files = []
    config.outputdir = '/tmp'
    config.interpreter = True
    config.filename += config.gmllibfiles
    print 'getConfig: files:', config.filename
    print 'getConfig: libs:', config.lib_files
    print 'getConfig: gmllibs:', config.gmllibfiles
    return config

def tryRunMain():
    print('run gml', sys.argv, __file__)
    sys.setrecursionlimit(10000)
    opts = getConfig()
    ret = process(opts)
    print('run gml end.', ret)
    if isinstance(ret, Exception):
        xutils.saySomething('exception')
    else:
        xutils.saySomething('succeeded')

def runMain():
    initLogging(logging.WARNING)
    gmllogger = createLogger('gml')
    gmllogger.info('gml started')
    try:
        ret = tryRunMain()
    except Exception as e:
        print('run_main error:', e)
        printException(e, None)
        xutils.saySomething('failed')
    print('run gml end2.')

if __name__ == '__main__':
    if 0:
        import cProfile
        cProfile.run('runMain()', 'gml.pyprof')
    else:
        runMain()

