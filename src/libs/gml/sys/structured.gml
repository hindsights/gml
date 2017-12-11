package sys

interface StructuredWriter {
    func writeString(name: string, val: string)
    func startList(s: string, count: int)
    func endList()
    func startDict(s: string)
    func endDict()
}

class XmlWriter: StructuredWriter {
    var writer: Writer
    func writeString(name: string, val: string) {

    }
    func startList(s: string, count: int) {}
    func endList() {}
    func startDict(s: string) {}
    func endDict() {}
}

func createXmlWriter(writer: Writer) => StructuredWriter {
    return XmlWriter(writer=writer)
}
