
from basetype import BuiltinTypeClass, LibLiteral, LibClass, LibFunc, LibVar, makeFuncSpec
import builtins
import operator
import xutils
import ast
import os
import sys
import os.path
import yaml
import logging
from cStringIO import StringIO
import parser
import goparser
import lib
from itertools import chain
import time

prefix_tag_unit = 'ScriptUnit'
prefix_tag_class = 'ScriptClass'
prefix_tag_method = 'ScriptMethod'
prefix_tag_lazy_method = 'LazyScriptMethod'
prefix_tag_func = 'ScriptFunc'
prefix_tag_var = 'ScriptVar'
prefix_tag_const = 'ScriptConst'
prefix_tag_definitions = 'ScriptDefinitions'


class GmlAstConstructor(ast.AstVisitor):
    def __init__(self, interpreter, evalmode):
        ast.AstVisitor.__init__(self)
        # self.logger.debug('GmlAstConstructor.init', interpreter, evalmode)
        self.opname = 'constructAst'
        self.name = 'astConstructor'
        self.interpreter = interpreter
        self.evalmode = evalmode
    def visit(self, node):
        return self.constructAst(node)
    def constructAst(self, item):
        # self.logger.debug('constructAst', item)
        assert item is not None, ('GmlAstConstructor.constructAst', self, item)
        if item == self.interpreter.nilValue:
            return item
        if isinstance(item, list):
            return [self.constructAst(i) for i in item]
        if isinstance(item, ast.ExprEvaluation) and self.evalmode:
            # self.logger.debug('constructAst ExprEvaluation expr', item, item.expr, item.getOwner())
            exprval = item.expr.visit(self.interpreter)
            # self.logger.debug('constructAst ExprEvaluation', item, item.expr, exprval, item.getOwner(), item.getOwner().getOwner())
            return exprval
        if isinstance(item, xutils.EnumItem):
            ret = ast.AttrRef(ast.Identifier(item.enum.name), item.name)
            return item
        if not isinstance(item, ast.AstNode):
            # self.logger.debug('GmlAstConstructor ignore', item)
            return item
        clsname = type(item).__name__
        # self.logger.debug('constructAst cls', clsname, creatorname, item)
        cls = self.interpreter.project.pkg.getPackage('gml').findSymbol(clsname)
        assert cls is not None, (cls, clsname, item)
        args = []
        named_args = {}
        for var in cls.primaryVars:
            varname = var.name
            assert isinstance(varname, str), (cls, varname, cls.primaryVars)
            attr = getattr(item, varname, self.interpreter.nilValue)
            if attr is None:
                attr = self.interpreter.nilValue
            # assert attr is not None, (item, varname, item, attr)
            attrval = self.constructAst(attr)
            # self.logger.debug('constructAst class param getval', varname, var, attr, attrval)
            named_args[varname] = attrval
            # self.logger.debug('constructAst param', param.name, param, attrval, attr)
            # assert attr, (param.name, param, attr, clsvar, item)
        ret = self.interpreter.evalConstructor(cls, [], named_args, None)
        # self.logger.debug('constructAst create', clsname, item, type(item), cls, args, named_args, ret)
        return ret

class ScriptFunc(LibFunc):
    def __init__(self, protostr, evaluator=None, isstatic=False):
        LibFunc.__init__(self, None, protostr)
        self.evaluator = evaluator
        self.spec.static = isstatic
    def evaluateCall(self, visitor, callinfo):
        # visitor.logger.debug('ScriptFunc.evaluateCall', self.name, visitor, callinfo.args)
        args = [arg.evaluateParam(visitor) for arg in callinfo.args]
        if self.spec.static:
            # visitor.logger.debug('ScriptFunc.evaluateCall func args', self, visitor, args)
            return self.evaluator(visitor, *args)
        caller = callinfo.caller.object.visit(visitor)
        # visitor.logger.debug('ScriptFunc.evaluateCall method args', self, visitor, args)
        return self.evaluator(caller, *args)

class ScriptVar(LibVar):
    def __init__(self, name, t):
        LibVar.__init__(self)
        self.name = name
        self.type = t
        self.astFieldNames = []


class ScriptClass(LibClass):
    def __init__(self, name, impl, evaluator=None):
        LibClass.__init__(self, name)
        self.returnType = ast.UserType([self.name])
        self.spec = makeFuncSpec(self.returnType, [])
        self.evaluator = evaluator
        self.impl = impl
    def getItemType(self):
        return self.impl.getItemType()
    def getKeyType(self):
        return self.impl.getKeyType()
    def getValueType(self):
        return self.impl.getValueType()
    def addFunctions(self):
        pass
    def transformUserType(self, transformer, ut):
        pass
    def evaluateBinaryOp(self, visitor, opstr, left, right):
        self.impl.evaluateBinaryOp(visitor, opstr, left, right)
    def evaluateCall(self, visitor, callinfo):
        # visitor.logger.debug('ScriptClass.evaluateCall', self, visitor, callinfo, self.impl, callinfo.args)
        if not self.impl:
            return self.evaluator(visitor, callinfo)
        args = [arg.evaluateParam(visitor) for arg in callinfo.args]
        # visitor.logger.debug('ScriptClass.evaluateCall args', self, visitor, self.impl, args)
        ret = self.impl(*args)
        ret.ast_interpreter = visitor
        return ret
    def evaluateNil(self, visitor):
        return visitor.nilValue

def loadUnits(proj, scope):
    units = []
    for name, item in scope.iteritems():
        parts = name.split('_')
        # print('loadUnits', name, item, parts)
        if len(parts) < 2:
            continue
        prefix_tag = parts[0]
        if prefix_tag == prefix_tag_unit:
            pkgpath = parts[1:]
            unit = ast.createLibUnit('.'.join(pkgpath), [])
            defs = loadUnitItems(proj, item.__dict__)
            unit.definitions.extend(defs)
            # print('loadUnits unit', name, item, unit, defs)
            units.append(unit)
    return units

def loadUnitItems(proj, symbols):
    print('loadUnitItems', symbols)
    defs = []
    for name, item in symbols.iteritems():
        if name == prefix_tag_definitions:
            print('loadUnitItems definitions:', len(defs), name, item)
            defs.extend(item)
            continue
        parts = name.split('_', 1)
        if len(parts) != 2:
            continue
        prefix_tag = parts[0]
        childname = parts[1]
        defitem = loadUnitItem(proj, prefix_tag, childname, item)
        if defitem is not None:
            defs.append(defitem)
    # print('loadUnitItems', defs)
    return defs

def loadUnitItem(proj, tag, name, item):
    # print('loadUnitItem', tag, name, item, type(item))
    if tag == prefix_tag_class:
        # print('loadUnitItem class start', tag, name, item, type(item))
        if isinstance(item, BuiltinTypeClass):
            # print('loadUnitItem class with item', tag, name, item, type(item))
            return item
        cls = ScriptClass(name, item)
        item.scriptClass = cls
        defs = loadUnitItems(proj, item.__dict__)
        print('loadUnitItem class', tag, name, item, cls, defs)
        cls.definitions.extend(defs)
        return cls
    elif tag == prefix_tag_method:
        return ScriptFunc(item.__doc__, item, isstatic=False)
    elif tag == prefix_tag_func:
        return ScriptFunc(item.__doc__, item, isstatic=True)
    elif tag == prefix_tag_var:
        var = ScriptVar(name, item)
        return var
    elif tag == prefix_tag_const:
        return item
    else:
        pass
    return None

def loadAll(proj):
    # print('loadAll', rootpkg)
    return loadUnits(proj, globals()) + lib.loadAll()

builtinIntegerNames = ['int', 'long', 'uint', 'ulong', 'byte', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']

def createScriptObject(visitor, name, cls, args):
    return visitor.evalConstructor(ScriptClass(name, cls), args, {}, None)

class ScriptUnit_sys_lang(object):
    ScriptDefinitions = [
            LibLiteral('true', ast.makePrimitiveType('bool'), True),
            LibLiteral('false', ast.makePrimitiveType('bool'), False),
            builtins.StringClass(),
            builtins.CharClass(),
            builtins.BoolClass(),
            builtins.VoidClass(),

            builtins.GenericClass('Dict', builtins.GenericDictClassImpl),
            builtins.GenericClass('Set', builtins.GenericSetClassImpl),
            builtins.GenericClass('List', builtins.GenericListClassImpl),
            builtins.GenericClass('Array', builtins.GenericArrayClassImpl),
            builtins.GenericClass('Tuple', builtins.GenericTupleClassImpl),
            builtins.FloatingClass('float'),
            builtins.FloatingClass('double'),
            builtins.LogClass()
    ] + [builtins.IntegerClass(typename) for typename in builtinIntegerNames]
    class ScriptClass_builtins(object):
        ScriptDefinitions = [ast.builtinCharType,ast.builtinBoolType, ast.builtinStringType,
            ast.builtinIntType, ast.builtinLongType, ast.builtinFloatType]

class ScriptUnit_sys(object):
    class ScriptClass_System(object):
        def ScriptFunc_getEpochSecond(visitor):
            'getEpochSecond() => double'
            return time.time()
    class ScriptClass_Console(object):
        def ScriptFunc_println(visitor, *args):
            'println(string)'
            argstrs = [arg if isinstance(arg, str) else str(arg) for arg in args]
            print(' '.join(argstrs))
        def ScriptFunc_print(visitor, *args):
            'print(string)'
            argstrs = [arg if isinstance(arg, str) else str(arg) for arg in args]
            sys.stdout.write(' '.join(argstrs))
        def ScriptFunc_printf(visitor, formatstr, *args):
            'printf(string, string)'
            sys.stdout.write(formatstr % tuple(args))

    class ScriptClass_Logging(object):
        loggerLevel = logging.WARNING
        def ScriptFunc_initLogging(visitor, level):
            'initLogging(int)'
            ScriptUnit_sys.ScriptClass_Logging.loggerLevel = level
            # logging.basicConfig(level=level)
            logging.basicConfig(level=level, format='[%(name)s] %(message)s')
        def ScriptFunc_getLogger(visitor, name):
            'getLogger(string) => Logger'
            # return createScriptObject(visitor, 'Logger', ScriptUnit_sys.ScriptClass_Logger, [logging.getLogger(name)])
            return ScriptUnit_sys.ScriptClass_Logger(logging.getLogger(name))
        ScriptDefinitions = [LibLiteral('DEBUG', ast.makePrimitiveType('int'), logging.DEBUG),
            LibLiteral('INFO', ast.makePrimitiveType('int'), logging.INFO),
            LibLiteral('WARNING', ast.makePrimitiveType('int'), logging.WARNING),
            LibLiteral('EVENT', ast.makePrimitiveType('int'), logging.WARNING),
            LibLiteral('ERROR', ast.makePrimitiveType('int'), logging.ERROR),
            LibLiteral('CRITICAL', ast.makePrimitiveType('int'), logging.CRITICAL),
            LibLiteral('FATAL', ast.makePrimitiveType('int'), logging.CRITICAL)]
    class ScriptClass_Logger(object):
        def __init__(self, syslogger):
            self.syslogger = syslogger
        def log(self, level, *args):
            if level < ScriptUnit_sys.ScriptClass_Logging.loggerLevel:
                return
            # print('ScriptClass_Logger.log', level, ScriptUnit_sys.ScriptClass_Logging.loggerLevel)
            argstrs = [str(arg) for arg in args]
            self.syslogger.log(level, ' '.join(argstrs))
        def ScriptMethod_log(self, level, *args):
            'log(int, [AnyRef])'
            self.log(level, *args)
        def ScriptMethod_debug(self, *args):
            'debug([AnyRef])'
            self.log(logging.DEBUG, *args)
        def ScriptMethod_info(self, *args):
            'info([AnyRef])'
            self.log(logging.INFO, *args)
        def ScriptMethod_warn(self, *args):
            'warn([AnyRef])'
            self.log(logging.WARN, *args)
        def ScriptMethod_event(self, *args):
            'event([AnyRef])'
            self.log(logging.ERROR, *args)
        def ScriptMethod_error(self, *args):
            'error([AnyRef])'
            self.log(logging.ERROR, *args)
        def ScriptMethod_critical(self, *args):
            'critical([AnyRef])'
            self.log(logging.CRITICAL, *args)
        def ScriptMethod_fatal(self, *args):
            'fatal([AnyRef])'
            self.log(logging.CRITICAL, *args)
    class ScriptClass_Path(object):
        def ScriptFunc_combine(visitor, dirname, *names):
            'combine(string, string) => string'
            return os.path.join(dirname, *names)
        def ScriptFunc_join(visitor, *names):
            'join(string, string) => string'
            if len(names) == 1 and isinstance(names[0], list):
                return os.path.join(*names[0])
            return os.path.join(*names)
        def ScriptFunc_getExtension(visitor, path):
            'getExtension(string) => string'
            _, ext = os.path.splitext(path)
            return ext
        def ScriptFunc_getBaseName(visitor, path):
            'getBaseName(string) => string'
            filename = os.path.basename(path)
            basename, _ = os.path.splitext(filename)
            return basename
        def ScriptFunc_getFileName(visitor, path):
            'getFileName(string) => string'
            return os.path.basename(path)

    class ScriptClass_FileInfo(object):
        def __init__(self, dirname, name):
            self.dir = dirname
            self.name = name
            self.path = os.path.join(self.dir, self.name)
        def ScriptMethod_getName(self):
            'getName() => string'
            return self.name
        def ScriptMethod_getPath(self):
            'getPath() => string'
            return self.path
        def ScriptMethod_getDir(self):
            'getDir() => string'
            return self.dir
        def ScriptMethod_isFile(self):
            'isFile() => bool'
            return os.path.isfile(self.path)
        def ScriptMethod_isDir(self):
            'isDir() => bool'
            # print('ScriptMethod_isDir', self.path, os.path.isdir(self.path))
            return os.path.isdir(self.path)

    class ScriptClass_FileSystem(object):
        def ScriptFunc_ensureDirectoryExists(visitor, path):
            'ensureDirectoryExists(string) => bool'
            if os.path.isdir(path):
                return True
            try:
                return os.makedirs(path)
            except os.error, e:
                return False
        def ScriptFunc_walk(visitor, dir, walkfn):
            'walk(dir: string, walkfn: func (filepath: string, fileinfo: FileInfo))'
            # visitor.logger.debug('ScriptFunc_walk', dir, walkfn)
            items = os.listdir(dir)
            visitor.implicit_args_stack.insert(0, [])
            for item in items:
                # visitor.logger.debug('ScriptFunc_walk item', dir, item)
                visitor.pushScope()
                # fi = createScriptObject(visitor, 'FileInfo', ScriptUnit_sys.ScriptClass_FileInfo, [dir, item])
                fi = ScriptUnit_sys.ScriptClass_FileInfo(dir, item)
                visitor.implicit_args_stack[0] = [fi.path, fi]
                walkfn.visit(visitor)
                visitor.popScope()
            del visitor.implicit_args_stack[0]

    class ScriptClass_Env(object):
        def ScriptFunc_get(visitor, name):
            'get(string) => string'
            return os.getenv(name)

    class ScriptClass_Strings(object):
        def ScriptFunc_createReader(visitor, s):
            'createReader(string) => sys.Reader'
            # return createScriptObject(visitor, 'StringReaer', ScriptUnit_sys.ScriptClass_StringReader, [s])
            return ScriptUnit_sys.ScriptClass_StringReader(s)
        def ScriptFunc_createWriter(visitor, path):
            'createWriter() => sys.StringWriter'
            # return createScriptObject(visitor, 'StringWriter', ScriptUnit_sys.ScriptClass_StringWriter, [])
            return ScriptUnit_sys.ScriptClass_StringWriter()

    class ScriptClass_YamlElement(object):
        def __init__(self, d=None):
            # assert d is None or isinstance(d, dict) or isinstance(d, list), d
            self.data = d
        def ScriptMethod_load(self, filepath):
            'load(string) => bool'
            self.data = yaml.load(open(filepath))
            return self.data is not None
        def ScriptMethod_getString(self, name, defval=''):
            'getString(string, string) => string'
            # print('ScriptMethod_getString', self, name, defval)
            assert self.data is None or isinstance(self.data, dict), (self, name, defval)
            return self.data.get(name, defval)
        def ScriptMethod_getNamedItem(self, name):
            'getNamedItem(string) => YamlElement'
            assert self.data is None or isinstance(self.data, dict)
            itemdata = self.data.get(name, None)
            # if isinstance(itemdata, dict) or isinstance(itemdata, list):
            # return createScriptObject('YamlElement', ScriptUnit_sys.ScriptClass_YamlElement, [itemdata])
            return ScriptUnit_sys.ScriptClass_YamlElement(itemdata)
        def ScriptMethod_getItem(self, seq):
            'getItem(int) => YamlElement'
            assert self.data is None or (isinstance(self.data, list) and seq < len(self.data)), (self, self.data, seq)
            itemdata = self.data[seq]
            # if isinstance(itemdata, dict) or isinstance(itemdata, list):
            # return createScriptObject('YamlElement', ScriptUnit_sys.ScriptClass_YamlElement, [itemdata])
            return ScriptUnit_sys.ScriptClass_YamlElement(itemdata)
        def ScriptMethod_isValid(self):
            'isValid() => bool'
            return self.data is not None
        def ScriptMethod_getSize(self):
            'getSize() => int'
            assert self.data is None or isinstance(self.data, list)
            return len(self.data)
        def ScriptMethod_getText(self, defval=''):
            'getText(string) => string'
            assert self.data is None or isinstance(self.data, str)
            return self.data if self.data else defval

    class ScriptClass_File(object):
        def __init__(self, fp):
            self.istream = fp
        def ScriptMethod_close(self):
            'close()'
            if self.istream:
                self.istream.flush()
                self.istream.close()
            self.istream = None
        def ScriptMethod_openText(self, filepath):
            'openText(string) => bool'
            # print('ScriptMethod_openText', filepath, os.getcwd())
            self.istream = open(filepath, 'w')
            assert self.istream
            return self.istream is not None
        def ScriptMethod_write(self, s):
            'write([byte]) => int'
            # print('ScriptMethod_write', s)
            # assert False
            self.istream.write(s)
            self.istream.flush()
            return len(s)
        def ScriptMethod_writeString(self, s):
            'writeString(string) => int'
            # print('ScriptMethod_write', s)
            # assert False
            self.istream.write(s)
            self.istream.flush()
            return len(s)
        def ScriptFunc_createWriter(visitor, filepath):
            'createWriter(string) => Writer'
            fp = open(filepath, 'wb')
            # return createScriptObject('File', ScriptUnit_sys.ScriptClass_File, [fp])
            return ScriptUnit_sys.ScriptClass_File(fp)
        def ScriptFunc_createReader(visitor, filepath):
            'createReader(string) => Reader'
            fp = open(filepath, 'rb')
            # return createScriptObject('File', ScriptUnit_sys.ScriptClass_File, [fp])
            return ScriptUnit_sys.ScriptClass_File(fp)

    class ScriptClass_StringReader(object):
        def __init__(self, s):
            assert isinstance(s, str), s
            self.istream = StringIO(s)
        def ScriptMethod_close(self):
            'close()'
            pass
        def ScriptMethod_read(self, buf):
            'read([byte]) => int'
            assert False, buf
            return 0

    class ScriptClass_Writer(object):
        def __init__(self):
            pass
        def ScriptMethod_close(self):
            'close()'
        def ScriptMethod_write(self, s):
            'write([byte]) => int'
            assert False
        def ScriptMethod_writeString(self, s):
            'writeString(string) => int'
            assert False

    class ScriptClass_Reader(object):
        def __init__(self):
            pass
        def ScriptMethod_close(self):
            'close()'
        def ScriptMethod_read(self, buf):
            'read([byte]) => int'
            assert False
            return 0

    class ScriptClass_StringWriter(object):
        def __init__(self):
            self.out = StringIO()
        def ScriptMethod_close(self):
            'close()'
        def ScriptMethod_write(self, s):
            'write([byte]) => int'
            self.out.write(s)
            return len(s)
        def ScriptMethod_writeString(self, s):
            'writeString(string) => int'
            self.out.write(s)
            return len(s)

class ScriptUnit_gml_grammar(object):
    class ScriptClass_GmlLexer(object):
        def __init__(self, fin):
            self.fin = fin

    class ScriptClass_GmlParser(object):
        def __init__(self, lexer):
            self.lexer = lexer
            self.parser = parser.codeparser
            self.unit = None
            self.funcProto = None
            self.variable = None
        def ScriptMethod_getCodeUnit(self):
            'getCodeUnit() => CodeUnit'
            assert self.unit, (self, self.parser)
            return self.unit
        def ScriptMethod_getFuncProto(self):
            'getFuncProto() => FuncProto'
            assert self.funcProto, (self, self.parser)
            return self.funcProto
        def ScriptMethod_getVar(self):
            'getVar() => SingleVarDef'
            assert self.variable, (self, self.parser)
            return self.variable
        def ScriptMethod_parse(self):
            'parse()'
            unit = self.parser.parse(self.lexer.fin.istream.read())
            # print('GmlParser.parse')
            assert unit.pkg is None
            unit.pkg = ast.Package.getRoot().getPackage(unit.packageDef.fullpath)
            print('ScriptMethod_parse parse ok', unit, unit.pkg)
            astConstructor = GmlAstConstructor(self.ast_interpreter, False)
            self.unit = astConstructor.visit(unit)
            # print('ScriptMethod_parse parse constructed', unit)
        def ScriptMethod_parseFuncProto(self):
            'parseFuncProto(string)'
            funcproto = parseFuncProto(self.lexer.fin.istream.read())
            # print('GmlParser.parse')
            assert funcproto
            # print('ScriptMethod_parse parse ok', unit, unit.pkg)
            astConstructor = GmlAstConstructor(self.ast_interpreter, False)
            funcproto = astConstructor.visit(funcproto)
            # print('ScriptMethod_parse parse constructed', unit)
            return funcproto
        def ScriptMethod_parseVar(self):
            'parseVar(string)'
            var = parseVarDef(self.lexer.fin.istream.read())
            # print('GmlParser.parse')
            assert var
            # print('ScriptMethod_parse parse ok', unit, unit.pkg)
            astConstructor = GmlAstConstructor(self.ast_interpreter, False)
            var = astConstructor.visit(var)
            # print('ScriptMethod_parse parse constructed', unit)
            return funcprvaroto

    class ScriptClass_VarParser(object):
        def __init__(self, lexer):
            self.lexer = lexer
            self.parser = Parser()
            self.parser.build('var_def_item')
            self.variable = None
        def ScriptMethod_parseVar(self):
            'parseVar()'
            (vartype, varname) = self.parser.parse(self.lexer.fin.istream.read())
            var = ast.SingleVarDef(varname, vartype, None)
            astConstructor = GmlAstConstructor(self.ast_interpreter, False)
            self.variable = astConstructor.constructAst(var)
        def ScriptMethod_getVar(self):
            'getVar() => gml.SingleVarDef'
            return self.variable

def goStripDocument(declstr):
    lines = declstr.split('\n')
    i = len(lines)
    while i > 0:
        line = lines[i - 1]
        if line != '' and not line[0].isspace():
            # find the last line with whitespace(s) at start position
            retstr = '\n'.join(lines[:i])
            assert retstr != 'const (', (declstr, lines)
            return retstr
        i -= 1
    assert False, declstr
    return declstr

def goSplitDocument(text, seps):
    parts = [text]
    for sep in seps:
        splitparts = [part.split(sep) for part in parts]
        parts = list(chain.from_iterable(splitparts))
        # print('goSplitDocument', delimiter, len(splitparts), len(parts), splitparts, parts)
    return parts[1:]

def splitSlices(arr, indexes):
    ret = []
    for i in range(len(indexes)):
        startpos = indexes[i]
        endpos = indexes[i + 1] if i + 1 < len(indexes) else None
        slicelines = arr[startpos:endpos]
        # print('splitSlices', i, indexes, startpos, endpos, slicelines)
        ret.append(slicelines)
    return ret

def goSplitDeclaration(parts, tags):
    ret = []
    for part in parts:
        lines = part.split('\n')
        indexes = []
        for i in range(len(lines)):
            line = lines[i]
            if line != '' and not line[0].isspace():
                words = line.split(None, 1)
                if words[0] in tags:
                    indexes.append(i)
        lineparts = ['\n'.join(p) for p in splitSlices(lines, indexes)]
        # assert len(indexes) == 1, (indexes, lines, lineparts)
        ret.extend(lineparts)
    # assert False, (len(ret), ret)
    return ret

class ScriptUnit_sys_go(object):
    class ScriptClass_GoDoc(object):
        def ScriptFunc_getPackageInfo(visitor, pkgpath):
            'getPackageInfo([string]) => gml.LibUnit'
            startTime = time.time()
            print('ScriptFunc_getPackageInfo', pkgpath)
            fullpath = '/'.join(pkgpath)
            text = xutils.execCommand('godoc ' + fullpath)
            parts = goSplitDocument(text, ['\n\n%s\n\n' % s for s in ['CONSTANTS', 'VARIABLES', 'FUNCTIONS', 'TYPES', 'SUBDIRECTORIES', 'BUGS']])
            parts = goSplitDeclaration(parts, ['func', 'var', 'const', 'type'])
            parts = [goStripDocument(part) for part in parts]
            decls = [goparser.godeclparser.parse(part) for part in parts]
            pkgdef = ast.PackageDef(pkgpath)
            assert fullpath, pkgpath
            gounit = ast.createLibUnit(fullpath, decls)
            astConstructor = GmlAstConstructor(visitor, False)
            gmlunit = astConstructor.visit(gounit)
            print('ScriptFunc_getPackageInfo ok', pkgpath, gmlunit, time.time() - startTime)
            # assert False, ('ScriptFunc_getPackageInfo ok', pkgpath, gmlunit, time.time() - startTime)
            return gmlunit

