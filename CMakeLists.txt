####
# fprime-devices-reference: reference deployments for the fprime-devices libraries.
####
cmake_minimum_required(VERSION 3.26)
cmake_policy(SET CMP0048 NEW)
project(fprime-devices-reference VERSION 1.0.0 LANGUAGES C CXX)

include("${CMAKE_CURRENT_LIST_DIR}/lib/fprime/cmake/FPrime.cmake")

# Development only (fth dev-campaign, harness skill §3a): gcov-instrument the UUT source. Only files matching the
# filter are instrumented (KissCam/Components/SunCamMgr/SunCamMgr.cpp); CovDump reads the .gcda the hosted libgcov
# writes under this build cache. Placed before fprime_setup_included_code() so the options reach the library
# targets (directory scope). An image built with this option is never the RfR image.
option(SUNCAMREF_COVERAGE "gcov-instrument KissCam.SunCamMgr for fth dev-campaign (never an RfR image)" OFF)
if(SUNCAMREF_COVERAGE)
  add_compile_options(-fprofile-arcs -ftest-coverage -fprofile-update=single "-fprofile-filter-files=SunCamMgr\\.cpp$")
  add_link_options(--coverage)
  add_compile_definitions(SUNCAMREF_COVERAGE=1 "SUNCAMREF_GCDA_ROOT=\"${CMAKE_BINARY_DIR}\"")
endif()
fprime_setup_included_code()

add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/config-overrides/")
add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/SunCamRef/")
