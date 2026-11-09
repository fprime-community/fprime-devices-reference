# SunCamRef system test (plan QUAL-SUNCAM, KissCam.SunCamMgr)

Harness: [fprime-testing-harness](https://github.com/LeStarch/fprime-testing-harness) v0.1.2 (`fth`).

| File | Role |
| --- | --- |
| `plan.json`, `plan.md`, `faults-menu.json` | The approved plan — byte copies; any change is a plan change (anchor + reviewer). |
| `planted_faults.py` | The 5 `@planted_fault` declarations and the 5 `@helper` predicates (`version_matches_manifest`, `delta_mod`, `memory_slot_exposure`, `decode_image_in_window`, `event_count_at_most`); the Image data-product decoder lives here. |
| `test_<ID>.py` (19) | One stimulus per plan test, procedure transcribed verbatim; `require("STD")` for infrastructure, `check(...)` for every plan check (names are the plan's bytes), `check("ABS")` for the absence group. Metrics are judged by the plugin from `plan.json`. |
| `suncam.py`, `conftest.py` | `bracket()` (two further suncam-packet samples), `wait_any()`, `helper()` (bind a plan helper to its plan args). |
| `bench.json`, `bench/*.sh` | Bench recipe for the Raspberry Pi 5 (`flash`, `dump`, `reset`, `gds`, `recorder`, `send`); relative paths from the campaign root. |
| `../kat/` | Known-answer tests of every helper (pass + fail + unverified) on hand-built records — no bench needed. |

## Run

Host (no bench):

```sh
fth verify-plan SunCamRef/test/int/plan.json --tests SunCamRef/test/int   # plan + stimulus + fails/req consistency
python -m pytest SunCamRef/test/kat                                       # helper known-answer tests
```

Bench — campaign-root layout (`croot/`): `uut/` = this repository (submodules checked out, `cd uut/SunCamRef && fprime-util generate && fprime-util build`), `harness/` = the fth checkout, the fth venv active, `fprime-gds`/`fprime-cli` on `PATH`.

```sh
cd croot
fth run dry-1 --manifest manifest.json --plan uut/SunCamRef/test/int/plan.json \
    --bench uut/SunCamRef/test/int/bench.json --tests uut/SunCamRef/test/int --dry-run          # full plan, dry (neutral id)
fth run dry-2 ... --dry-run --unsealed --plant L2-5=preview_instead_of_full                     # one planted fault alone
python -m pytest -p fth.pytest_plugin --fth-plan=... --fth-bench=... --fth-run-dir=... uut/SunCamRef/test/int/test_L2_5.py   # one test
fth audit --tests dry-1                                                                          # replay == live, no DIVERGENCE
```

The DpWriter directory is `<rundir>/DpCat` (`bench.json` `vars.rundir`); `dump` copies it into `record/raw/dp/`, where `decode_image_in_window` reads the Image products and writes `dev-evidence/images/<test>.png` (relative to the campaign root).

## Windows and markers

Markers are `cmdDisp.CMD_NO_OP_STRING` / `cmdDisp.NoOpStringReceived` (`Received a NO-OP string=<id>`); the plugin sends the start/end markers of each `with window(start, end)` block; multi-window tests share the edge marker as the plan declares (L2-1, L3-1, L6-1, L6-2).
