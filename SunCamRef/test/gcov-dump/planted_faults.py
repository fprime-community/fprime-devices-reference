"""Planted fault of the gcov dump plan (fth requires one `uut-state` fault per plan for a manifest; the dump plan
is development evidence only and is never drawn)."""
from fth.registry import planted_fault


def _is(command_name, short):
    return command_name == short or command_name.endswith("." + short)


@planted_fault("partial_dump_first", applies_to=["GC-1"], cls="uut-state", kind="insert",
               mechanism="DUMP_COVERAGE(0, 1) inserted before DUMP_COVERAGE(0, 0): the first chunk of object 0 is "
                         "streamed twice (byte-identical, so fth coverage-system still reassembles), the plan's "
                         "exactly-once check on chunk (object 0, offset 0) fails",
               fails={"GC-1": ["event covDump.CoverageChunk(object=0, offset=0) count == 1"]})
def partial_dump_first(test_id, command_name, args):
    if test_id == "GC-1" and _is(command_name, "DUMP_COVERAGE") and list(args) == [0, 0]:
        return [("covDump.DUMP_COVERAGE", [0, 1]), (command_name, args)]
    return None


@planted_fault("valid_range_instead", applies_to=["GC-2"], cls="stimulus", kind="rewrite",
               mechanism="DUMP_COVERAGE(65535, 1) rewritten to (0, 1): the command is accepted and streams one chunk "
                         "where the negative control expects a rejection",
               fails={"GC-2": ["event covDump.CoverageDumpError count == 1", "event cmdDisp.OpCodeError count == 1",
                               "event covDump.CoverageChunk count == 0"]})
def valid_range_instead(test_id, command_name, args):
    if test_id == "GC-2" and _is(command_name, "DUMP_COVERAGE") and list(args) == [65535, 1]:
        return [0, 1]
    return None
