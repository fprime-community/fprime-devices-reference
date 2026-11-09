"""L2-6: EXPOSURE parameter push and readback

Procedure (plan.json, verbatim order):
  MARK(260)
  bracket (2 suncam samples)
  sunCamMgr.EXPOSURE_PRM_SET(300)
  wait(ExposureReadback, 5 s)
  sunCamMgr.EXPOSURE_PRM_SET(672)
  wait(ExposureReadback, 5 s)
  bracket (2 suncam samples)
  MARK(261)
"""
import pytest

from suncam import bracket, flush, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-010', 'REQ-SunCamMgr-012', 'REQ-SunCamMgr-023')
def test_L2_6(fth_plan, window, check, require, send, bench):
    with window(260, 261):  # W
        require("STD")
        check('event sunCamMgr.SettingApplied(setting=EXPOSURE, value=300) count == 1')
        check('event sunCamMgr.ExposureReadback(pushed=300, readback=300) count == 1')
        check('event sunCamMgr.SettingApplied(setting=EXPOSURE, value=672) count == 1')
        check('event sunCamMgr.ExposureReadback(pushed=672, readback=672) count == 1')
        check('event sunCamMgr.SettingPushFailed count == 0')
        check('last(sunCamMgr.Exposure) == 672')
        check('last(sunCamMgr.SetupState) == READY')
        check('delta(sunCamMgr.Exchanges) == 4')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.EXPOSURE_PRM_SET", [300])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        send("sunCamMgr.EXPOSURE_PRM_SET", [672])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        bracket(bench)
    flush(send)
