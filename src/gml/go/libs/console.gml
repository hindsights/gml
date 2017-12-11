package gml.go.libs

class LibFunctionPrintln: LibFunc {
    func LibFunctionPrintln() {
        pkg = "sys"
        var proto = #{func println()}
        // println("LibFunctionPrintln proto", proto)
        name = proto.name
        spec = proto.spec
        //println("LibFunctionPrintln.init", proto)
    }
    func analyzeDependency(visitor: DeepAnalyzer, unit: CodeUnit) {
        // println("LibFunctionPrintln.analyzeDependency", unit.name)
        unit.handler.addDep("fmt")
        //do assert false, "LibFunctionPrintln.analyzeDependency"
    }
    func writeCall(writer: SourceWriter, call: Call) {
        //println("LibFunctionPrintln", call, call.args)
        writer.writer.writeInlineBlockExpression("fmt.Println(", ")", {writer.writeArgs(spec, call.args)})
    }
}
