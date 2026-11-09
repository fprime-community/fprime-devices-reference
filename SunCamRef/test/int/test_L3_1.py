"""L3-1: EXPOSURE persists across a restart

Procedure (plan.json, verbatim order):
  MARK(310)
  bracket (2 suncam samples)
  sunCamMgr.EXPOSURE_PRM_SET(400)
  wait(ExposureReadback, 5 s)
  sunCamMgr.EXPOSURE_PRM_SAVE
  prmDb.PRM_SAVE_FILE
  wait(prmDb.PrmFileSaveComplete, 10 s)
  bracket (2 suncam samples)
  MARK(311)
  action: bench reset (restart SunCamRef by recorded PID; ≥ 3 s settle)
  bracket (2 suncam samples)
  MARK(312)
  bracket (2 suncam samples)
  sunCamMgr.SETUP_CAMERA
  wait(SetupComplete, 15 s)
  sunCamMgr.EXPOSURE_PRM_SET(672)
  wait(ExposureReadback, 5 s)
  sunCamMgr.EXPOSURE_PRM_SAVE
  prmDb.PRM_SAVE_FILE
  wait(prmDb.PrmFileSaveComplete, 10 s)
  bracket (2 suncam samples)
  MARK(313)
"""
import pytest

from suncam import bracket, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-003', 'REQ-SunCamMgr-005', 'REQ-SunCamMgr-010', 'REQ-SunCamMgr-027')
def test_L3_1(fth_plan, window, check, require, send, bench):
    with window(310, 311):  # W1
        require("STD")
        check('event sunCamMgr.ExposureReadback(pushed=400, readback=400) count == 1')
        check('event prmDb.PrmFileSaveComplete count == 1')
        check('last(sunCamMgr.Exposure) == 400')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.EXPOSURE_PRM_SET", [400])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        send("sunCamMgr.EXPOSURE_PRM_SAVE", [])
        send("prmDb.PRM_SAVE_FILE", [])
        bench.wait_event("prmDb.PrmFileSaveComplete", 10)
        bracket(bench)
    with window(311, 312):  # R
        require('both markers present')
        check('ABS')
        check('last(sunCamMgr.SetupState) == NOT_SETUP')
        check('last(sunCamMgr.CurrentOperation) == NONE')
        check('event sunCamMgr.SetupComplete count == 0')
        check('last(sunCamMgr.Exchanges) == 0')
        bench.reset()  # action: bench reset (restart SunCamRef by recorded PID; ≥ 3 s settle)
        bracket(bench)
    with window(312, 313):  # W2
        require("STD")
        check('event sunCamMgr.SetupComplete(mode=SD, exposure=400) count == 1')
        check('event sunCamMgr.ExposureReadback(pushed=672, readback=672) count == 1')
        check('event prmDb.PrmFileSaveComplete count == 1')
        check('last(sunCamMgr.Exposure) == 672')
        check('last(sunCamMgr.SetupState) == READY')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.SETUP_CAMERA", [])
        bench.wait_event("sunCamMgr.SetupComplete", 15)
        send("sunCamMgr.EXPOSURE_PRM_SET", [672])
        bench.wait_event("sunCamMgr.ExposureReadback", 5)
        send("sunCamMgr.EXPOSURE_PRM_SAVE", [])
        send("prmDb.PRM_SAVE_FILE", [])
        bench.wait_event("prmDb.PrmFileSaveComplete", 10)
        bracket(bench)
