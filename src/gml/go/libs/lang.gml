package gml.go.libs

class MatchFunc : LibFunc {
    func MatchFunc() {
        var proto = `func match()`
        name = proto.name
        spec = proto.spec
        pkg = "sys.builtin"
    }
}

class SwitchFunc : LibFunc {
    func SwitchFunc() {
        var proto = `func switch()`
        name = proto.name
        spec = proto.spec
        pkg = "sys.builtin"
    }
}
