"""L5-3: Out-of-range exposure refused locally; set-up fails before Set Exposure

Procedure (plan.json, verbatim order):
  MARK(530)
  bracket (2 suncam samples)
  sunCamMgr.EXPOSURE_PRM_SET(1)
  wait(SettingRejected, 5 s)
  sunCamMgr.SETUP_CAMERA
  wait(SetupFailed, 15 s)
  sunCamMgr.EXPOSURE_PRM_SET(672)
  wait(2 s)
  sunCamMgr.SETUP_CAMERA
  wait(SetupComplete, 15 s)
  bracket (2 suncam samples)
  MARK(531)
"""
import pytest

from suncam import bracket, flush, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-002', 'REQ-SunCamMgr-004', 'REQ-SunCamMgr-031')
def test_L5_3(fth_plan, window, check, require, send, bench):
    with window(530, 531):  # W
        require("STD")
        check('event sunCamMgr.SettingRejected(setting=EXPOSURE, value=1, min=2, max=960) count == 2')
        check('event sunCamMgr.SetupFailed(step=SET_EXPOSURE, cause=OUT_OF_RANGE) count == 1')
        check('event sunCamMgr.SettingPushFailed count == 0')
        check('event sunCamMgr.SetupComplete(mode=SD, exposure=672) count == 1')
        check('event sunCamMgr.CameraError count == 0')
        check('event sunCamMgr.SettingApplied(setting=EXPOSURE, value=672) count == 1')
        check('event sunCamMgr.ExposureReadback(pushed=672, readback=672) count == 1')
        check("CameraValidCmds between the failed set-up's Ping MCU reply and the successful set-up's Ping MCU+sensor reply = 6 frames (Set Mode, Ping MCU, Set Mode, Set Exposure, Read Register, Ping MCU+sensor): none for exposure 1 (mod 256)",
              helper(fth_plan, "delta_mod", channel='sunCamMgr.CameraValidCmds', delta=6, mod=256))
        check('delta(sunCamMgr.Exchanges) == 7')
        check('delta(sunCamMgr.CameraErrors) == 0')
        check('last(sunCamMgr.SetupState) == READY')
        check('last(sunCamMgr.CameraMode) == SD')
        check('last(sunCamMgr.Exposure) == 672')
        check('event cmdDisp.OpCodeError count == 1')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.EXPOSURE_PRM_SET", [1], wait_completion=False)  # plan expects the UUT to refuse this command (OpCodeError)
        bench.wait_event("sunCamMgr.SettingRejected", 5)
        send("sunCamMgr.SETUP_CAMERA", [], wait_completion=False)  # plan expects the UUT to refuse this command (OpCodeError)
        bench.wait_event("sunCamMgr.SetupFailed", 15)
        send("sunCamMgr.EXPOSURE_PRM_SET", [672], wait_completion=False)  # plan expects the UUT to refuse this command (OpCodeError)
        bench.wait(2)
        send("sunCamMgr.SETUP_CAMERA", [])
        bench.wait_event("sunCamMgr.SetupComplete", 15)
        bracket(bench)
    flush(send)
