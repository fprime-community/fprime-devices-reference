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
    """plan 'wait(A or B, N s)': the first of the named events within ONE timeout (all names polled together)."""
    import time
    base = {name: bench.count_events(name) for name in events}
    deadline = time.monotonic() + float(timeout)
    while True:
        for name in events:
            if bench.count_events(name) > base[name]:
                return name
        if time.monotonic() >= deadline:
            raise TimeoutError(f"bench: timed out after {timeout} s waiting for any of {events}")
        time.sleep(0.2)


def helper(plan, name, **args):
    """A plan helper predicate bound to its plan arguments: ``check(text, helper(fth_plan, "delta_mod", channel=..., ...))``."""
    return partial(plan.registry.helpers[name], **args)
