package sys

@go.import(["path", "os", "path/filepath"])

typedef FileInfo = os.FileInfo
typedef File = os.File

class PathFunctions {
    func getBaseName(s: string) => string {
        s = getFileName(s)
        var i = s.size() - 1
        for ; i >= 0 and not os.IsPathSeparator(s[i]); i-= 1 {
            if s[i] == '.' {
                return s[i:]
            }
        }
        return s
    }
    func getFileName(s : string) => string = path.Base(s)
    func getExtension(s : string) => string = path.Ext(s)
    func getDirectory(s : string) => string = path.Dir(s)
    func join(dirname : string, filename : string) => string = path.Join(dirname, filename)
}

var Path : PathFunctions = PathFunctions()

class FileSystemFunctions {
    func walkCallback(fullpath: string, info: os.FileInfo, err: error) => error {
        return nil
    }
    func walk(dir: string, walkfn: func (fullpath: string, info: os.FileInfo)) {
        filepath.Walk(dir, {
            walkfn($0, $1)
            return nil
        })
    }
}

var FileSystem = FileSystemFunctions()

func trivial() {
}

class EnvFunctions {
}

var Env = EnvFunctions()
