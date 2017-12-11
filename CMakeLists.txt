cmake_minimum_required(VERSION 2.8)

project(gml)

file(GLOB_RECURSE gml_sources "src/gml/*.gml")
message("gml sources: ${gml_sources}")

file(GLOB_RECURSE gmlparser_sources "tools/parser/*.gml")
message("gmlparser sources: ${gmlparser_sources}")

file(GLOB_RECURSE gmllexer_sources "tools/lexer/*.gml")
message("gmllexer sources: ${gmllexer_sources}")

#file(GLOB_RECURSE lib_gml_sources "../libs/gml/*.gml")
#message("lib gml sources: ${lib_gml_sources}")
#message("lib gml lib:" "$CMAKE_SOURCE_DIR/libs/gml)

add_custom_target(runtest python ${CMAKE_SOURCE_DIR}/src/python/gml.py -l ${CMAKE_SOURCE_DIR}/src/libs/gml:${CMAKE_SOURCE_DIR}/src/libs/go ${CMAKE_SOURCE_DIR}/tests/simple.gml)
add_custom_target(gogml python ${CMAKE_SOURCE_DIR}/src/python/gml.py -l ${CMAKE_SOURCE_DIR}/src/libs/gml:${CMAKE_SOURCE_DIR}/src/libs/go ${gml_sources})
add_custom_target(gmlparser python ${CMAKE_SOURCE_DIR}/src/python/gml.py -l ${CMAKE_SOURCE_DIR}/src/libs/gml:${CMAKE_SOURCE_DIR}/src/libs/go ${gmlparser_sources})
add_custom_target(gmllexer python ${CMAKE_SOURCE_DIR}/src/python/gml.py -l ${CMAKE_SOURCE_DIR}/src/libs/gml:${CMAKE_SOURCE_DIR}/src/libs/go ${gmllexer_sources})
