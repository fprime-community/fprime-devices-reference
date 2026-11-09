"""L2-2: Ping MCU and MCU+sensor

Procedure (plan.json, verbatim order):
  MARK(220)
  bracket (2 suncam samples)
  sunCamMgr.PING(MCU)
  wait(PingReply, 5 s)
  sunCamMgr.PING(MCU_AND_SENSOR)
  wait(PingReply, 5 s)
  bracket (2 suncam samples)
  MARK(221)
"""
import pytest

from suncam import bracket, flush, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-006', 'REQ-SunCamMgr-022', 'REQ-SunCamMgr-025')
def test_L2_2(fth_plan, window, check, require, send, bench):
    with window(220, 221):  # W
        require("STD")
        check('event sunCamMgr.PingReply(pingType=MCU) count == 1')
        check('event sunCamMgr.PingReply(pingType=MCU_AND_SENSOR) count == 1')
        check('event sunCamMgr.CommandRejected count == 0')
        check('delta(sunCamMgr.Exchanges) == 2')
        check('delta(sunCamMgr.CameraInvalidCmds) == 0')
        check('CameraValidCmds advances by exactly 1 between the two ping replies (mod 256)',
              helper(fth_plan, "delta_mod", channel='sunCamMgr.CameraValidCmds', delta=1, mod=256))
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.PING", ['MCU'])
        bench.wait_event("sunCamMgr.PingReply", 5)
        send("sunCamMgr.PING", ['MCU_AND_SENSOR'])
        bench.wait_event("sunCamMgr.PingReply", 5)
        bracket(bench)
    flush(send)
