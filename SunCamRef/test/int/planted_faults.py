"""Planted faults and helpers for QUAL-SUNCAM (KissCam.SunCamMgr on SunCamRef).

Planted-fault hooks receive ``(test_id, command_name, args)`` and return rewritten ``args``
(kind="rewrite"), a list of ``(command_name, args)`` tuples (kind="insert"), or ``None`` to leave
the command untouched. One declaration per plant site; ``fails`` lists are the verbatim check
strings of the target test that the fault breaks; ``ripples_to`` names the later tests whose
listed checks also fail (none here: every fault's site restores the camera state or is last).
Helper bodies are completed with the harness at stage 2; their names and contracts are declared here.
"""
import json
import os
import struct
import zlib
from pathlib import Path

from fth.registry import helper, planted_fault


def _is(command_name, short):
    return command_name == short or command_name.endswith("." + short)


# ---- planted faults --------------------------------------------------------------------------

@planted_fault("expect_wrong_exposure_resetup", applies_to=["L2-1"], cls="stimulus", kind="rewrite",
               mechanism="L2-1 W2: EXPOSURE_PRM_SET(300) rewritten to 299 before the re-entrant SETUP_CAMERA; the set-up applies 299 where the checks expect 300 (stateless: the only EXPOSURE_PRM_SET(300) of the test; the 672 restore is untouched)",
               fails={"L2-1": [
                   "event sunCamMgr.SetupComplete(mode=SD, exposure=300) count == 1",
                   "event sunCamMgr.SettingApplied(setting=EXPOSURE, value=300) count == 2",
                   "event sunCamMgr.ExposureReadback(pushed=300, readback=300) count == 2"]})
def expect_wrong_exposure_resetup(test_id, command_name, args):
    if test_id == "L2-1" and _is(command_name, "EXPOSURE_PRM_SET") and list(args) == [300]:
        return [299]
    return None


@planted_fault("expect_wrong_exposure_push", applies_to=["L2-6"], cls="stimulus", kind="rewrite",
               mechanism="EXPOSURE_PRM_SET(300) rewritten to 301; the checks expect 300 (672 restore untouched)",
               fails={"L2-6": [
                   "event sunCamMgr.SettingApplied(setting=EXPOSURE, value=300) count == 1",
                   "event sunCamMgr.ExposureReadback(pushed=300, readback=300) count == 1"]})
def expect_wrong_exposure_push(test_id, command_name, args):
    if test_id == "L2-6" and _is(command_name, "EXPOSURE_PRM_SET") and list(args) == [300]:
        return [301]
    return None


@planted_fault("read_wrong_register", applies_to=["L2-8"], cls="stimulus", kind="rewrite",
               mechanism="READ_REGISTER(12306) rewritten to READ_REGISTER(12304, fine integration): camera and UUT nominal, the checker still expects register 0x3012 = 300. Classed stimulus (the drive of the operation under test changes); the skill's harness-expectation class fits a rewritten verification step, which this protocol has none of",
               fails={"L2-8": ["event sunCamMgr.RegisterRead(address=3012, value=300) count == 1"]})
def read_wrong_register(test_id, command_name, args):
    if test_id == "L2-8" and _is(command_name, "READ_REGISTER") and list(args) == [12306]:
        return [12304]
    return None


@planted_fault("preview_instead_of_full", applies_to=["L2-5"], cls="stimulus", kind="rewrite",
               mechanism="DOWNLOAD(SLOT_1, FULL) rewritten to PREVIEW: 60 lines / 4800 bytes arrive where 480 / 307200 are expected",
               fails={"L2-5": [
                   "event sunCamMgr.DownloadStarted(slot=SLOT_1, imageMode=SD, resolution=FULL, lines=480) count == 1",
                   "event sunCamMgr.DownloadComplete(slot=SLOT_1, imageMode=SD, resolution=FULL, lines=480, bytes=307200) count == 1",
                   "delta(sunCamMgr.LinesDownloaded) == 480",
                   "one Image product in window: ImageHeader(slot=1, imageMode=SD, resolution=FULL, width=640, height=480), 480 slot-tagged ImageLine records in order; PNG → dev-evidence/images/L2-5-full.png",
                   "t(event sunCamMgr.DownloadComplete(slot=SLOT_1, imageMode=SD, resolution=FULL, lines=480, bytes=307200)) - t(sunCamMgr.DOWNLOAD sent) <= 90 s"]})
def preview_instead_of_full(test_id, command_name, args):
    if test_id == "L2-5" and _is(command_name, "DOWNLOAD") and len(args) == 2 and str(args[1]) == "FULL":
        return [args[0], "PREVIEW"]
    return None


@planted_fault("sleep_before_final", applies_to=["L7-1"], cls="uut-state", kind="insert",
               mechanism="SLEEP inserted before CAPTURE(SLOT_4, ON): the component is NOT_SETUP, CAPTURE/DOWNLOAD/MEMORY_STATUS are rejected NOT_READY, no product is written in the window",
               fails={"L7-1": [
                   "event sunCamMgr.CaptureComplete(slot=SLOT_4, testPattern=ON, mode=SD) count == 1",
                   "event sunCamMgr.DownloadComplete(slot=SLOT_4, imageMode=SD, resolution=PREVIEW, lines=60, bytes=4800) count == 1",
                   "event sunCamMgr.MemoryStatusReply count == 2",
                   "event sunCamMgr.CommandRejected count == 0",
                   "delta(sunCamMgr.ImagesCaptured) == 1",
                   "delta(sunCamMgr.ProductsSent) == 1",
                   "last(dpMgr.NumDataProducts) == 2",
                   "last(sunCamMgr.SetupState) == READY",
                   "exactly one Image product in window: ImageHeader(slot=4, imageMode=SD, resolution=PREVIEW, width=80, height=60), 60 lines in order; PNG → dev-evidence/images/L7-1-final.png",
                   "event cmdDisp.OpCodeError count == 0"]})
def sleep_before_final(test_id, command_name, args):
    if test_id == "L7-1" and _is(command_name, "CAPTURE"):
        return [("sunCamMgr.SLEEP", []), (command_name, args)]
    return None


# ---- helpers (contracts declared at test design; bodies completed with the harness at stage 2) ----
#
# Every helper returns ``(holds, seen, refs, unverified)``: ``unverified=True`` means the evidence is
# missing for an infrastructure reason (no manifest, no samples, no raw/dp/ directory), never a UUT verdict.

PROJECT_REPO = "fprime-devices-reference"
FRAMEWORK_REPO = "fprime"


def _manifest_path(ctx):
    """Where the run's manifest is: ``$FTH_MANIFEST``, else the ``--fth-manifest`` the runner recorded in
    ``<run>/runner/pytest-argv.json`` (``fth run`` does not copy the manifest into the sealed record)."""
    env = os.environ.get("FTH_MANIFEST")
    if env and Path(env).is_file():
        return Path(env)
    argv = Path(ctx.record.path).parent / "runner" / "pytest-argv.json"
    if argv.is_file():
        args = json.loads(argv.read_text(encoding="utf-8"))
        for i, a in enumerate(args):
            if a == "--fth-manifest" and i + 1 < len(args) and Path(args[i + 1]).is_file():
                return Path(args[i + 1])
            if a.startswith("--fth-manifest=") and Path(a.split("=", 1)[1]).is_file():
                return Path(a.split("=", 1)[1])
    return None


def _event_versions(ctx, short):
    rows = ctx.window.events(short)
    return [str(r.args.get("version", r.text)) for r in rows], [f"events.jsonl:{r.idx}" for r in rows]


@helper("version_matches_manifest")
def version_matches_manifest(ctx, **args):
    """PASS iff the window's version.ProjectVersion / FrameworkVersion / LibraryVersions payloads equal
    the manifest repos[].describe strings (project = fprime-devices-reference, framework = fprime,
    library = fprime-devices@<describe>) and the LibraryVersions count equals the number of manifest
    repos that are neither project nor framework. Formats: Svc/Version/Version.fpp:56, :64, :72."""
    mp = _manifest_path(ctx)
    if mp is None:
        return None, "no manifest reachable ($FTH_MANIFEST or <run>/runner/pytest-argv.json --fth-manifest)", [], True
    repos = {r["name"]: r["describe"] for r in json.loads(mp.read_text(encoding="utf-8")).get("repos", [])}
    if PROJECT_REPO not in repos or FRAMEWORK_REPO not in repos:
        return None, f"manifest {mp} lacks repos {PROJECT_REPO!r}/{FRAMEWORK_REPO!r}: {sorted(repos)}", [], True
    libs = sorted(f"{n}@{d}" for n, d in repos.items() if n not in (PROJECT_REPO, FRAMEWORK_REPO))
    proj, r1 = _event_versions(ctx, "version.ProjectVersion")
    fw, r2 = _event_versions(ctx, "version.FrameworkVersion")
    lib, r3 = _event_versions(ctx, "version.LibraryVersions")
    refs = r1 + r2 + r3
    seen = f"project={proj} framework={fw} libraries={sorted(lib)}; manifest project={repos[PROJECT_REPO]!r} framework={repos[FRAMEWORK_REPO]!r} libraries={libs}"
    holds = proj == [repos[PROJECT_REPO]] and fw == [repos[FRAMEWORK_REPO]] and sorted(lib) == libs
    return holds, seen, refs, False


@helper("delta_mod")
def delta_mod(ctx, channel, delta, mod):
    """PASS iff (last(channel) - first(channel)) mod `mod` == delta over the window's samples (≥ 2 samples)."""
    rows = ctx.window.channel(channel)
    if len(rows) < 2:
        return None, f"{channel}: {len(rows)} sample(s) in window (need ≥ 2)", [], True
    first, last = int(rows[0].value), int(rows[-1].value)
    got = (last - first) % int(mod)
    refs = [f"channels.jsonl:{rows[0].idx}-{rows[-1].idx}"]
    return got == int(delta), f"{channel}: first {first} last {last} -> delta mod {mod} = {got} (expected {delta})", refs, False


def _slot_exposures(value):
    """``MemorySlots`` sample -> {slot number: exposure}; accepts the exporter's parsed list or its text."""
    if isinstance(value, str):
        value = json.loads(value)
    out = {}
    for i, slot in enumerate(value, start=1):
        if isinstance(slot, dict):
            out[i] = int(slot["exposure"])
        else:
            out[i] = int(slot[1])
    return out


@helper("memory_slot_exposure")
def memory_slot_exposure(ctx, **slots):
    """PASS iff last(sunCamMgr.MemorySlots) carries the named slot exposures (slot4=0 → test pattern, §7.4.3)."""
    rows = ctx.window.channel("sunCamMgr.MemorySlots")
    if not rows:
        return None, "sunCamMgr.MemorySlots: no sample in window", [], True
    last = rows[-1]
    try:
        got = _slot_exposures(last.raw if last.raw is not None else last.value)
    except (KeyError, TypeError, ValueError, IndexError, json.JSONDecodeError) as exc:
        return False, f"sunCamMgr.MemorySlots: undecodable sample {last.raw!r} ({exc})", [f"channels.jsonl:{last.idx}"], False
    want = {int(k[4:]) if k.startswith("slot") else int(k): int(v) for k, v in slots.items()}
    holds = all(got.get(k) == v for k, v in want.items())
    seen = "last MemorySlots exposures " + ", ".join(f"slot{k}={got.get(k)}" for k in sorted(want)) + f" (expected {want})"
    return holds, seen, [f"channels.jsonl:{last.idx}"], False


# ---- Image data product decoding (SDD §Data product; Fw/Dp/DpContainer.hpp) ----------------------------

# DpContainer header for this build (default FpConfig on 64-bit Linux):
# desc U16 | id U32 | priority U32 | time (base U16, context U8, sec U32, usec U32) | procTypes U8 |
# userData[32] | dpState U8 | dataSize U64 ; then the header hash (CRC32, 4 B) ; records ; data hash.
_HDR = struct.Struct(">HIIHBIIB32sBQ")
_HDR_HASH = 4
_DATA_OFFSET = _HDR.size + _HDR_HASH
_RECORD_ID = struct.Struct(">I")
_ARRAY_SIZE = struct.Struct(">Q")
_IMAGE_HEADER = struct.Struct(">BBBHHBH")  # slot, imageMode, resolution, width, height, cameraMode, linesExpected
_MODE = {1: "SD", 2: "HD", 0: "SLEEP"}
_RESOLUTION = {0: "FULL", 1: "PREVIEW"}
_LINE_PIXELS = {"FULL": 640, "PREVIEW": 80}


def parse_product(data):
    """Parse one DpContainer file -> dict(id, time_s, header=ImageHeader dict or None, lines=[(slot, line, bytes)])."""
    if len(data) < _DATA_OFFSET:
        raise ValueError(f"short container: {len(data)} B")
    desc, dp_id, prio, tbase, tctx, sec, usec, proc, _user, state, data_size = _HDR.unpack_from(data, 0)
    end = _DATA_OFFSET + data_size
    if end > len(data):
        raise ValueError(f"dataSize {data_size} exceeds file ({len(data)} B)")
    pos, header, lines = _DATA_OFFSET, None, []
    while pos < end:
        (rid,) = _RECORD_ID.unpack_from(data, pos)
        pos += _RECORD_ID.size
        if rid == 0:
            header = dict(zip(("slot", "imageMode", "resolution", "width", "height", "cameraMode", "linesExpected"),
                              _IMAGE_HEADER.unpack_from(data, pos)))
            pos += _IMAGE_HEADER.size
        elif rid == 1:
            (n,) = _ARRAY_SIZE.unpack_from(data, pos)
            pos += _ARRAY_SIZE.size
            payload = data[pos:pos + n]
            if len(payload) != n or n < 3:
                raise ValueError(f"ImageLine record at {pos}: size {n}, available {len(payload)}")
            lines.append((payload[0], (payload[1] << 8) | payload[2], bytes(payload[3:])))
            pos += n
        else:
            raise ValueError(f"unknown record id {rid} at offset {pos}")
    return {"id": dp_id, "time_s": sec + usec / 1e6, "header": header, "lines": lines}


def write_png(path, width, height, rows):
    """8-bit greyscale PNG (Bayer samples shown as grey); ``rows`` = list of ``bytes`` of length ``width``."""
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(png)


def assemble(header, lines):
    """Place slot-tagged lines in the image: SD = one slot; HD = slots 1-4 as TL/TR/BL/BR quadrants (SDD Fig. 3)."""
    width, height = header["width"], header["height"]
    n = _LINE_PIXELS[_RESOLUTION[header["resolution"]]]
    sub_h = height if header["imageMode"] != 2 else height // 2
    image = [bytearray(width) for _ in range(height)]
    for slot, line, px in lines:
        if header["imageMode"] == 2:
            x0, y0 = n * ((slot - 1) % 2), sub_h * ((slot - 1) // 2)
        else:
            x0, y0 = 0, 0
        if 0 <= line < sub_h and len(px) == n and x0 + n <= width:
            image[y0 + line][x0:x0 + n] = px
    return image


def check_product(parsed, slot, image_mode, resolution, width, height, lines):
    """Compare a parsed product with the expected ImageHeader and line sequence -> (holds, problems)."""
    h = parsed["header"]
    problems = []
    if h is None:
        return False, ["no ImageHeader record"]
    want = {"slot": int(slot), "imageMode": {"SD": 1, "HD": 2}[image_mode], "resolution": {"FULL": 0, "PREVIEW": 1}[resolution],
            "width": int(width), "height": int(height), "linesExpected": int(lines)}
    for k, v in want.items():
        if h[k] != v:
            problems.append(f"header.{k}={h[k]} (expected {v})")
    n = _LINE_PIXELS[resolution]
    got = parsed["lines"]
    if len(got) != int(lines):
        problems.append(f"{len(got)} ImageLine records (expected {lines})")
    per_slot = int(lines) // 4 if image_mode == "HD" else int(lines)
    expected = [((i // per_slot) + 1 if image_mode == "HD" else int(slot), i % per_slot) for i in range(int(lines))]
    bad_order = [i for i, ((s, l, px), (es, el)) in enumerate(zip(got, expected)) if (s, l) != (es, el)]
    if bad_order:
        problems.append(f"{len(bad_order)} record(s) out of slot/line order, first at index {bad_order[0]}: {got[bad_order[0]][:2]}")
    bad_len = [i for i, (_s, _l, px) in enumerate(got) if len(px) != n]
    if bad_len:
        problems.append(f"{len(bad_len)} record(s) with pixel count != {n}, first at index {bad_len[0]}")
    return not problems, problems


def test_pattern_kat(image, width, height):
    """§7 refresh (decision 10): the camera's test pattern as decoded from the bench unit. Filled in at the bench;
    until then any decoded preview is reported with its row statistics and the KAT is UNVERIFIED."""
    return None, "pattern KAT reference not pinned yet (§7 refresh item)"


@helper("decode_image_in_window")
def decode_image_in_window(ctx, slot, image_mode, resolution, width, height, lines, expect, out):
    """Reads record/raw/dp/ (copied from the DpWriter directory by the bench dump recipe), selects the
    Image-container product whose header time lies in [t(START), t(END)] of the window (FSW time);
    FAILs when none or more than one exists; decodes ImageHeader + ImageLine records, checks
    header fields (incl. imageMode), `lines` slot-tagged records in slot then line order (HD: slots 1-4 assembled as quadrants); expect="pattern_kat" (added at the §7 refresh,
    decision log 10) compares the decoded preview with the pinned test-pattern reference;
    writes dev-evidence/images/<out> (PNG, Bayer as grey)."""
    w = ctx.window
    dp_dir = Path(ctx.record.path) / "raw" / "dp"
    if not dp_dir.is_dir():
        return None, f"{dp_dir}: no DpWriter dump in the record (bench dump recipe)", [], True
    if not w.ok:
        return None, "window markers incomplete", [], True
    t0, t1 = w.start_marker.fsw, w.end_marker.fsw
    products = []
    for f in sorted(dp_dir.rglob("*")):
        if not f.is_file():
            continue
        try:
            parsed = parse_product(f.read_bytes())
        except (ValueError, struct.error) as exc:
            products.append((f, None, str(exc)))
            continue
        if t0 <= parsed["time_s"] <= t1:
            products.append((f, parsed, None))
    in_window = [(f, p) for f, p, err in products if p is not None]
    broken = [f"{f.name}: {err}" for f, p, err in products if err]
    refs = [f"events.jsonl:{w.start_marker.idx}", f"events.jsonl:{w.end_marker.idx}"]
    if len(in_window) != 1:
        return False, f"{len(in_window)} Image product(s) with header time in [{t0:.3f}, {t1:.3f}] s under raw/dp/ ({[f.name for f, _ in in_window]}; undecodable: {broken})", refs, False
    f, parsed = in_window[0]
    holds, problems = check_product(parsed, slot, image_mode, resolution, width, height, lines)
    refs.append(f"raw/dp/{f.name}")
    seen = f"{f.name}: header {parsed['header']}, {len(parsed['lines'])} ImageLine records"
    if parsed["header"] is not None and parsed["lines"]:
        hdr = parsed["header"]
        img_w, img_h = hdr["width"], hdr["height"]
        try:
            rows = assemble(hdr, parsed["lines"])
            out_path = Path("dev-evidence") / "images" / str(out)
            write_png(out_path, img_w, img_h, rows)
            seen += f"; PNG -> {out_path}"
            if expect == "pattern_kat":
                kat, kat_seen = test_pattern_kat(rows, img_w, img_h)
                seen += f"; pattern KAT: {kat_seen}"
                if kat is False:
                    problems.append("test-pattern KAT mismatch")
        except (KeyError, ValueError) as exc:
            problems.append(f"assembly failed: {exc}")
    if problems:
        seen += "; problems: " + "; ".join(problems)
    return holds and not problems, seen, refs, False


@helper("event_count_at_most")
def event_count_at_most(ctx, event, max):
    n = len(ctx.window.events(event))
    return n <= max, f"{event} count {n} (max {max})"
