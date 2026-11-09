"""Shared stimulus helpers for the SunCamRef plan tests (QUAL-SUNCAM).

Every ``test_<ID>.py`` is a transcription of its plan procedure; what is checked comes from
``plan.json`` through :func:`declare_checks`, never from the test file.
"""
from functools import partial

BRACKET_CHANNEL = "sunCamMgr.Exchanges"  # a suncam-packet channel: rewritten every 10th run tick (1 Hz)


def bracket(bench, timeout=10.0):
    """plan 'bracket (2 suncam samples)': two further samples of the suncam packet (channels_note)."""
    bench.wait_samples(BRACKET_CHANNEL, 2, timeout=timeout)


def wait_any(bench, events, timeout):
    """plan 'wait(A or B, N s)': the first of the named events within the timeout."""
    last_error = None
    for name in events:
        try:
            bench.wait_event(name, timeout)
            return
        except Exception as exc:  # noqa: BLE001 - the next alternative is tried; the last failure is raised
            last_error = exc
    raise last_error


def helper(plan, name, **args):
    """A plan helper predicate bound to its plan arguments: ``check(text, helper(fth_plan, "delta_mod", channel=..., ...))``."""
    return partial(plan.registry.helpers[name], **args)


def flush(send):
    """One harmless command after a test's last window: fth v0.1.2 closes a window at the END marker event plus the
    dispatcher rows that follow it up to the next OpCodeDispatched (its pilot UUT logged OpCodeDispatched after the
    handler); this F´ logs OpCodeDispatched before the handler, so without a following command the END marker's own
    dispatch row is the one before the START marker's and `commands_sent == count(OpCodeDispatched)` is off by one
    for the last window of a run."""
    send("cmdDisp.CMD_NO_OP", [])
