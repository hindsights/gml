package sys.util

class SimpleProgramOptions {
	var args : [string]
	var flags : {string}
	var opts : {string:string}
	var files : [string]
	func SimpleProgramOptions() {
	}
	func getFiles() => [string] {
		return files
	}
	func loadStrings(a : [string]) {
		println("loadStrings start", a.size(), a)
		args = a
		for var i = 0; i < args.size(); i += 1 {
			var arg = args[i]
			println("loadStrings arg", i, arg)
			if arg[0] == '-' {
				println("loadStrings arg", arg, arg[0], i)
				if i + 1 < args.size() and args[i + 1][0] != '-' {
					println("loadStrings arg check val arg", arg, args[i+1], i)
					opts[arg] = args[i + 1]
					i += 1
				} else {
					println("loadStrings arg check bool arg", arg)
					flags.add(arg)
				}
			} else {
				println("loadStrings collect remaining args", i)
				files = args[i:]
				break
			}
		}
	}
	func getOption(name : string, defval : string) => string {
		return opts.get(name, defval)
	}
}
