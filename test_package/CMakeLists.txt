cmake_minimum_required(VERSION 3.1)
project(test_package)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(${PROJECT_NAME}_c test_package.c)
target_link_libraries(${PROJECT_NAME}_c ${CONAN_LIBS})

if(SPIRV_TOOLS_STATIC)
  add_executable(${PROJECT_NAME}_cpp test_package.cpp)
  target_link_libraries(${PROJECT_NAME}_cpp ${CONAN_LIBS})
  set_property(TARGET ${PROJECT_NAME}_cpp PROPERTY CXX_STANDARD 11)
endif()
