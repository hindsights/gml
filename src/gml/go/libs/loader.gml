package gml.go.libs

func loadLib() => [CodeUnit] {
    return [createLibUnit("sys", [LibFunctionPrintln()]),
        createLibUnit("sys.builtin", [MatchFunc(), SwitchFunc()])]
}
