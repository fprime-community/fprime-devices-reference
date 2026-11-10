"""GC-1: gcov dump of the instrumented image

Procedure (test/gcov-dump/plan.json, verbatim order):
  MARK(900)
  covDump.DUMP_COVERAGE(0, 0)
  MARK(901)
"""
import pytest


@pytest.mark.req('GC-DUMP')
def test_GC_1(fth_plan, window, check, require, send, bench):
    with window(900, 901):  # W
        require("STD")
        check('event covDump.CoverageDumpDone count == 1')
        check('event covDump.CoverageObject count >= 1')
        check('event covDump.CoverageChunk count >= 1')
        check('event covDump.CoverageChunk(object=0, offset=0) count == 1')
        check('ABS')
        send("covDump.DUMP_COVERAGE", [0, 0])  # the response follows the last chunk (paced 4 per 10 Hz tick)
