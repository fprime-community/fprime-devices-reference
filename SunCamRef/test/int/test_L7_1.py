"""L7-1: Final state: test-pattern capture, preview product on disk

Procedure (plan.json, verbatim order):
  MARK(710)
  bracket (2 suncam samples)
  sunCamMgr.CAPTURE(SLOT_4, ON)
  wait(CaptureComplete, 10 s)
  sunCamMgr.DOWNLOAD(SLOT_4, PREVIEW)
  wait(DownloadComplete, 20 s)
  sunCamMgr.MEMORY_STATUS
  wait(MemoryStatusReply, 5 s)
  bracket (2 suncam samples)
  MARK(711)
"""
import pytest

from suncam import bracket, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-001', 'REQ-SunCamMgr-013', 'REQ-SunCamMgr-015')
def test_L7_1(fth_plan, window, check, require, send, bench):
    with window(710, 711):  # W
        require("STD")
        check('event sunCamMgr.CaptureComplete(slot=SLOT_4, testPattern=ON, mode=SD) count == 1')
        check('event sunCamMgr.DownloadComplete(slot=SLOT_4, imageMode=SD, resolution=PREVIEW, lines=60, bytes=4800) count == 1')
        check('event sunCamMgr.MemoryStatusReply count == 2')
        check('event sunCamMgr.CommandRejected count == 0')
        check('delta(sunCamMgr.ImagesCaptured) == 1')
        check('delta(sunCamMgr.ProductsSent) == 1')
        check('last(dpMgr.NumDataProducts) == 2')
        check('last(sunCamMgr.SetupState) == READY')
        check('exactly one Image product in window: ImageHeader(slot=4, imageMode=SD, resolution=PREVIEW, width=80, height=60), 60 lines in order; PNG → dev-evidence/images/L7-1-final.png',
              helper(fth_plan, "decode_image_in_window", slot=4, image_mode='SD', resolution='PREVIEW', width=80, height=60, lines=60, expect='none', out='L7-1-final.png'))
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.CAPTURE", ['SLOT_4', 'ON'])
        bench.wait_event("sunCamMgr.CaptureComplete", 10)
        send("sunCamMgr.DOWNLOAD", ['SLOT_4', 'PREVIEW'])
        bench.wait_event("sunCamMgr.DownloadComplete", 20)
        send("sunCamMgr.MEMORY_STATUS", [])
        bench.wait_event("sunCamMgr.MemoryStatusReply", 5)
        bracket(bench)
