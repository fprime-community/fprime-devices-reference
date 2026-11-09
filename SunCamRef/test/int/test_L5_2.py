"""L5-2: Camera error reply on an unsupported register

Procedure (plan.json, verbatim order):
  MARK(520)
  bracket (2 suncam samples)
  sunCamMgr.READ_REGISTER(65535)
  wait(CameraError or RegisterRead, 5 s)
  sunCamMgr.PING(MCU)
  wait(PingReply, 5 s)
  bracket (2 suncam samples)
  MARK(521)
"""
import pytest

from suncam import bracket, flush, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-019')
def test_L5_2(fth_plan, window, check, require, send, bench):
    with window(520, 521):  # W
        require("STD")
        check('event sunCamMgr.CameraError(operation=READ_REGISTER, errorType=INVALID_PARAMETER) count == 1')
        check('event sunCamMgr.RegisterRead count == 0')
        check('delta(sunCamMgr.CameraErrors) == 1')
        check('event sunCamMgr.PingReply count == 1')
        check('last(sunCamMgr.SetupState) == READY')
        check('event cmdDisp.OpCodeError count == 1')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.READ_REGISTER", [65535], wait_completion=False)  # plan expects the UUT to refuse this command (OpCodeError)
        wait_any(bench, ["sunCamMgr.CameraError", "sunCamMgr.RegisterRead"], 5)
        send("sunCamMgr.PING", ['MCU'])
        bench.wait_event("sunCamMgr.PingReply", 5)
        bracket(bench)
    flush(send)
