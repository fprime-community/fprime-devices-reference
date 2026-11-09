"""Known-answer tests for the plan helpers in test/int/planted_faults.py (pass + fail per helper).

Hand-built records (events.jsonl / channels.jsonl / commands.jsonl + raw/dp/ product files) stand in for the
bench; run with plain pytest: ``pytest SunCamRef/test/kat`` (not under --fth-plan, these are not plan tests).
"""
import json
import struct
import zlib
from pathlib import Path

import pytest
from fth.engine import HelperContext
from fth.plan import load_plan
from fth.replay import load_record

INT = Path(__file__).resolve().parents[1] / "int"
MARKER = "cmdDisp.NoOpStringReceived"


@pytest.fixture(scope="module")
def plan():
    return load_plan(INT / "plan.json")


def _rows(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def make_ctx(plan, tmp_path, events=(), channels=(), start=(10, 100.0), end=(11, 200.0), test_id="L0-1"):
    """A record dir with marker events at `start`/`end` (id, fsw) plus the given (fsw, name, text|value) rows."""
    rec = tmp_path / "run" / "record"
    rec.mkdir(parents=True)
    ev = [{"name": MARKER, "fsw": start[1], "epoch": 1, "id": 1, "severity": "ACTIVITY_HI",
           "args": {"text": f"Received a NO-OP string={start[0]}"}}]
    ev += [{"name": n, "fsw": t, "epoch": 1, "id": 2, "severity": "ACTIVITY_LO", "args": {"text": x}} for t, n, x in events]
    ev += [{"name": MARKER, "fsw": end[1], "epoch": 1, "id": 1, "severity": "ACTIVITY_HI",
            "args": {"text": f"Received a NO-OP string={end[0]}"}}]
    _rows(rec / "events.jsonl", sorted(ev, key=lambda r: r["fsw"]))
    _rows(rec / "channels.jsonl", [{"name": n, "fsw": t, "epoch": 1, "id": 3, "value": v} for t, n, v in sorted(channels, key=lambda r: r[0])])
    _rows(rec / "commands.jsonl", [])
    record = load_record(rec, plan.raw["event_patterns"], marker_event=MARKER, marker_command=plan.raw["markers"]["command"])
    w = record.window(start[0], end[0])
    return HelperContext(record, plan, plan.test(test_id), w, {"W": w})


def H(plan, name):
    return plan.registry.helpers[name]


# ---- event_count_at_most ------------------------------------------------------------------------------

def test_event_count_at_most_pass_fail(plan, tmp_path):
    ctx = make_ctx(plan, tmp_path, events=[(120.0, "sunCamMgr.ReplyTimeout", "x"), (130.0, "sunCamMgr.ReplyTimeout", "x")])
    assert H(plan, "event_count_at_most")(ctx, event="sunCamMgr.ReplyTimeout", max=2)[0] is True
    assert H(plan, "event_count_at_most")(ctx, event="sunCamMgr.ReplyTimeout", max=1)[0] is False


# ---- delta_mod ------------------------------------------------------------------------------------------

def test_delta_mod_pass(plan, tmp_path):
    ctx = make_ctx(plan, tmp_path, channels=[(110.0, "sunCamMgr.CameraValidCmds", 250), (190.0, "sunCamMgr.CameraValidCmds", 4)])
    holds, seen, refs, unverified = H(plan, "delta_mod")(ctx, channel="sunCamMgr.CameraValidCmds", delta=10, mod=256)
    assert (holds, unverified) == (True, False) and "first 250 last 4" in seen and refs


def test_delta_mod_fail(plan, tmp_path):
    ctx = make_ctx(plan, tmp_path, channels=[(110.0, "sunCamMgr.CameraValidCmds", 250), (190.0, "sunCamMgr.CameraValidCmds", 5)])
    assert H(plan, "delta_mod")(ctx, channel="sunCamMgr.CameraValidCmds", delta=10, mod=256)[0] is False


def test_delta_mod_unverified_with_one_sample(plan, tmp_path):
    ctx = make_ctx(plan, tmp_path, channels=[(110.0, "sunCamMgr.CameraValidCmds", 250)])
    holds, _seen, _refs, unverified = H(plan, "delta_mod")(ctx, channel="sunCamMgr.CameraValidCmds", delta=0, mod=256)
    assert (holds, unverified) == (None, True)


# ---- memory_slot_exposure ------------------------------------------------------------------------------

SLOTS = [{"slot": 1, "exposure": 672}, {"slot": 2, "exposure": 672}, {"slot": 3, "exposure": 300}, {"slot": 4, "exposure": 0}]


def test_memory_slot_exposure_pass_last_sample_wins(plan, tmp_path):
    stale = [{"slot": 1, "exposure": 1}, {"slot": 2, "exposure": 1}, {"slot": 3, "exposure": 1}, {"slot": 4, "exposure": 1}]
    ctx = make_ctx(plan, tmp_path, channels=[(110.0, "sunCamMgr.MemorySlots", stale), (150.0, "sunCamMgr.MemorySlots", SLOTS)])
    holds, seen, refs, unverified = H(plan, "memory_slot_exposure")(ctx, slot4=0, slot3=300)
    assert (holds, unverified) == (True, False) and refs == ["channels.jsonl:2"], seen


def test_memory_slot_exposure_accepts_text_sample(plan, tmp_path):
    ctx = make_ctx(plan, tmp_path, channels=[(150.0, "sunCamMgr.MemorySlots", json.dumps(SLOTS))])
    assert H(plan, "memory_slot_exposure")(ctx, slot1=672)[0] is True


def test_memory_slot_exposure_fail(plan, tmp_path):
    ctx = make_ctx(plan, tmp_path, channels=[(150.0, "sunCamMgr.MemorySlots", SLOTS)])
    assert H(plan, "memory_slot_exposure")(ctx, slot4=672)[0] is False


def test_memory_slot_exposure_unverified_without_sample(plan, tmp_path):
    ctx = make_ctx(plan, tmp_path)
    assert H(plan, "memory_slot_exposure")(ctx, slot4=0)[3] is True


# ---- version_matches_manifest --------------------------------------------------------------------------

REPOS = [{"name": "fprime-devices-reference", "describe": "a99a783-dirty"}, {"name": "fprime", "describe": "v4.0.0-100-gf28d2da"},
         {"name": "fprime-devices", "describe": "6a2cf2d"}]
VERSION_EVENTS = [(101.0, "version.ProjectVersion", "Project Version: [a99a783-dirty]"),
                  (102.0, "version.FrameworkVersion", "Framework Version: [v4.0.0-100-gf28d2da]"),
                  (103.0, "version.LibraryVersions", "Library Versions: [fprime-devices@6a2cf2d]")]


def _manifest(tmp_path, monkeypatch, repos=REPOS):
    m = tmp_path / "manifest.json"
    m.write_text(json.dumps({"repos": repos}), encoding="utf-8")
    monkeypatch.setenv("FTH_MANIFEST", str(m))


def test_version_matches_manifest_pass(plan, tmp_path, monkeypatch):
    _manifest(tmp_path, monkeypatch)
    ctx = make_ctx(plan, tmp_path, events=VERSION_EVENTS)
    holds, seen, refs, unverified = H(plan, "version_matches_manifest")(ctx)
    assert (holds, unverified) == (True, False) and len(refs) == 3, seen


def test_version_matches_manifest_fail_on_framework_drift(plan, tmp_path, monkeypatch):
    _manifest(tmp_path, monkeypatch)
    ev = list(VERSION_EVENTS)
    ev[1] = (102.0, "version.FrameworkVersion", "Framework Version: [v4.0.0-99-gdeadbee]")
    assert H(plan, "version_matches_manifest")(make_ctx(plan, tmp_path, events=ev))[0] is False


def test_version_matches_manifest_fail_on_missing_library_event(plan, tmp_path, monkeypatch):
    _manifest(tmp_path, monkeypatch)
    assert H(plan, "version_matches_manifest")(make_ctx(plan, tmp_path, events=VERSION_EVENTS[:2]))[0] is False


def test_version_matches_manifest_reads_runner_argv(plan, tmp_path, monkeypatch):
    monkeypatch.delenv("FTH_MANIFEST", raising=False)
    m = tmp_path / "manifest.json"
    m.write_text(json.dumps({"repos": REPOS}), encoding="utf-8")
    ctx = make_ctx(plan, tmp_path, events=VERSION_EVENTS)
    runner = tmp_path / "run" / "runner"
    runner.mkdir()
    (runner / "pytest-argv.json").write_text(json.dumps(["pytest", "--fth-manifest", str(m)]), encoding="utf-8")
    assert H(plan, "version_matches_manifest")(ctx)[0] is True


def test_version_matches_manifest_unverified_without_manifest(plan, tmp_path, monkeypatch):
    monkeypatch.delenv("FTH_MANIFEST", raising=False)
    holds, _s, _r, unverified = H(plan, "version_matches_manifest")(make_ctx(plan, tmp_path, events=VERSION_EVENTS))
    assert (holds, unverified) == (None, True)


# ---- decode_image_in_window ---------------------------------------------------------------------------

HDR = struct.Struct(">HIIHBIIB32sBQ")


def product(sec, slot, image_mode, resolution, width, height, lines, pixels_for=lambda s, l: None, line_order=None):
    """A DpContainer Image product: header, CRC slot, ImageHeader record (id 0), ImageLine records (id 1), data hash."""
    n = 640 if resolution == 0 else 80
    body = struct.pack(">I", 0) + struct.pack(">BBBHHBH", slot, image_mode, resolution, width, height, image_mode, lines)
    per_slot = lines // 4 if image_mode == 2 else lines
    order = line_order or [((i // per_slot) + 1 if image_mode == 2 else slot, i % per_slot) for i in range(lines)]
    for s, l in order:
        px = pixels_for(s, l) or bytes([(s * 40 + l) & 0xFF]) * n
        body += struct.pack(">I", 1) + struct.pack(">Q", 3 + len(px)) + bytes([s, l >> 8, l & 0xFF]) + px
    hdr = HDR.pack(0, 0, 1, 2, 0, sec, 0, 0, b"\0" * 32, 0, len(body))
    return hdr + b"\0\0\0\0" + body + b"\0\0\0\0"


def _dp(ctx, name, data):
    d = Path(ctx.record.path) / "raw" / "dp"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_bytes(data)


def _png_pixels(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, w, h = 8, b"", 0, 0
    while pos < len(data):
        (n,) = struct.unpack(">I", data[pos:pos + 4]); tag = data[pos + 4:pos + 8]; body = data[pos + 8:pos + 8 + n]
        if tag == b"IHDR":
            w, h = struct.unpack(">II", body[:8])
        elif tag == b"IDAT":
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    return w, h, [raw[r * (w + 1) + 1:(r + 1) * (w + 1)] for r in range(h)]


ARGS_L7 = dict(slot=4, image_mode="SD", resolution="PREVIEW", width=80, height=60, lines=60, expect="none", out="kat-L7-1.png")


def test_decode_sd_preview_pass_writes_png(plan, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ctx = make_ctx(plan, tmp_path, test_id="L7-1")
    _dp(ctx, "SunCamRef_sunCamMgr_Image_0001.fdp", product(150, 4, 1, 1, 80, 60, 60))
    _dp(ctx, "earlier.fdp", product(50, 4, 1, 1, 80, 60, 60))  # before the window: ignored
    holds, seen, refs, unverified = H(plan, "decode_image_in_window")(ctx, **ARGS_L7)
    assert (holds, unverified) == (True, False), seen
    assert "raw/dp/SunCamRef_sunCamMgr_Image_0001.fdp" in refs
    w, h, rows = _png_pixels(tmp_path / "dev-evidence" / "images" / "kat-L7-1.png")
    assert (w, h) == (80, 60) and rows[5][0] == (4 * 40 + 5) & 0xFF


def test_decode_hd_preview_quadrants(plan, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ctx = make_ctx(plan, tmp_path, test_id="L2-10")
    _dp(ctx, "hd.fdp", product(150, 1, 2, 1, 160, 120, 240, pixels_for=lambda s, l: bytes([s * 50]) * 80))
    args = dict(slot=1, image_mode="HD", resolution="PREVIEW", width=160, height=120, lines=240, expect="none", out="kat-hd.png")
    holds, seen, _refs, _u = H(plan, "decode_image_in_window")(ctx, **args)
    assert holds is True, seen
    w, h, rows = _png_pixels(tmp_path / "dev-evidence" / "images" / "kat-hd.png")
    assert (w, h) == (160, 120)
    assert (rows[0][0], rows[0][159], rows[119][0], rows[119][159]) == (50, 100, 150, 200)  # TL/TR/BL/BR = slots 1-4


@pytest.mark.parametrize("bad, why", [
    (dict(lines=59), "one line short"),
    (dict(image_mode=2), "header imageMode HD instead of SD"),
    (dict(slot=1), "header slot 1 instead of 4"),
])
def test_decode_fails_on_header_or_line_count(plan, tmp_path, monkeypatch, bad, why):
    monkeypatch.chdir(tmp_path)
    ctx = make_ctx(plan, tmp_path, test_id="L7-1")
    kw = dict(sec=150, slot=4, image_mode=1, resolution=1, width=80, height=60, lines=60)
    kw.update(bad)
    _dp(ctx, "p.fdp", product(**kw))
    holds, seen, _r, unverified = H(plan, "decode_image_in_window")(ctx, **ARGS_L7)
    assert (holds, unverified) == (False, False), (why, seen)


def test_decode_fails_on_line_order(plan, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ctx = make_ctx(plan, tmp_path, test_id="L7-1")
    order = [(4, l) for l in range(60)]
    order[10], order[11] = order[11], order[10]
    _dp(ctx, "p.fdp", product(150, 4, 1, 1, 80, 60, 60, line_order=order))
    holds, seen, _r, _u = H(plan, "decode_image_in_window")(ctx, **ARGS_L7)
    assert holds is False and "out of slot/line order" in seen


def test_decode_fails_when_two_products_in_window(plan, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ctx = make_ctx(plan, tmp_path, test_id="L7-1")
    _dp(ctx, "a.fdp", product(150, 4, 1, 1, 80, 60, 60))
    _dp(ctx, "b.fdp", product(160, 4, 1, 1, 80, 60, 60))
    holds, seen, _r, _u = H(plan, "decode_image_in_window")(ctx, **ARGS_L7)
    assert holds is False and "2 Image product(s)" in seen


def test_decode_fails_when_no_product_in_window(plan, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ctx = make_ctx(plan, tmp_path, test_id="L7-1")
    _dp(ctx, "late.fdp", product(250, 4, 1, 1, 80, 60, 60))
    holds, seen, _r, unverified = H(plan, "decode_image_in_window")(ctx, **ARGS_L7)
    assert (holds, unverified) == (False, False) and "0 Image product(s)" in seen


def test_decode_unverified_without_dump(plan, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ctx = make_ctx(plan, tmp_path, test_id="L7-1")
    assert H(plan, "decode_image_in_window")(ctx, **ARGS_L7)[3] is True


# ---- planted faults: each changes the command stream exactly as its `kind` declares, only in its test -----

def F(plan, name):
    return plan.registry.planted_faults[name].func


@pytest.mark.parametrize("fault, test_id, cmd, args, out", [
    ("expect_wrong_exposure_resetup", "L2-1", "sunCamMgr.EXPOSURE_PRM_SET", [300], [299]),
    ("expect_wrong_exposure_push", "L2-6", "sunCamMgr.EXPOSURE_PRM_SET", [300], [301]),
    ("read_wrong_register", "L2-8", "sunCamMgr.READ_REGISTER", [12306], [12304]),
    ("preview_instead_of_full", "L2-5", "sunCamMgr.DOWNLOAD", ["SLOT_1", "FULL"], ["SLOT_1", "PREVIEW"]),
])
def test_rewrite_faults(plan, fault, test_id, cmd, args, out):
    assert F(plan, fault)(test_id, cmd, args) == out
    assert F(plan, fault)(test_id, cmd, [672] if len(args) == 1 else ["SLOT_1", "PREVIEW"]) is None  # other args untouched
    assert F(plan, fault)("L2-2", cmd, args) is None  # other tests untouched
    assert F(plan, fault)(test_id, "sunCamMgr.SETUP_CAMERA", []) is None


def test_insert_fault_sleep_before_final(plan):
    out = F(plan, "sleep_before_final")("L7-1", "sunCamMgr.CAPTURE", ["SLOT_4", "ON"])
    assert out == [("sunCamMgr.SLEEP", []), ("sunCamMgr.CAPTURE", ["SLOT_4", "ON"])]
    assert F(plan, "sleep_before_final")("L2-2", "sunCamMgr.CAPTURE", ["SLOT_1", "OFF"]) is None
    assert F(plan, "sleep_before_final")("L7-1", "sunCamMgr.DOWNLOAD", ["SLOT_4", "PREVIEW"]) is None
