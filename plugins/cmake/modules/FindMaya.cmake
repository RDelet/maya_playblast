# FindMaya.cmake
# Locates the Maya Devkit and defines the required targets
# to build a Maya plugin.
#
# Input variables (to define before find_package):
#   MAYA_VERSION       — Maya year (e.g: 2024, 2025)
#   MAYA_DEVKIT_DIR    — Path to the devkit (optional, auto-detected otherwise)
#
# Output variables:
#   Maya_FOUND
#   Maya_INCLUDE_DIRS
#   Maya_LIBRARY_DIRS
#   Maya_LIBRARIES
#   Maya_VERSION
#
# Imported target:
#   Maya::Maya

cmake_minimum_required(VERSION 3.13)

# ─── Default platform-specific paths ─────────────────────────────────────────
if(NOT MAYA_VERSION)
    set(MAYA_VERSION "2025" CACHE STRING "Maya version year")
endif()

if(WIN32)
    set(_MAYA_DEFAULT_LOCATION "C:/Program Files/Autodesk/Maya${MAYA_VERSION}")
elseif(APPLE)
    set(_MAYA_DEFAULT_LOCATION "/Applications/Autodesk/maya${MAYA_VERSION}/Maya.app/Contents")
else()
    set(_MAYA_DEFAULT_LOCATION "/usr/autodesk/maya${MAYA_VERSION}")
endif()

if(NOT MAYA_DEVKIT_DIR)
    set(MAYA_DEVKIT_DIR "${_MAYA_DEFAULT_LOCATION}" CACHE PATH "Maya devkit location")
endif()

# ─── Includes ────────────────────────────────────────────────────────────────
message(STATUS "=== FindMaya Debug ===")
message(STATUS "MAYA_DEVKIT_DIR : ${MAYA_DEVKIT_DIR}")

# Check if directory exists
if(EXISTS "${MAYA_DEVKIT_DIR}")
    message(STATUS "Maya directory EXISTS")
else()
    message(STATUS "ERROR: Maya directory NOT FOUND")
endif()

# Check include folder
if(EXISTS "${MAYA_DEVKIT_DIR}/include")
    message(STATUS "include/ EXISTS")
else()
    message(STATUS "ERROR: include/ NOT FOUND")
endif()

# Specifically check MFnPlugin.h
if(EXISTS "${MAYA_DEVKIT_DIR}/include/maya/MFnPlugin.h")
    message(STATUS "MFnPlugin.h EXISTS")
else()
    message(STATUS "ERROR: MFnPlugin.h NOT FOUND")
endif()

# Check lib folder
if(EXISTS "${MAYA_DEVKIT_DIR}/lib")
    message(STATUS "lib/ EXISTS")
    file(GLOB _MAYA_LIBS_FOUND "${MAYA_DEVKIT_DIR}/lib/*.lib")
    foreach(_f ${_MAYA_LIBS_FOUND})
        message(STATUS "  library found : ${_f}")
    endforeach()
else()
    message(STATUS "ERROR: lib/ NOT FOUND")
endif()
message(STATUS "=== FindMaya Debug End ===")

find_path(Maya_INCLUDE_DIRS
    NAMES maya/MFnPlugin.h
    PATHS
        "${MAYA_DEVKIT_DIR}/include"
        "${MAYA_DEVKIT_DIR}/devkit/include"
    NO_DEFAULT_PATH
)

# ─── Libraries ───────────────────────────────────────────────────────────────
if(WIN32)
    set(_MAYA_LIB_DIR "${MAYA_DEVKIT_DIR}/lib")
    set(_MAYA_LIBS OpenMaya OpenMayaUI OpenMayaRender Foundation)
elseif(APPLE)
    set(_MAYA_LIB_DIR "${MAYA_DEVKIT_DIR}/Maya.app/Contents/MacOS")
    set(_MAYA_LIBS OpenMaya OpenMayaUI OpenMayaRender Foundation)
else()
    set(_MAYA_LIB_DIR "${MAYA_DEVKIT_DIR}/lib")
    set(_MAYA_LIBS OpenMaya OpenMayaUI OpenMayaRender Foundation)
endif()

set(Maya_LIBRARY_DIRS "${_MAYA_LIB_DIR}")
set(Maya_LIBRARIES "")

foreach(_lib ${_MAYA_LIBS})
    find_library(_MAYA_${_lib}_LIB
        NAMES ${_lib}
        PATHS "${_MAYA_LIB_DIR}"
        NO_DEFAULT_PATH
    )
    if(_MAYA_${_lib}_LIB)
        list(APPEND Maya_LIBRARIES "${_MAYA_${_lib}_LIB}")
    endif()
    unset(_MAYA_${_lib}_LIB CACHE)
endforeach()

# ─── Validation ──────────────────────────────────────────────────────────────
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Maya
    REQUIRED_VARS Maya_INCLUDE_DIRS Maya_LIBRARIES
    VERSION_VAR   MAYA_VERSION
)

# ─── Imported target Maya::Maya ──────────────────────────────────────────────
if(Maya_FOUND AND NOT TARGET Maya::Maya)
    add_library(Maya::Maya INTERFACE IMPORTED)
    target_include_directories(Maya::Maya INTERFACE "${Maya_INCLUDE_DIRS}")
    target_link_directories(Maya::Maya INTERFACE "${Maya_LIBRARY_DIRS}")
    target_link_libraries(Maya::Maya INTERFACE ${Maya_LIBRARIES})

    # Required definitions for Maya plugins
    target_compile_definitions(Maya::Maya INTERFACE
        REQUIRE_IOSTREAM
        _BOOL
        $<$<PLATFORM_ID:Windows>:NT_PLUGIN WIN32 _WINDOWS>
        $<$<PLATFORM_ID:Darwin>:MAC_PLUGIN OSMac_ OSMac_MachO>
        $<$<PLATFORM_ID:Linux>:LINUX LINUX_64>
    )

    # Compile flags
    if(WIN32)
        target_compile_options(Maya::Maya INTERFACE /EHsc)
    else()
        target_compile_options(Maya::Maya INTERFACE -fPIC)
    endif()
endif()