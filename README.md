### README

#### Overview
GML(Generative Meta Language) is a programming language which focuses on automatic code generation.

There are two parts in GML's source code. The first is an GML interpreter written in python, the second is a GML generator which is written in GML itself and generates golang code.

Currently, GML is still at a very early stage, the implementation is incomplete, especially the generator(with a very limited support for golang code generation). And there will be substantial changes in the features of the language.

#### Quick Start
```
mkdir build
cd build
cmake ..
# "make runtest" will run the interpreter and evaluate the code of gml generator with simple.gml as the input
make runtest
# add current working directory to GOPATH
source ../tools/gopath.env
go build -o simple
# run ./simple, it will search the specified folder, and print files with identical names
./simple .
```

#### Dependencies
cmake, make, Python, ply(lexer/parser), godoc(extract information from golang's core library)

Test Environment:<br>
Mac OS X 10.12<br>
Python 2.7<br>
ply 3.10<br>
golang 1.9<br>
cmake 3.10<br>
