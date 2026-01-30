cmake_minimum_required(VERSION 3.15)
project(PokeathlonNative C)

set(CMAKE_C_STANDARD 11)

# Enable optimizations by default
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Output directory for built libraries
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Destination for copying DLLs into the Python package
set(SOLVER_BINDINGS_DIR "${CMAKE_SOURCE_DIR}/../solver_core/src/solver_core/bindings")

# ===== Recipe Calculator Library =====
add_library(recipe_calc SHARED
    src/recipe/recipe_calculator.c
)

target_compile_options(recipe_calc PRIVATE
    $<$<C_COMPILER_ID:MSVC>:/W3 /O2>
    $<$<C_COMPILER_ID:GNU>:-Wall -Wextra -Ofast>
    $<$<C_COMPILER_ID:Clang>:-Wall -Wextra -Ofast>
)

# ===== HGSS Seed Search Library =====
add_library(hgss_seedlib SHARED
    src/seed/hgss_searcher.c
    src/seed/mt_tool.c
    src/seed/pid_tool.c
)

target_compile_options(hgss_seedlib PRIVATE
    $<$<C_COMPILER_ID:MSVC>:/W3 /O2>
    $<$<C_COMPILER_ID:GNU>:-Wall -Wextra -Ofast>
    $<$<C_COMPILER_ID:Clang>:-Wall -Wextra -Ofast>
)

# Link math library on Unix systems
if(UNIX)
    target_link_libraries(recipe_calc PRIVATE m)
    target_link_libraries(hgss_seedlib PRIVATE m)
endif()

# ===== Installation / Copy to Python package =====
# Custom target to copy DLLs to solver_core/bindings after build
add_custom_command(TARGET recipe_calc POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "${SOLVER_BINDINGS_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:recipe_calc> "${SOLVER_BINDINGS_DIR}/"
    COMMENT "Copying recipe_calc library to ${SOLVER_BINDINGS_DIR}"
)

add_custom_command(TARGET hgss_seedlib POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "${SOLVER_BINDINGS_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:hgss_seedlib> "${SOLVER_BINDINGS_DIR}/"
    COMMENT "Copying hgss_seedlib library to ${SOLVER_BINDINGS_DIR}"
)

# Install targets (optional, for system-wide installation)
install(TARGETS recipe_calc hgss_seedlib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)

# ===== Print build configuration =====
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C Compiler: ${CMAKE_C_COMPILER_ID}")
message(STATUS "Output directory: ${CMAKE_BINARY_DIR}")
message(STATUS "Python bindings directory: ${SOLVER_BINDINGS_DIR}")
