####
# SunCamRef: KissCam.SunCamMgr on a POSIX UART, with the standard CdhCore / ComFprime /
# DataProducts / FileHandling subtopologies. System test under test/int/.
####
add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/CovDump/")
add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/Top/")

register_fprime_deployment(
    SOURCES
        "${CMAKE_CURRENT_LIST_DIR}/Main.cpp"
    DEPENDS
        SunCamRef_Top
)
