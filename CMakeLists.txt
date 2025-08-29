cmake_minimum_required(VERSION 3.16)
project(knapsack_aco CXX)

# C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Onde colocar os .exe gerados
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Inclui a pasta de headers
include_directories(${CMAKE_SOURCE_DIR}/include)

# Coleta todos os .cpp dentro de src/ automaticamente
file(GLOB_RECURSE PROJECT_SOURCES CONFIGURE_DEPENDS
    ${CMAKE_SOURCE_DIR}/src/*.cpp
)

# Gera o executável principal a partir dos .cpp encontrados
add_executable(main ${PROJECT_SOURCES})
