cmake_minimum_required(VERSION 3.12)

# Pull in SDK (must be before project)
include(pico_sdk_import.cmake)

project(pico_examples C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

if (PICO_SDK_VERSION_STRING VERSION_LESS "1.3.0")
    message(FATAL_ERROR "Raspberry Pi Pico SDK version 1.3.0 (or later) required. Your version is ${PICO_SDK_VERSION_STRING}")
endif()

set(PICO_EXAMPLES_PATH ${PROJECT_SOURCE_DIR})

# Initialize the SDK
pico_sdk_init()

#include(example_auto_set_url.cmake)

if (TARGET tinyusb_device)
    add_executable(stimote_control
            stimote_control.c
            )

    # pull in common dependencies
    target_link_libraries(stimote_control pico_stdlib pico_multicore hardware_pio)

    # enable usb output, disable uart output
    pico_enable_stdio_usb(stimote_control 0)
    pico_enable_stdio_uart(stimote_control 1)

    # make dac_control.pio.h
    pico_generate_pio_header(stimote_control ${CMAKE_CURRENT_LIST_DIR}/dac121s101.pio)
    pico_generate_pio_header(stimote_control ${CMAKE_CURRENT_LIST_DIR}/stream_monitor.pio)
    pico_generate_pio_header(stimote_control ${CMAKE_CURRENT_LIST_DIR}/clk_ext.pio)
    pico_generate_pio_header(stimote_control ${CMAKE_CURRENT_LIST_DIR}/cmp_ext.pio)

    # create map/bin/hex/uf2 file etc.
    pico_add_extra_outputs(stimote_control)

    # add url via pico_set_program_url
	#example_auto_set_url(dac_control)
elseif(PICO_ON_DEVICE)
    message(WARNING "not building hello_usb because TinyUSB submodule is not initialized in the SDK")
endif()

add_compile_options(-Wall
        -Wno-format          # int != int32_t as far as the compiler is concerned because gcc has int32_t as long int
        -Wno-unused-function # we have some for the docs that aren't called
        -Wno-maybe-uninitialized
        )

