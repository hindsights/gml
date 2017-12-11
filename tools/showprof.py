import pstats
import sys
sortColumn = 1
if len(sys.argv) >= 2:
    sortColumn = int(sys.argv[1])

p = pstats.Stats('gml.pyprof')
p.strip_dirs().sort_stats(sortColumn).print_stats()
