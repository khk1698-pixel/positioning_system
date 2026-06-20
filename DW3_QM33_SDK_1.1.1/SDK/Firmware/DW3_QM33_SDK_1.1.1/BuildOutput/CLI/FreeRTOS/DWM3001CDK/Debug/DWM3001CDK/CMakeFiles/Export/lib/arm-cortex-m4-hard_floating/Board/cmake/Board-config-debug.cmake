#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debug".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Board" for configuration "Debug"
set_property(TARGET Board APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBUG)
set_target_properties(Board PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_DEBUG "C"
  IMPORTED_LOCATION_DEBUG "${_IMPORT_PREFIX}/lib/libBoard.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS Board )
list(APPEND _IMPORT_CHECK_FILES_FOR_Board "${_IMPORT_PREFIX}/lib/libBoard.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
