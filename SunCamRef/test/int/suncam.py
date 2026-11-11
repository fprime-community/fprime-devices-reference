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
    """plan 'wait(A or B, N s)': the first of the named events within ONE timeout, counted from the last send
    (fth v0.1.8 ``bench.wait_any_event``; a baseline taken here, after send() returned, misses a fast reply —
    dry-6 L2-8). Returns the event name seen."""
    return bench.wait_any_event(list(events), float(timeout))


def helper(plan, name, **args):
    """A plan helper predicate bound to its plan arguments: ``check(text, helper(fth_plan, "delta_mod", channel=..., ...))``."""
    return partial(plan.registry.helpers[name], **args)
