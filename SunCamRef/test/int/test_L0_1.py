"""L0-1: Image identity and boot state

Procedure (plan.json, verbatim order):
  MARK(10)
  bracket (2 suncam samples)
  version.VERSION(ALL)
  bracket (2 suncam samples)
  MARK(11)
"""
import pytest

from suncam import bracket, flush, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-002', 'REQ-SunCamMgr-030')
def test_L0_1(fth_plan, window, check, require, send, bench):
    with window(10, 11):  # W
        require("STD")
        check('Svc.Version payloads == manifest repos[].describe (ProjectVersion = fprime-devices-reference, FrameworkVersion = fprime, LibraryVersions = fprime-devices@describe)',
              helper(fth_plan, "version_matches_manifest"))
        check('event version.FrameworkVersion count == 1')
        check('event version.ProjectVersion count == 1')
        check('last(sunCamMgr.SetupState) == NOT_SETUP')
        check('last(sunCamMgr.CurrentOperation) == NONE')
        check('last(sunCamMgr.Exchanges) == 0')
        check('event sunCamMgr.SetupComplete count == 0')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("version.VERSION", ['ALL'])
        bracket(bench)
    flush(send)
