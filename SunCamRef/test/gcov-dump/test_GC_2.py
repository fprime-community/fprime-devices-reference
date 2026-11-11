"""GC-2: gcov dump range check (negative control)

Procedure (test/gcov-dump/plan.json, verbatim order):
  MARK(910)
  covDump.DUMP_COVERAGE(65535, 1)
  wait(covDump.CoverageDumpError or covDump.CoverageChunk, 5 s)
  MARK(911)
"""
import pytest


@pytest.mark.req('GC-RANGE')
def test_GC_2(fth_plan, window, check, require, send, bench):
    with window(910, 911):  # W
        require("STD")
        check('event covDump.CoverageDumpError count == 1')
        check('event cmdDisp.OpCodeError count == 1')
        check('event covDump.CoverageDumpDone count == 0')
        check('event covDump.CoverageChunk count == 0')
        send("covDump.DUMP_COVERAGE", [65535, 1], wait_completion=False)  # rejected: no OpCodeCompleted
        bench.wait_any_event(["covDump.CoverageDumpError", "covDump.CoverageChunk"], 5.0)
