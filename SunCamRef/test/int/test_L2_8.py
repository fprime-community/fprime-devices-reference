"""L2-8: Register read of the exposure register

Procedure (plan.json, verbatim order):
  MARK(280)
  bracket (2 suncam samples)
  sunCamMgr.SETUP_CAMERA
  wait(SetupComplete, 15 s)
  sunCamMgr.EXPOSURE_PRM_SET(300)
  wait(ExposureReadback, 5 s)
  sunCamMgr.READ_REGISTER(12306)
  wait(RegisterRead or CameraError, 5 s)
  sunCamMgr.EXPOSURE_PRM_SET(672)
  wait(ExposureReadback, 5 s)
  bracket (2 suncam samples)
  MARK(281)
"""
import pytest

from suncam import bracket, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-012', 'REQ-SunCamMgr-025')
def test_L2_8(fth_plan, window, check, require, send, bench):
    with window(280, 281):  # W
        require("STD")
        check('event sunCamMgr.SetupComplete(mode=SD, exposure=672) count == 1')
        check('event sunCamMgr.SettingApplied(setting=EXPOSURE, value=300) count == 1')
        check('event sunCamMgr.ExposureReadback(pushed=300, readback=300) count == 1')
        check('event sunCamMgr.RegisterRead(address=3012, value=300) count == 1')
        check('event sunCamMgr.SettingApplied(setting=EXPOSURE, value=672) count == 1')
        check('last(sunCamMgr.Exposure) == 672')
        check('last(sunCamMgr.SetupState) == READY')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.SETUP_CAMERA", [])
        bench.wait_event("sunCamMgr.SetupComplete", 15)
        send("sunCamMgr.EXPOSURE_PRM_SET", [300])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        send("sunCamMgr.READ_REGISTER", [12306])
        wait_any(bench, ["sunCamMgr.RegisterRead", "sunCamMgr.CameraError"], 5)
        send("sunCamMgr.EXPOSURE_PRM_SET", [672])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        bracket(bench)
