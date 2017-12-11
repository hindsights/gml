
import xml
import classinfo
import tree

def loadScripts(lib):
    lib.scripts['tree'] = tree.loadAll()
    classinfo.loadAll(lib.scripts)

