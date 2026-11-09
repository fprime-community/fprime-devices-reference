"""L2-1: Set-up from NOT_SETUP and re-entrant from READY

Procedure (plan.json, verbatim order):
  MARK(210)
  bracket (2 suncam samples)
  sunCamMgr.SETUP_CAMERA
  wait(SetupComplete, 15 s)
  bracket (2 suncam samples)
  MARK(212)
  bracket (2 suncam samples)
  sunCamMgr.EXPOSURE_PRM_SET(300)
  wait(ExposureReadback, 5 s)
  sunCamMgr.SETUP_CAMERA
  wait(SetupComplete, 15 s)
  sunCamMgr.EXPOSURE_PRM_SET(672)
  wait(ExposureReadback, 5 s)
  bracket (2 suncam samples)
  MARK(211)
"""
import pytest

from suncam import bracket, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-001', 'REQ-SunCamMgr-003', 'REQ-SunCamMgr-005', 'REQ-SunCamMgr-012', 'REQ-SunCamMgr-022', 'REQ-SunCamMgr-023')
def test_L2_1(fth_plan, window, check, require, send, bench):
    with window(210, 212):  # W1
        require("STD")
        check('event sunCamMgr.SetupStarted count == 1')
        check('event sunCamMgr.SetupComplete(mode=SD, exposure=672) count == 1')
        check('event sunCamMgr.SettingApplied(setting=CAMERA_MODE, value=1) count == 1')
        check('event sunCamMgr.SettingApplied(setting=EXPOSURE, value=672) count == 1')
        check('event sunCamMgr.ExposureReadback(pushed=672, readback=672) count == 1')
        check('event sunCamMgr.SetupFailed count == 0')
        check('last(sunCamMgr.SetupState) == READY')
        check('last(sunCamMgr.CameraMode) == SD')
        check('last(sunCamMgr.Exposure) == 672')
        check('last(sunCamMgr.ExposureReadback) == 672')
        check('delta(sunCamMgr.Exchanges) == 5')
        check('delta(sunCamMgr.CameraErrors) == 0')
        check('last(sunCamMgr.CurrentOperation) == NONE')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.SETUP_CAMERA", [])
        bench.wait_event("sunCamMgr.SetupComplete", 15)
        bracket(bench)
    with window(212, 211):  # W2
        require("STD")
        check('event sunCamMgr.SetupStarted count == 1')
        check('event sunCamMgr.SetupComplete(mode=SD, exposure=300) count == 1')
        check('event sunCamMgr.SettingApplied(setting=EXPOSURE, value=300) count == 2')
        check('event sunCamMgr.ExposureReadback(pushed=300, readback=300) count == 2')
        check('event sunCamMgr.SettingApplied(setting=EXPOSURE, value=672) count == 1')
        check('event sunCamMgr.ExposureReadback(pushed=672, readback=672) count == 1')
        check('event sunCamMgr.SetupFailed count == 0')
        check('last(sunCamMgr.SetupState) == READY')
        check('delta(sunCamMgr.Exchanges) == 9')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.EXPOSURE_PRM_SET", [300])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        send("sunCamMgr.SETUP_CAMERA", [])
        bench.wait_event("sunCamMgr.SetupComplete", 15)
        send("sunCamMgr.EXPOSURE_PRM_SET", [672])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        bracket(bench)
