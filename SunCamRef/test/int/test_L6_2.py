"""L6-2: Negative control: DOWNLOAD_ABORT with no download

Procedure (plan.json, verbatim order):
  MARK(620)
  bracket (2 suncam samples)
  sunCamMgr.SETUP_CAMERA
  wait(SetupComplete, 15 s)
  bracket (2 suncam samples)
  MARK(622)
  bracket (2 suncam samples)
  sunCamMgr.PING(MCU)
  wait(PingReply, 5 s)
  sunCamMgr.DOWNLOAD_ABORT
  wait(CommandRejected, 5 s)
  sunCamMgr.PING(MCU)
  wait(PingReply, 5 s)
  bracket (2 suncam samples)
  MARK(621)
"""
import pytest

from suncam import bracket, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-026')
def test_L6_2(fth_plan, window, check, require, send, bench):
    with window(620, 622):  # W1
        require("STD")
        check('event sunCamMgr.SetupComplete(mode=SD, exposure=672) count == 1')
        check('last(sunCamMgr.SetupState) == READY')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.SETUP_CAMERA", [])
        bench.wait_event("sunCamMgr.SetupComplete", 15)
        bracket(bench)
    with window(622, 621):  # W
        require("STD")
        check('event sunCamMgr.CommandRejected(operation=DOWNLOAD_ABORT, cause=NO_DOWNLOAD) count == 1')
        check('event sunCamMgr.PingReply(pingType=MCU) count == 2')
        check('delta(sunCamMgr.Exchanges) == 2')
        check('CameraValidCmds advances by exactly 1 between the two ping replies: the refused DOWNLOAD_ABORT sent no frame (mod 256)',
              helper(fth_plan, "delta_mod", channel='sunCamMgr.CameraValidCmds', delta=1, mod=256))
        check('event sunCamMgr.DownloadAborted count == 0')
        check('event cmdDisp.OpCodeError count == 1')
        check('ABS')
        bracket(bench)
        send("sunCamMgr.PING", ['MCU'])
        bench.wait_event("sunCamMgr.PingReply", 5)
        send("sunCamMgr.DOWNLOAD_ABORT", [], wait_completion=False)  # plan expects the UUT to refuse this command (OpCodeError)
        bench.wait_event("sunCamMgr.CommandRejected", 5)
        send("sunCamMgr.PING", ['MCU'])
        bench.wait_event("sunCamMgr.PingReply", 5)
        bracket(bench)
