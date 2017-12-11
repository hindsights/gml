package gml.go

import sys (File, Writer)
import sys (Path, FileSystem)
import sys.Env

func toPascal(name: string) => string {
    return name[:1].upper() + name[1:]
}

class AstFormatter {
    var binaryOperatorMapping : {string: string} = {"and": "&&", "or": "||"}
    var unaryOperatorMapping : {string: string} = {"not": "!"}
    func AstNode.formatStringArg(formatter: AstFormatter) => string =
        do match {
            AstNode => "formatStringArg(AstNode:%s)" % toString()
        }
    func AstNode.formatStorageType(formatter: AstFormatter) => string = formatParamType(formatter)
    func AstNode.formatReturnType(formatter: AstFormatter) => string = formatParamType(formatter)
    func AstNode.formatParamType(formatter: AstFormatter) => string = 
        do match {
            AstNode => formatType(formatter)
            UserType => target.getTypeClass().formatParamUserType(formatter, this)
            // UserType => "UserType.formatParamType:%s:%s" % (fullpath, target)
        }
    func AstNode.formatUserType(formatter: AstFormatter, ut: UserType) => string {
        // println("AstNode.formatUserType", this, ut)
        return do match {
            // AstNode => "AstNode.formatParamUserType:%s:%s" % (toString(), ut.fullpath)
            AstNode => ut.getTypeClass().formatType(formatter)
            ClassDef => ut.fullpath
            UserTypeClass => storage.formatParamUserType(formatter, ut)
        }
    }
    func AstNode.formatParamUserType(formatter: AstFormatter, ut: UserType) => string {
        // println("AstNode.formatParamUserType", this, ut.toString())
        return do match {
            AstNode => formatType(formatter)
            UserTypeClass => storage.formatParamUserType(formatter, ut)
            ClassDef => typeClass.formatParamUserType(formatter, ut)
        }
    }
    func AstNode.formatType(formatter: AstFormatter) => string =
        do match {
            AstNode => "formatType(AstNode:%s)" % toString()
            UserType => target.getTypeClass().formatUserType(formatter, this)
            FuncSpec => "func (%s) %s" % (", ".join(["%s %s" % (param.name, param.type.formatType(formatter)) for param in params]), returnType.formatReturnType(formatter) if returnType else "")
        }
    func AstNode.formatVarInitial(formatter: AstFormatter, val: AstNode) => string =
        do match {
            AstNode => "formatVarInitial(AstNode:%s,val=%s)" % (toString(), val)
        }
    func AstNode.formatAttrCall(formatter: AstFormatter, call: Call, attr: AttrRef) => string =
        do match {
            AstNode => "formatAttrCall(AstNode:%s,attr:%s)" % (toString(), attr)
            FuncDef => "%s(%s)" % (attr.format(formatter), formatter.formatArgs(spec, call.args))
            FuncProto => "%s(%s)" % (attr.format(formatter), formatter.formatArgs(spec, call.args))
        }
    func AstNode.formatCall(formatter: AstFormatter, call: Call) => string =
        do match {
            AstNode => "formatCall(AstNode:%s)" % toString()
            Identifier => target.formatCall(formatter, call)
            AttrRef => target.formatAttrCall(formatter, call, this)
            ClassDef => "&%s{%s}" % (call.caller.format(formatter), formatter.formatConstructorArgs(this, call))
            FuncDef => "%s(%s)" % (call.caller.format(formatter), formatter.formatArgs(getSpec(), call.args))
        }
    func formatArgs(spec: FuncSpec, args: [Expression]) => string = ", ".join([arg.format(this) for arg in args])
    func formatConstructorArgs(cls: ClassDef, call: Call) => string {
        do assert call.args.size() == 0, "formatConstructorArgs with args", cls, call.args, call.namedArgs
        var args = ["%s: %s" % (toPascal(arg.name), arg.value.format(this)) for arg in call.namedArgs]
        var fields = ["%s: %s" % (toPascal(field.name), field.initial.format(this)) for field in cls.context.vars if field.name not in call.namedArgs and field.initial != nil]
        var defaultfields = ["%s: %s" % (toPascal(field.name), field.type.formatDefaultValue()) for field in cls.context.vars if field.name not in call.namedArgs and field.initial == nil and field.type.needDefaultValue()]
        // println("formatConstructorArgs", cls, args, fields, defaultfields)
        return ", ".join(args + fields + defaultfields)
        // return ", ".join(args)
    }
    func AstNode.needDefaultValue() => bool =
        do match {
            AstNode => false
            UserType => getTypeClass().needDefaultValue()
        }
    func AstNode.formatDefaultValue(formatter: AstFormatter) => string =
        do match {
            AstNode => "AstNode.formatDefaultValue:%s" % this
            UserType => getTypeClass().formatDefaultValue(formatter)
        }
    func AstNode.format(formatter: AstFormatter) => string =
        do match {
            AstNode => "format(AstNode:%s)" % toString()
            Break => "break"
            Continue => "continue"
            IntLiteral => text
            FloatLiteral => text
            BoolLiteral => text
            StringLiteral => "\"%s\"" % text
            CharLiteral => "\'%s\'" % text
            Nil => "nil"
            Identifier => target.formatIdentifier(formatter, this)
            BinaryOp => handler.formatBinaryOp(formatter, this)
            UnaryOp => operand.getTypeClass().formatUnaryOp(formatter, this)
            Call => caller.formatCall(formatter, this)
            Return => "return %s" % value.format(formatter) if value != nil else "return"
            ArgumentPlaceholder => targetParam.name
            AttrRef => "%s.%s" % (object.format(formatter), toPascal(ref))
            Assignment => "%s %s %s" % (targets[0].format(formatter), op, values[0].format(formatter))
            Subscript => "%s[%s]" % (collection.format(formatter), key.format(formatter))
            Slicing => "%s[%s:%s]" % (collection.format(formatter), start.format(formatter) if start else "", stop.format(formatter) if stop else "")
            StringEvaluation => evaluation.format(formatter) if evaluation else literal.format(formatter)
            Closure => spec.format(formatter) + " {%s}" % "; ".join([stmt.format(formatter) for stmt in body.statements])
            FuncSpec => "func (" + ", ".join(["%s %s" % (param.name, param.type.formatParamType(formatter)) for param in params]) + ") " + returnType.formatReturnType(formatter)
            SingleVarDef => name + " := " + initial.format(formatter) if initial else "var " + name + " " + type.format(formatter)
        }
    func AstNode.formatIdentifierInOwner(formatter: AstFormatter, identifier: Identifier) => string =
        do match {
            AstNode => identifier.name
            CodeUnit => pkg.path[-1] + "." + toPascal(identifier.name) if pkg.fullpath != identifier.getCodeUnit().pkg.fullpath else identifier.name
            ClassDef => "self.%s" % toPascal(identifier.name)
            ExtensionDef => "self.%s" % toPascal(identifier.name)
        }
    func AstNode.formatIdentifier(formatter: AstFormatter, identifier: Identifier) => string =
        getOwner().formatIdentifierInOwner(formatter, identifier)
    func BinaryOpHandler.formatBinaryOp(formatter: AstFormatter, expr: BinaryOp) => string =
        do match {
            BinaryOpHandler => "%s %s %s" % (expr.left.format(formatter), formatter.binaryOperatorMapping.get(expr.op, expr.op), expr.right.format(formatter))
            MembershipBinaryOpHandler => expr.right.getTypeClass().formatBinaryOp(formatter, expr)
        }
    func AstNode.formatBinaryOp(formatter: AstFormatter, expr: BinaryOp) => string =
        do match {
            AstNode => "formatBinaryOp(AstNode:%s,expr:%s)" % (toString(), expr)
        }
    func AstNode.formatUnaryOp(formatter: AstFormatter, expr: UnaryOp) => string =
        do match {
            AstNode => "formatUnaryOp(AstNode:%s)" % toString()
        }
}

class WriterConfig {
    var useTab = false
    var tabWidth = 4
}

class CodeWriter {
    var fout: Writer
    var depth: int = 0
    var config: WriterConfig
    func writeTab() {
        if depth <= 0 {
            return
        }
        var tabstr = "\t" * depth if config.useTab else " " * config.tabWidth * depth
        //println("writeTab", depth, tabstr.size())
        write(tabstr)
    }
    func writeBlankLine() {
        writeBlankLines(1)
    }
    func writeBlankLines(count: int) {
        write("\n" * count)
    }
    func writeCode(s: string) {
        writeTab()
        write(s)
    }
    func writeStatement(s: string) {
        writeCode(s)
        writeBlankLine()
    }
    func incIndent() {
        depth += 1
    }
    func decIndent() {
        depth -= 1
    }
    func write(s: string) {
        fout.writeString(s)
    }
    func writeCodeStart(s: string) {
        writeCode(s)
        incIndent()
    }
    func writeCodeEnd(s: string) {
        decIndent()
        writeCode(s)
    }
    func writeStart(s: string) {
        write(s)
        incIndent()
    }
    func writeEnd(s: string) {
        decIndent()
        write(s)
    }
    func writeBlockStatement(s: string, fn: func() => void) {
        writeCodeBlock(s + " {\n", "}\n", fn)
    }
    func writeInlineBlockStatement(s: string, fn: func() => void) {
        writeBlockExpression(s + " {\n", "}\n", fn)
    }
    func writeParenthesis(s: string, fn: func() => void) {
        writeCodeBlock(s + "(\n", ")\n", fn)
    }
    func writeCodeBlock(starttag: string, endtag: string, fn: func() => void) {
        writeCodeStart(starttag)
        fn()
        writeCodeEnd(endtag)
    }
    func writeBlockExpression(starttag: string, endtag: string, fn: func() => void) {
        writeStart(starttag)
        fn()
        writeCodeEnd(endtag)
    }
    func writeInlineBlockExpression(starttag: string, endtag: string, fn: func() => void) {
        writeStart(starttag)
        fn()
        writeEnd(endtag)
    }
}

class SourceWriter: AstVisitor {
    var writer: CodeWriter
    var formatter: AstFormatter
    func visit(node: AstNode) {
        node.writeSource(this)
    }
    func AstNode.writeExpression(visitor: SourceWriter) => void {
        do match {
            case AstNode:
                do assert false, "AstNode.writeExpression", toString(), getOwner()
            case Expression:
                visitor.writer.write(format(visitor.formatter))
            case BinaryOp:
                handler.writeBinaryOp(visitor, this)
            case UnaryOp:
                do assert operand.getTypeClass(), ("UnaryOp.writeExpression", operand, operand.getType(), op, getFuncDef())
                operand.getTypeClass().writeUnaryOp(visitor, this)
            case Call:
                caller.writeCall(visitor, this)
            case Closure:
                // println("Closure.writeExpression", getSpec(), getSpec().params, getSpec().returnType, getFuncDef(), getCodeUnit())
                visitor.writer.writeBlockExpression(getSpec().format(visitor.formatter) + " {\n", "}", {body.writeSource(visitor)})
            case SingleVarDef:
                visitor.writer.write(name + " := ")
                initial.writeExpression(visitor)
            case Assignment:
                targets[0].writeExpression(visitor)
                visitor.writer.write(" %s " % op)
                // println("Assignment.writeExpression", values, targets, op)
                values[0].writeExpression(visitor)
            case CallStatement:
                call.writeExpression(visitor)
        }
    }
    func AstNode.writeSource(visitor: SourceWriter) => void {
        do match {
            case AstNode:
                do assert false, "AstNode.writeSource", toString(), getOwner()
            case Expression:
                writeExpression(visitor)
            case Statement:
                visitor.writer.writeStatement(format(visitor.formatter))
            case PackageDef:
                // pass
            case Import:
                // pass
            case Script:
                //pass
            case CodeUnit:
                handler.writeSource(visitor)
            case TypeDef:
                visitor.writer.writeStatement("type " + name + " " + target.formatType(visitor.formatter))
            case SingleVarDef:
                getOwner().writeSingleVarDef(visitor, this)
            case MultipleVarDef:
                getOwner().writeMultipleVarDef(visitor, this)
            case TupleVarDef:
                getOwner().writeTupleVarDef(visitor, this)
            case Return:
                if value == nil {
                    visitor.writer.writeStatement("return")
                } else {
                    visitor.writer.writeCode("return ")
                    value.writeSource(visitor)
                    visitor.writer.writeBlankLine()
                }
            case Assignment:
                visitor.writer.writeTab()
                writeExpression(visitor)
                visitor.writer.writeBlankLine()
            case CallStatement:
                visitor.writer.writeTab()
                writeExpression(visitor)
                visitor.writer.writeBlankLine()
            case StatementBlock:
                body.writeSource(visitor)
            case StatementBody:
                for stmt in statements {
                    stmt.writeSource(visitor)
                }
        }
    }
    func AstNode.writeUnaryOp(visitor: SourceWriter, expr: UnaryOp) {
        visitor.writer.write(" %s " % visitor.formatter.unaryOperatorMapping.get(expr.op, expr.op))
        expr.operand.writeSource(visitor)
    }
    func BinaryOpHandler.writeBinaryOp(visitor: SourceWriter, expr: BinaryOp) => void {
        do match {
            case BinaryOpHandler:
                expr.left.writeSource(visitor)
                visitor.writer.write(" %s " % visitor.formatter.binaryOperatorMapping.get(expr.op, expr.op))
                expr.right.writeSource(visitor)
            case MembershipBinaryOpHandler:
                expr.right.getTypeClass().writeBinaryOp(visitor, expr)
        }
    }
    func AstNode.writeCall(visitor: SourceWriter, call: Call) => void {
        do match {
            case AstNode:
                do assert false, "AstNode.writeCall(AstNode:%s:%s)" % (toString(), call.caller)
            case Identifier:
                target.writeCall(visitor, call)
            case AttrRef:
                target.writeAttrCall(visitor, call, this)
            case Param:
                visitor.writer.writeInlineBlockExpression("%s(" % call.caller.format(visitor.formatter), ")", {visitor.writeArgs(call.getSpec(), call.args)})
            case ClassDef:
                // visitor.writer.write(formatCall(visitor.formatter, call))
                var cls = this
                visitor.writer.writeInlineBlockExpression("&%s{" % call.caller.format(visitor.formatter), "}", {visitor.writeConstructorArgs(cls, call)})
            case FuncDef:
                visitor.writer.writeInlineBlockExpression("%s(" % call.caller.format(visitor.formatter), ")", {visitor.writeArgs(spec, call.args)})
        }
    }
    func TypeClass.writeBinaryOp(writer: SourceWriter, expr: BinaryOp) {
        do assert false, "TypeClass.writeBinaryOp", expr.left, expr.right, expr.op
    }
    func AstNode.writeAttrCall(visitor: SourceWriter, call: Call, attr: AttrRef) => void {
        do match {
            case AstNode:
                do assert false, "AstNode.writeAttrCall(AstNode:%s,attr:%s)" % (toString(), attr)
            case FuncDef:
                visitor.writer.writeInlineBlockExpression(attr.format(visitor.formatter) + "(", ")", {visitor.writeArgs(spec, call.args)})
            case FuncProto:
                visitor.writer.writeInlineBlockExpression(attr.format(visitor.formatter) + "(", ")", {visitor.writeArgs(spec, call.args)})
        }
    }
    func writeArgs(spec: FuncSpec, args: [Expression]) => void {
        // println("writeArgs", args)
        var tag = ""
        for arg in args {
            // println("writeArgs arg", tag, arg)
            writer.write(tag)
            arg.writeSource(this)
            tag = ", "
        }
    }
    func writeNamedArgs(args: [NamedExpressionItem]) => int {
        var argcount = 0
        for arg in args {
            // println("writeNamedArgs arg", arg)
            if argcount > 0 {
                writer.write(", ")
            }
            writer.write(toPascal(arg.name) + ": ")
            arg.value.writeSource(this)
            argcount += 1
        }
        return argcount
    }
    func writeFields(cls: ClassDef, call: Call, argcount: int) => int {
        for field in cls.context.vars {
            Log.event("writeFields arg check", cls, field, call, call.namedArgs)
            if field.name not in call.namedArgs and field.initial != nil {
                Log.event("writeFields arg", cls, field)
                if argcount > 0 {
                    writer.write(", ")
                }
                writer.write(toPascal(field.name) + ": ")
                field.initial.writeSource(this)
                argcount += 1
            }
        }
        return argcount
    }
    func writeDefaultFields(cls: ClassDef, call: Call, argcount: int) => int {
        for field in cls.context.vars {
            Log.event("writeDefaultFields arg check", cls, field, call, call.namedArgs)
            if field.name not in call.namedArgs and field.initial == nil and field.type.needDefaultValue() {
                Log.event("writeDefaultFields arg", cls, field)
                if argcount > 0 {
                    writer.write(", ")
                }
                writer.write(toPascal(field.name) + ": " + field.type.formatDefaultValue(formatter))
                argcount += 1
            }
        }
        return argcount
    }
    func writeConstructorArgs(cls: ClassDef, call: Call) => void {
        do assert call.args.size() == 0, "writeArgs with args", cls, call.args, call.namedArgs
        var argcount = writeNamedArgs(call.namedArgs)
        argcount = writeFields(cls, call, argcount)
        argcount = writeDefaultFields(cls, call, argcount)
        Log.event("formatConstructorArgs", cls, argcount)
    }
    func AstNode.getUnitPackage() => Package =
        do match {
            AstNode => nil
            CodeUnit => pkg
            LibUnit => pkg
        }
    func GoUnitHandler.writeSource(visitor: SourceWriter) {
        var writer = visitor.writer
        var unitpkg = unit.getUnitPackage()
        writer.writeStatement("package " + unitpkg.path[-1])
        writer.writeBlankLine()
        writer.writeParenthesis("import ", {deps.each({writer.writeStatement("\"%s\"" % $0)})})
        writer.writeBlankLine()
        unit.visitChildren(visitor)
    }
    func writeInterface(cls: ClassDef) {
        var visitor = this
        writer.writeBlockStatement("type " + cls.name + " interface", {
            cls.context.functions.each({$0.writeSource(visitor)})
        })
    }
    func ClassDef.writeSource(visitor: SourceWriter) {
        Log.event("ClassDef.writeSource", name, classType, ClassType.normal, ClassType.interface, ClassType.trait)
        if classType != ClassType.normal {
            visitor.writeInterface(this)
            return
        }
        visitor.writer.writeBlockStatement("type " + name + " struct", {
            bases.each({visitor.writer.writeStatement($0.fullpath)})
            context.vars.each({$0.writeSource(visitor)})
        })
        context.functions.each({$0.writeSource(visitor)})
    }
    func EnumDef.writeSource(visitor: SourceWriter) {
        visitor.writer.writeParenthesis("const ", {
            items.each({visitor.writer.writeStatement($0.name + " = " + $0.value.format(visitor.formatter))})
        })
    }
    func AstNode.writeMultipleVarDef(visitor: SourceWriter, v: MultipleVarDef) {
        do assert false, ("AstNode.writeMultipleVarDef", toString(), v)
    }
    func AstNode.writeTupleVarDef(visitor: SourceWriter, v: TupleVarDef) {
        visitor.writer.writeCode(", ".join([sv.name for sv in v.vars]))
        visitor.writer.write(" := ")
        v.initial.writeExpression(visitor)
        visitor.writer.writeBlankLine()
    }
    func AstNode.writeSingleVarDef(visitor: SourceWriter, v: SingleVarDef) {
        do match {
            case AstNode:
                var s = "var " + v.name
                if v.initial {
                    visitor.writer.writeCode(s + " = ")
                    v.initial.writeSource(visitor)
                    visitor.writer.writeBlankLine()
                } else {
                    s = s + " " + v.type.formatType(visitor.formatter)
                    visitor.writer.writeStatement(s)
                }
            case CodeUnit:
                var s = "var " + toPascal(v.name)
                if v.initial {
                    visitor.writer.writeStatement(s + " = ")
                    v.initial.writeSource(visitor)
                    visitor.writer.writeBlankLine()
                } else {
                    s = s + " " + v.type.formatType(visitor.formatter)
                    visitor.writer.writeStatement(s)
                }
            case ClassDef:
                visitor.writer.writeStatement(toPascal(v.name) + " " + v.type.formatType(visitor.formatter))
        }
    }
    func FuncProto.writeSource(visitor: SourceWriter) {
        var f = this
        var writer = visitor.writer
        var rettype = f.spec.returnType.formatReturnType(visitor.formatter) if f.spec.returnType else ""
        var funcname = toPascal(name)
        var argstr = ", ".join(["%s %s" % (param.name, param.type.formatParamType(visitor.formatter)) for param in f.spec.params])
        visitor.writer.writeStatement("%s(%s) %s" % (funcname, argstr, rettype))
    }
    func FuncDef.writeSource(visitor: SourceWriter) {
        var f = this
        var writer = visitor.writer
        var clsprefix = ""
        if f.cls {
            clsprefix = "(self *%s) " % toPascal(f.cls.name)
        }
        Log.event("function:", f.name, f.spec)
        var funcname = toPascal(name)
        var rettype = ""
        if f.info.type == FuncType.normal {
            rettype = f.spec.returnType.formatReturnType(visitor.formatter) + " " if f.spec.returnType else " "
            Log.event("FuncDef.writeSource", f.spec.returnType, f.spec, f, rettype)
        } elseif f.info.type == FuncType.constructor {
        }
        var argstr = ", ".join(["%s %s" % (param.name, param.type.formatParamType(visitor.formatter)) for param in f.spec.params])
        visitor.writer.writeBlockStatement("func %s%s(%s) %s" % (clsprefix, funcname, argstr, rettype), {
            f.body.writeSource(visitor)
        })
    }
    func IfStatement.writeSource(visitor: SourceWriter) {
        var tag = "if"
        var writer = visitor.writer
        writer.writeTab()
        for branch in branches {
            writer.write(tag + " ")
            branch.condition.writeSource(visitor)
            writer.writeBlockExpression(" {\n", "}", {branch.body.writeSource(visitor)})
            tag = " else if"
        }
        Log.event("IfStatement.writeSoure else", elseBranch)
        if elseBranch {
            writer.writeBlockExpression(" else {\n", "}", {elseBranch.body.writeSource(visitor)})
        }
        writer.writeBlankLine()
    }
    func ForStatement.writeSource(visitor: SourceWriter) {
        var writer = visitor.writer
        writer.writeCode("for ")
        if init == nil and step == nil {
            if condition {
                condition.writeSource(visitor)
            }
        } else {
            if init {
                init.writeExpression(visitor)
            }
            writer.write("; ")
            if condition {
                condition.writeSource(visitor)
            }
            writer.write("; ")
            if step {
                step.writeExpression(visitor)
            }
        }
        writer.writeInlineBlockStatement("", {body.writeSource(visitor)})
    }
}

class Generator: AstVisitor {
    var config: GeneratorConfig
    func visit(unit: CodeUnit) {
        Log.event("generate name=%s dir=%s" % (unit.name, config.outputDir))
        FileSystem.ensureDirectoryExists(config.outputDir)
        // var gopath = Env.get("GOPATH").split(":")[0]
        var outputDir = Path.combine(config.outputDir, "src", Path.join(unit.pkg.path))
        FileSystem.ensureDirectoryExists(outputDir)
        Log.event("outputDir for code unit", unit.name, unit, config.outputDir, outputDir)
        var writerConfig = WriterConfig()
        var formatter = AstFormatter()

        var gofilepath = Path.combine(outputDir, unit.name + ".go")
        Log.event("generate file:", gofilepath)
        var fout = File.createWriter(gofilepath)
        var writer = CodeWriter(fout=fout, config=writerConfig)
        var defWriter = SourceWriter(writer=writer, formatter=formatter)
        defWriter.visit(unit)
        fout.close()
        Log.event("check main", unit.name, unit.hasMain)
        if unit.hasMain {
            var mainfilepath = Path.combine(config.outputDir, unit.name + "_main.go")
            Log.event("generate file main:", mainfilepath)
            using mainfout = File.createWriter(mainfilepath) {
                var mainwriter = CodeWriter(fout=mainfout, config=writerConfig)
                mainwriter.writeStatement("package main")
                mainwriter.writeParenthesis("import ", {
                    mainwriter.writeStatement("\"os\"")
                    mainwriter.writeStatement("\"%s\"" % unit.pkg.fullpath)
                })
                mainwriter.writeBlockStatement("func main()", {mainwriter.writeStatement("%s.RunMain(os.Args)" % unit.pkg.path[-1])})
            }
        }
    }
}
