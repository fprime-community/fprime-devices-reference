"""L2-4: Preview download → Image data product (decoded)

Procedure (plan.json, verbatim order):
  MARK(240)
  bracket (2 suncam samples)
  sunCamMgr.DOWNLOAD(SLOT_4, PREVIEW)
  wait(DownloadComplete, 20 s)
  bracket (2 suncam samples)
  MARK(241)
"""
import pytest

from suncam import bracket, flush, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-001', 'REQ-SunCamMgr-014', 'REQ-SunCamMgr-015')
def test_L2_4(fth_plan, window, check, require, send, bench):
    with window(240, 241):  # W
        require("STD")
        check('event sunCamMgr.DownloadStarted(slot=SLOT_4, imageMode=SD, resolution=PREVIEW, lines=60) count == 1')
        check('event sunCamMgr.DownloadComplete(slot=SLOT_4, imageMode=SD, resolution=PREVIEW, lines=60, bytes=4800) count == 1')
        check('event sunCamMgr.MemoryStatusReply count == 1')
        check('event sunCamMgr.LineRetry count == 0')
        check('event sunCamMgr.DownloadAborted count == 0')
        check('delta(sunCamMgr.LinesDownloaded) == 60')
        check('delta(sunCamMgr.ProductsSent) == 1')
        check('last(dpMgr.NumDataProducts) == 1')
        check('exactly one Image product in record/raw/dp/ with header time in [t(START), t(END)]: ImageHeader(slot=4, imageMode=SD, resolution=PREVIEW, width=80, height=60), 60 slot-tagged ImageLine records in order; PNG → dev-evidence/images/L2-4-preview.png',
              helper(fth_plan, "decode_image_in_window", slot=4, image_mode='SD', resolution='PREVIEW', width=80, height=60, lines=60, expect='none', out='L2-4-preview.png'))
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.DOWNLOAD", ['SLOT_4', 'PREVIEW'])
        bench.wait_event("sunCamMgr.DownloadComplete", 20)
        bracket(bench)
    flush(send)
