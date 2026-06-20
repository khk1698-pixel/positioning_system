#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debug".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "app_common" for configuration "Debug"
set_property(TARGET app_common APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBUG)
set_target_properties(app_common PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_DEBUG "C"
  IMPORTED_LOCATION_DEBUG "${_IMPORT_PREFIX}/lib/libapp_common.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS app_common )
list(APPEND _IMPORT_CHECK_FILES_FOR_app_common "${_IMPORT_PREFIX}/lib/libapp_common.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
