"""L0-2: Marker round-trip

Procedure (plan.json, verbatim order):
  MARK(20)
  bracket (2 suncam samples)
  MARK(4294901759)
  bracket (2 suncam samples)
  MARK(21)
"""
import pytest

from suncam import bracket, flush, helper, wait_any


@pytest.mark.req('REQ-SunCamMgr-030')
def test_L0_2(fth_plan, window, check, require, send, bench):
    with window(20, 21):  # W
        require("STD")
        check('event cmdDisp.NoOpStringReceived(id=4294901759) count == 1')
        check('event cmdDisp.OpCodeError count == 0')
        check('ABS')
        bracket(bench)
        send("cmdDisp.CMD_NO_OP_STRING", [4294901759])  # in-window marker
        bracket(bench)
    flush(send)
