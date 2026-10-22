# Sparrow Decider C runtime. Works as an ESP-IDF component (add this directory to
# EXTRA_COMPONENT_DIRS) and as a plain CMake library elsewhere.
if(ESP_PLATFORM)
  idf_component_register(SRCS "src/sparrow.c" INCLUDE_DIRS "include")
  target_compile_options(${COMPONENT_LIB} PRIVATE -O2 -ffast-math)
else()
  cmake_minimum_required(VERSION 3.16)
  project(sparrow C)
  add_library(sparrow src/sparrow.c)
  target_include_directories(sparrow PUBLIC include)
  target_compile_options(sparrow PRIVATE -O3 -ffast-math)
  target_link_libraries(sparrow PUBLIC m)
endif()
