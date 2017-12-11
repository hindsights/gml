package test

@go.import("os")
import sys (Path, FileSystem)

class FileIndex(name: string) {
	var files: {string: int64}
	func add(path: string, info: os.FileInfo) {
		//do assert path not in files, "FileInfo.add", path
		if info.IsDir() {
			return
		}
		files[path] = info.Size()
	}
	func printAll() {
		// files.each({println("file:", $0, $1)})
	}
}

class FileSearcher {
	var files234: {string: FileIndex}
	var dupicateFiles: {string}

	func addFile(path: string, info: os.FileInfo) {
		var name = Path.getFileName(path)
		if name in files234 {
			// println("add duplicate", name, path, info.Size())
			var fi1 = files234[name]
			fi1.add(path, info)
			dupicateFiles.add(name)
		} else {
			var fi2 = FileIndex(name=name)
			fi2.add(path, info)
			files234[name] = fi2
		}
	}
	func search(path: string) {
		FileSystem.walk(path, {
			addFile($0, $1)
		})
		println("search ok", path)
	}
	func printDuplicates(name: string) {
		println("printDuplicates", name)
		var fi = files234.get(name)
		if fi == nil {
			println("printDuplicates: not found", name)
			return
		}
		fi.printAll()
	}
	func testCallback(fn: func (s: string) => string) {
		var s1 = "abc"
		var s2 = "xyz"
		var s3 = fn(s1)
		println(s3)
		println(fn(s2))
	}
}

func runMain(args: [string]) => int {
	println("simple main", args)
	if args.size() < 2 {
		println("no argument")
		return 1
	}
	var dir = args[1]
	println("dir name:", dir)
	var searcher = FileSearcher()
	searcher.search(dir)
	println("search completed", searcher.files234.size(), searcher.dupicateFiles.size())
	searcher.dupicateFiles.each({
		searcher.printDuplicates($0)
	})
	searcher.testCallback({
		println("callback", $0)
		return $0 + "_ending"
	})
	return 0
}
