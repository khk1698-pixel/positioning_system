#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debug".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Helpers" for configuration "Debug"
set_property(TARGET Helpers APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBUG)
set_target_properties(Helpers PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_DEBUG "C"
  IMPORTED_LOCATION_DEBUG "${_IMPORT_PREFIX}/lib/libHelpers.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS Helpers )
list(APPEND _IMPORT_CHECK_FILES_FOR_Helpers "${_IMPORT_PREFIX}/lib/libHelpers.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
