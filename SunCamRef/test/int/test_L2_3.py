"""L2-3: Capture test pattern and live frame; memory status

Procedure (plan.json, verbatim order):
  MARK(230)
  bracket (2 suncam samples)
  sunCamMgr.CAPTURE(SLOT_4, ON)
  wait(CaptureComplete, 10 s)
  sunCamMgr.CAPTURE(SLOT_1, OFF)
  wait(CaptureComplete, 10 s)
  sunCamMgr.MEMORY_STATUS
  wait(MemoryStatusReply, 5 s)
  bracket (2 suncam samples)
  MARK(231)
"""
import pytest

from suncam import bracket, flush, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-001', 'REQ-SunCamMgr-013', 'REQ-SunCamMgr-022', 'REQ-SunCamMgr-025')
def test_L2_3(fth_plan, window, check, require, send, bench):
    with window(230, 231):  # W
        require("STD")
        check('event sunCamMgr.CaptureComplete(slot=SLOT_4, testPattern=ON, mode=SD) count == 1')
        check('event sunCamMgr.CaptureComplete(slot=SLOT_1, testPattern=OFF, exposure=672, mode=SD) count == 1')
        check('event sunCamMgr.MemoryStatusReply count == 1')
        check('last(MemorySlots): slot 4 exposure 0 (test pattern, §7.4.3) and slot 1 exposure 672',
              helper(fth_plan, "memory_slot_exposure", slot4=0, slot1=672))
        check('delta(sunCamMgr.ImagesCaptured) == 2')
        check('delta(sunCamMgr.CameraErrors) == 0')
        check('last(sunCamMgr.CurrentOperation) == NONE')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.CAPTURE", ['SLOT_4', 'ON'])
        bench.wait_event("sunCamMgr.CaptureComplete", 10)
        send("sunCamMgr.CAPTURE", ['SLOT_1', 'OFF'])
        bench.wait_event("sunCamMgr.CaptureComplete", 10)
        send("sunCamMgr.MEMORY_STATUS", [])
        bench.wait_event("sunCamMgr.MemoryStatusReply", 5)
        bracket(bench)
    flush(send)
