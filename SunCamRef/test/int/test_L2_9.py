"""L2-9: CAMERA_MODE push re-pushes exposure

Procedure (plan.json, verbatim order):
  MARK(290)
  bracket (2 suncam samples)
  sunCamMgr.EXPOSURE_PRM_SET(300)
  wait(ExposureReadback, 5 s)
  sunCamMgr.CAMERA_MODE_PRM_SET(HD)
  wait(ExposureReadback, 5 s)
  sunCamMgr.CAMERA_MODE_PRM_SET(SD)
  wait(ExposureReadback, 5 s)
  sunCamMgr.EXPOSURE_PRM_SET(672)
  wait(ExposureReadback, 5 s)
  bracket (2 suncam samples)
  MARK(291)
"""
import pytest

from suncam import bracket, flush, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-010', 'REQ-SunCamMgr-012', 'REQ-SunCamMgr-023', 'REQ-SunCamMgr-027')
def test_L2_9(fth_plan, window, check, require, send, bench):
    with window(290, 291):  # W
        require("STD")
        check('event sunCamMgr.SettingApplied(setting=CAMERA_MODE, value=2) count == 1')
        check('event sunCamMgr.SettingApplied(setting=CAMERA_MODE, value=1) count == 1')
        check('event sunCamMgr.SettingApplied(setting=EXPOSURE, value=300) count == 3')
        check('event sunCamMgr.ExposureReadback(pushed=300, readback=300) count == 3')
        check('event sunCamMgr.SettingApplied(setting=EXPOSURE, value=672) count == 1')
        check('event sunCamMgr.SettingPushFailed count == 0')
        check('last(sunCamMgr.CameraMode) == SD')
        check('last(sunCamMgr.Exposure) == 672')
        check('last(sunCamMgr.SetupState) == READY')
        check('delta(sunCamMgr.Exchanges) == 10')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.EXPOSURE_PRM_SET", [300])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        send("sunCamMgr.CAMERA_MODE_PRM_SET", ['HD'])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        send("sunCamMgr.CAMERA_MODE_PRM_SET", ['SD'])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        send("sunCamMgr.EXPOSURE_PRM_SET", [672])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        bracket(bench)
    flush(send)
