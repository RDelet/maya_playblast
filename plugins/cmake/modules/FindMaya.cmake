# FindMaya.cmake
# Localise le Maya Devkit et définit les targets nécessaires
# pour compiler un plugin Maya.
#
# Variables d'entrée (à définir avant find_package) :
#   MAYA_VERSION       — Année Maya (ex: 2024, 2025)
#   MAYA_DEVKIT_DIR    — Chemin vers le devkit (optionnel, auto-détecté sinon)
#
# Variables de sortie :
#   Maya_FOUND
#   Maya_INCLUDE_DIRS
#   Maya_LIBRARY_DIRS
#   Maya_LIBRARIES
#   Maya_VERSION
#
# Target importé :
#   Maya::Maya

cmake_minimum_required(VERSION 3.13)

# ─── Chemins par défaut selon la plateforme ───────────────────────────────────
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

# Vérifie si le dossier existe
if(EXISTS "${MAYA_DEVKIT_DIR}")
    message(STATUS "Dossier Maya EXISTS")
else()
    message(STATUS "ERREUR : Dossier Maya INTROUVABLE")
endif()

# Vérifie le dossier include
if(EXISTS "${MAYA_DEVKIT_DIR}/include")
    message(STATUS "include/ EXISTS")
else()
    message(STATUS "ERREUR : include/ INTROUVABLE")
endif()

# Vérifie MFnPlugin.h spécifiquement
if(EXISTS "${MAYA_DEVKIT_DIR}/include/maya/MFnPlugin.h")
    message(STATUS "MFnPlugin.h EXISTS")
else()
    message(STATUS "ERREUR : MFnPlugin.h INTROUVABLE")
endif()

# Vérifie le dossier lib
if(EXISTS "${MAYA_DEVKIT_DIR}/lib")
    message(STATUS "lib/ EXISTS")
    file(GLOB _MAYA_LIBS_FOUND "${MAYA_DEVKIT_DIR}/lib/*.lib")
    foreach(_f ${_MAYA_LIBS_FOUND})
        message(STATUS "  lib trouvée : ${_f}")
    endforeach()
else()
    message(STATUS "ERREUR : lib/ INTROUVABLE")
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

# ─── Target importé Maya::Maya ───────────────────────────────────────────────
if(Maya_FOUND AND NOT TARGET Maya::Maya)
    add_library(Maya::Maya INTERFACE IMPORTED)
    target_include_directories(Maya::Maya INTERFACE "${Maya_INCLUDE_DIRS}")
    target_link_directories(Maya::Maya INTERFACE "${Maya_LIBRARY_DIRS}")
    target_link_libraries(Maya::Maya INTERFACE ${Maya_LIBRARIES})

    # Flags nécessaires pour les plugins Maya
    target_compile_definitions(Maya::Maya INTERFACE
        REQUIRE_IOSTREAM
        _BOOL
        $<$<PLATFORM_ID:Windows>:NT_PLUGIN WIN32 _WINDOWS>
        $<$<PLATFORM_ID:Darwin>:MAC_PLUGIN OSMac_ OSMac_MachO>
        $<$<PLATFORM_ID:Linux>:LINUX LINUX_64>
    )

    # Flags de compilation
    if(WIN32)
        target_compile_options(Maya::Maya INTERFACE /EHsc)
    else()
        target_compile_options(Maya::Maya INTERFACE -fPIC)
    endif()
endif()
