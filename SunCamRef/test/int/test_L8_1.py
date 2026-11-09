"""L8-1: Camera power-on (human step; run-for-record only, DEFERRED in rehearsal and dry runs) → set-up

Procedure (plan.json, verbatim order):
  MARK(810)
  bracket (2 suncam samples)
  sunCamMgr.SLEEP
  wait(SleepEntered, 5 s)
  bracket (2 suncam samples)
  MARK(812)
  human step (runner prompt: human_step)
  wait(3 s)
  sunCamMgr.SETUP_CAMERA
  wait(SetupComplete, 15 s)
  bracket (2 suncam samples)
  MARK(811)
"""
import pytest

from suncam import bracket, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-003', 'REQ-SunCamMgr-020', 'REQ-SunCamMgr-034', 'REQ-SunCamMgr-036')
def test_L8_1(fth_plan, window, check, require, send, bench):
    with window(810, 812):  # W1
        require("STD")
        check('event sunCamMgr.SleepEntered count == 1')
        check('last(sunCamMgr.SetupState) == NOT_SETUP')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.SLEEP", [])
        bench.wait_event("sunCamMgr.SleepEntered", 5)
        bracket(bench)
    with window(812, 811):  # W
        require("STD")
        check('event sunCamMgr.FrameDiscarded(cause=MALFORMED, bytes=21) count == 1')
        check('delta(sunCamMgr.DiscardedBytes) == 21')
        check('event sunCamMgr.CameraRestarted count == 0')
        check('event sunCamMgr.SetupComplete(mode=SD, exposure=672) count == 1')
        check('last(sunCamMgr.SetupState) == READY')
        check('last(sunCamMgr.CameraMode) == SD')
        check('event cmdDisp.OpCodeError count == 0')
        check('event sunCamMgr.QueueOverflow count == 0')
        check('event sunCamMgr.SendFailed count == 0')
        check('event sunCamMgr.ProductAllocationFailed count == 0')
        check('event sunCamMgr.ModeMismatch count == 0')
        check('event sunCamMgr.ReplyTimeout count == 0')
        check('event sunCamMgr.DownloadFailed count == 0')
        # human step (runner prompt: human_step): operator prompt + typed `CONFIRM L8-1` here (phase rfr; recorded in record/human/); a no-op
        # in every other phase, where the test is DEFERRED (fth v0.1.5 positional human step)
        bench.human_step('L8-1', 'The component is NOT_SETUP. Confirm the camera is OFF (unplug its USB power if it is on, wait 5 s); power it ON; type CONFIRM when its LED/power is on.')
        bench.wait(3)
        send("sunCamMgr.SETUP_CAMERA", [])
        bench.wait_event("sunCamMgr.SetupComplete", 15)
        bracket(bench)
