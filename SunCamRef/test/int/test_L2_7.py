"""L2-7: Sleep from READY and from NOT_SETUP; READY-only command rejected

Procedure (plan.json, verbatim order):
  MARK(270)
  bracket (2 suncam samples)
  sunCamMgr.SLEEP
  wait(SleepEntered, 5 s)
  sunCamMgr.SLEEP
  wait(SleepEntered, 5 s)
  sunCamMgr.CAPTURE(SLOT_1, OFF)
  wait(CommandRejected, 5 s)
  sunCamMgr.PING(MCU)
  wait(PingReply, 5 s)
  bracket (2 suncam samples)
  MARK(271)
"""
import pytest

from suncam import bracket, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-006', 'REQ-SunCamMgr-007', 'REQ-SunCamMgr-008')
def test_L2_7(fth_plan, window, check, require, send, bench):
    with window(270, 271):  # W
        require("STD")
        check('event sunCamMgr.SleepEntered count == 2')
        check('event sunCamMgr.CommandRejected(operation=CAPTURE, cause=NOT_READY) count == 1')
        check('event sunCamMgr.PingReply(pingType=MCU) count == 1')
        check('event sunCamMgr.CommandRejected count == 1')
        check('last(sunCamMgr.SetupState) == NOT_SETUP')
        check('delta(sunCamMgr.Exchanges) == 3')
        check('delta(sunCamMgr.ImagesCaptured) == 0')
        check('event cmdDisp.OpCodeError count == 1')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.SLEEP", [])
        bench.wait_event("sunCamMgr.SleepEntered", 5)
        send("sunCamMgr.SLEEP", [])
        bench.wait_event("sunCamMgr.SleepEntered", 5)
        send("sunCamMgr.CAPTURE", ['SLOT_1', 'OFF'])
        bench.wait_event("sunCamMgr.CommandRejected", 5)
        send("sunCamMgr.PING", ['MCU'])
        bench.wait_event("sunCamMgr.PingReply", 5)
        bracket(bench)
