package gml

class Analyzer: AstVisitor {
}

class ScriptProcessor: AstVisitor {
    func visit(node: AstNode) {
        // println("ScriptProcessor.visit", node)
        node.processScript(this)
    }
    func AstNode.processScript(visitor: ScriptProcessor) {
        visitChildren(visitor)
    }
}

class ScriptPreprocessor: AstVisitor {
    func visit(node: AstNode) {
        //println("ScriptPreprocessor.visit", node)
        node.preprocessScript(this)
    }
    func AstNode.preprocessScript(visitor: ScriptPreprocessor) {
        visitChildren(visitor)
    }
}
