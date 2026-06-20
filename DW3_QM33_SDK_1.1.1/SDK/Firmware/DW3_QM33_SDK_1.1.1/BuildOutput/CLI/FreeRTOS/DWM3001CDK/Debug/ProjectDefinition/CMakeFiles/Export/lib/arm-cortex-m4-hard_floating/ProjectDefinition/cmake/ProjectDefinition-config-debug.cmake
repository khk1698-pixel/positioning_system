#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debug".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "ProjectDefinition" for configuration "Debug"
set_property(TARGET ProjectDefinition APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBUG)
set_target_properties(ProjectDefinition PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_DEBUG "C"
  IMPORTED_LOCATION_DEBUG "${_IMPORT_PREFIX}/lib/libProjectDefinition.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS ProjectDefinition )
list(APPEND _IMPORT_CHECK_FILES_FOR_ProjectDefinition "${_IMPORT_PREFIX}/lib/libProjectDefinition.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
