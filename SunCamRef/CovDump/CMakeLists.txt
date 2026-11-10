####
# SunCamRef.CovDump: development-only gcov dump (fth coverage-system contract). Built into every SunCamRef
# image; only a -DSUNCAMREF_COVERAGE=ON build (root CMakeLists.txt) gives it instrumentation to dump.
####
register_fprime_module(
  AUTOCODER_INPUTS
    "${CMAKE_CURRENT_LIST_DIR}/CovDump.fpp"
  SOURCES
    "${CMAKE_CURRENT_LIST_DIR}/CovDump.cpp"
  HEADERS
    "${CMAKE_CURRENT_LIST_DIR}/CovDump.hpp"
)
