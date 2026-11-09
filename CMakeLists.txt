####
# fprime-devices-reference: reference deployments for the fprime-devices libraries.
####
cmake_minimum_required(VERSION 3.26)
cmake_policy(SET CMP0048 NEW)
project(fprime-devices-reference VERSION 1.0.0 LANGUAGES C CXX)

include("${CMAKE_CURRENT_LIST_DIR}/lib/fprime/cmake/FPrime.cmake")
fprime_setup_included_code()

add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/config-overrides/")
add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/SunCamRef/")
