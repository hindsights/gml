package sys

@go.import("strings")
@go.import("io")

typedef Reader = io.Reader
typedef Writer = io.Writer

class StringsFunctions {
    func createReader(s: string) => Reader {
        return strings.NewReader(s)
    }
}

var Strings = StringsFunctions()
