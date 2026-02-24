cmake_minimum_required(VERSION 3.13)

project(PlayblastReadPixels VERSION 1.0.0 LANGUAGES CXX)

# ─── Options ─────────────────────────────────────────────────────────────────
set(MAYA_VERSION "2025" CACHE STRING "Maya version year (e.g: 2024, 2025)")
set(MAYA_DEVKIT_DIR "" CACHE PATH "Path to the Maya Devkit (auto-detected if empty)")
set(PLUGIN_OUTPUT_DIR "" CACHE PATH "Output directory for the compiled plugin (optional)")

# ─── CMake modules ───────────────────────────────────────────────────────────
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules")

# ─── Maya ────────────────────────────────────────────────────────────────────
find_package(Maya REQUIRED)

if(NOT Maya_FOUND)
    message(FATAL_ERROR
        "Maya devkit not found. Please define MAYA_DEVKIT_DIR or MAYA_VERSION.\n"
        "  cmake .. -DMAYA_VERSION=2025 -DMAYA_DEVKIT_DIR=C:/path/to/devkit"
    )
endif()

message(STATUS "Maya devkit found : ${MAYA_DEVKIT_DIR}")
message(STATUS "Maya include dirs : ${Maya_INCLUDE_DIRS}")

# ─── C++ standard ────────────────────────────────────────────────────────────
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ─── Sources ─────────────────────────────────────────────────────────────────
set(SOURCES
    src/plugin_main.cpp
    src/read_pixels_cmd.cpp
    src/capture_operation.cpp
    src/offscreen_override.cpp
)

set(HEADERS
    src/read_pixels_cmd.h
)

# ─── Plugin target ───────────────────────────────────────────────────────────
add_library(${PROJECT_NAME} SHARED ${SOURCES} ${HEADERS})

target_link_libraries(${PROJECT_NAME} PRIVATE Maya::Maya)

# Extension: .mll on Windows, .bundle on macOS, .so on Linux
if(WIN32)
    set_target_properties(${PROJECT_NAME} PROPERTIES
        SUFFIX ".mll"
        PREFIX ""
    )
elseif(APPLE)
    set_target_properties(${PROJECT_NAME} PROPERTIES
        SUFFIX ".bundle"
        PREFIX ""
    )
else()
    set_target_properties(${PROJECT_NAME} PROPERTIES
        SUFFIX ".so"
        PREFIX ""
    )
endif()

# ─── Output directory ────────────────────────────────────────────────────────
if(PLUGIN_OUTPUT_DIR)
    set_target_properties(${PROJECT_NAME} PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY "${PLUGIN_OUTPUT_DIR}"
        LIBRARY_OUTPUT_DIRECTORY "${PLUGIN_OUTPUT_DIR}"
    )
    message(STATUS "Plugin output directory : ${PLUGIN_OUTPUT_DIR}")
endif()

# ─── Build information ───────────────────────────────────────────────────────
message(STATUS "--------------------------------------------")
message(STATUS "  Project   : ${PROJECT_NAME} ${PROJECT_VERSION}")
message(STATUS "  Maya      : ${MAYA_VERSION}")
message(STATUS "  Platform  : ${CMAKE_SYSTEM_NAME}")
message(STATUS "  Build     : ${CMAKE_BUILD_TYPE}")
message(STATUS "--------------------------------------------")