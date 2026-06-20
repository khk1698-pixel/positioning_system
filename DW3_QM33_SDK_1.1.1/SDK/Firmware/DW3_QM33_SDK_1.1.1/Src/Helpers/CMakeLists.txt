# SPDX-FileCopyrightText: Copyright (c) 2025 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

add_library(Helpers STATIC cJSON.c circular_buffer.c uwb_convert.c)

if(USE_DIAG_PRINTF)
  target_sources(Helpers PRIVATE deca_dbg.c)
endif()

target_include_directories(Helpers PUBLIC Inc
    E:/polytech/uwb/DW3_QM33_SDK_1.1.1/SDK/Firmware/DW3_QM33_SDK_1.1.1/Libs/uwbstack_libs/delivery/fira/Release/include/uwbstack_bundle
)

target_link_libraries(Helpers PUBLIC OSAL)

install(TARGETS Helpers EXPORT Helpers-config)
install(EXPORT Helpers-config DESTINATION lib/${CMAKE_LIBRARY_ARCHITECTURE}/Helpers/cmake)
