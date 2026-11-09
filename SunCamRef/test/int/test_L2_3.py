"""L2-3: Capture test pattern and live frame

Procedure (plan.json, verbatim order):
  MARK(230)
  bracket (2 suncam samples)
  sunCamMgr.CAPTURE(SLOT_3, ON)
  wait(CaptureComplete, 10 s)
  sunCamMgr.CAPTURE(SLOT_0, OFF)
  wait(CaptureComplete, 10 s)
  bracket (2 suncam samples)
  MARK(231)
"""
import pytest

from suncam import bracket, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-001', 'REQ-SunCamMgr-013', 'REQ-SunCamMgr-022', 'REQ-SunCamMgr-025', 'REQ-SunCamMgr-033')
def test_L2_3(fth_plan, window, check, require, send, bench):
    with window(230, 231):  # W
        require("STD")
        check('event sunCamMgr.CaptureComplete(slot=SLOT_3, testPattern=ON, mode=SD) count == 1')
        check('event sunCamMgr.CaptureComplete(slot=SLOT_0, testPattern=OFF, exposure=672, mode=SD) count == 1')
        check('delta(sunCamMgr.ImagesCaptured) == 2')
        check('delta(sunCamMgr.CameraErrors) == 0')
        check('last(sunCamMgr.CurrentOperation) == NONE')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.CAPTURE", ['SLOT_3', 'ON'])
        bench.wait_event("sunCamMgr.CaptureComplete", 10)
        send("sunCamMgr.CAPTURE", ['SLOT_0', 'OFF'])
        bench.wait_event("sunCamMgr.CaptureComplete", 10)
        bracket(bench)
