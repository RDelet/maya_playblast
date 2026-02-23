cmake_minimum_required(VERSION 3.13)

project(PlayblastReadPixels VERSION 1.0.0 LANGUAGES CXX)

# ─── Options ─────────────────────────────────────────────────────────────────
set(MAYA_VERSION "2025" CACHE STRING "Maya version year (ex: 2024, 2025)")
set(MAYA_DEVKIT_DIR "" CACHE PATH "Chemin vers le Maya Devkit (auto-détecté si vide)")
set(PLUGIN_OUTPUT_DIR "" CACHE PATH "Dossier de sortie du plugin compilé (optionnel)")

# ─── CMake modules ───────────────────────────────────────────────────────────
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules")

# ─── Maya ────────────────────────────────────────────────────────────────────
find_package(Maya REQUIRED)

if(NOT Maya_FOUND)
    message(FATAL_ERROR
        "Maya devkit introuvable. Définissez MAYA_DEVKIT_DIR ou MAYA_VERSION.\n"
        "  cmake .. -DMAYA_VERSION=2025 -DMAYA_DEVKIT_DIR=C:/path/to/devkit"
    )
endif()

message(STATUS "Maya devkit trouvé : ${MAYA_DEVKIT_DIR}")
message(STATUS "Maya includes     : ${Maya_INCLUDE_DIRS}")

# ─── C++ standard ────────────────────────────────────────────────────────────
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ─── Sources ─────────────────────────────────────────────────────────────────
set(SOURCES
    src/plugin_main.cpp
    src/read_pixels_cmd.cpp
    src/offscreen_override.cpp
)

set(HEADERS
    src/read_pixels_cmd.h
)

# ─── Plugin target ───────────────────────────────────────────────────────────
add_library(${PROJECT_NAME} SHARED ${SOURCES} ${HEADERS})

target_link_libraries(${PROJECT_NAME} PRIVATE Maya::Maya)

# Extension .mll sur Windows, .bundle sur Mac, .so sur Linux
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
    message(STATUS "Plugin output dir : ${PLUGIN_OUTPUT_DIR}")
endif()

# ─── Infos build ─────────────────────────────────────────────────────────────
message(STATUS "--------------------------------------------")
message(STATUS "  Project   : ${PROJECT_NAME} ${PROJECT_VERSION}")
message(STATUS "  Maya      : ${MAYA_VERSION}")
message(STATUS "  Platform  : ${CMAKE_SYSTEM_NAME}")
message(STATUS "  Build     : ${CMAKE_BUILD_TYPE}")
message(STATUS "--------------------------------------------")