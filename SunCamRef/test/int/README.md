# SunCamRef system test (plan QUAL-SUNCAM, KissCam.SunCamMgr)

Harness: [fprime-testing-harness](https://github.com/LeStarch/fprime-testing-harness) v0.1.10 (`fth`).

Pin (campaign fvp-2026-11-07-1): tag `v0.1.10` = tag object `77171e4ed0bea3904bafa39d24ecbd2d55bc6f65` on commit
`3a58356d1dd2439fe46875dfe75365c50d60db4e`, fetched from the autobot fork
`https://github.com/lestarch-autobot/fprime-testing-harness` until it lands upstream:
`git -C harness fetch --tags https://github.com/lestarch-autobot/fprime-testing-harness && git -C harness checkout --detach v0.1.10 && pip install -e "harness[test]"`.
v0.1.3 = window-slice fix (dispatchers that log `OpCodeDispatched` before the handler event); v0.1.4 = human-step, run-for-record-only tests
(`human_step` / `run_in`, verdict DEFERRED); v0.1.5 = positional `human step` procedure line → `bench.human_step()` and
`fth rfr --defer-human-steps RULING`. The deployment logs the same string at start-up (`HARNESS_DESCRIBE`, read by `fth manifest`).
v0.1.6 = `count <=|>=|<|>` n, helper metrics judged by their helper, bench `boot_event` epochs and `collect` recipe (data products into `record/raw/dp/` before every live judge), `FTH_MANIFEST` exported to the stimulus, SDD-table check insensitive to the renderer's phase marker (dry-3 / Mode B round-1 findings).
v0.1.7 = refusal fix: `boot_event` epoch rows crashed the live judge (`re.Match` indexed as a dict; SunCamRef dry-4), regression test on verbatim event.log lines.
v0.1.8 = dry-6 refusal fixes: channel epochs follow the bench `boot_event` rows, START-marker dispatch order decided by same-flush rows only, `bench.wait_any_event()` (plan `wait(A or B, N s)`) with the last-send baseline.
v0.1.9 = `wait_any_event` returns in a dry run / replay (audit parity, dry-7).
v0.1.10 = Mode B round-2 S-7/S-8: live judge settles until the channel flush passes t(END) (`timeouts.settle_s`), replay matches the plan's short command name (subtopology markers).

| File | Role |
| --- | --- |
| `plan.json`, `plan.md`, `faults-menu.json` | The approved plan — byte copies; any change is a plan change (anchor + reviewer). |
| `planted_faults.py` | The 5 `@planted_fault` declarations and the 4 `@helper` predicates (`version_matches_manifest`, `delta_mod`, `decode_image_in_window`, `event_count_at_most`; `memory_slot_exposure` retired with Memory Status, not implemented on the hardware); the Image data-product decoder lives here. |
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

Bench — campaign-root layout (`croot/`): `uut/` = this repository (submodules checked out, `cd uut/SunCamRef && fprime-util generate && fprime-util build`; after every later pull `rm -f build-fprime-*/versions/version.*` before `fprime-util build` — fprime regenerates `Svc.Version`'s describe strings only when those files are missing, and `fth manifest` rejects an image whose PROJECT version is not the current `uut` describe), `harness/` = the fth checkout, the bench recipe's `gds` line starts SunCamRef (recorded PID) together with fprime-gds and `flash` only installs (fth wants the camera UART free between flash and gds), the fth venv active, `fprime-gds`/`fprime-cli` on `PATH`.

```sh
cd croot
fth run dry-1 --manifest manifest.json --plan uut/SunCamRef/test/int/plan.json \
    --bench uut/SunCamRef/test/int/bench.json --tests uut/SunCamRef/test/int --dry-run          # full plan, dry (neutral id)
fth run dry-2 ... --dry-run --unsealed --plant L2-5=preview_instead_of_full                     # one planted fault alone
python -m pytest -p fth.pytest_plugin --fth-plan=... --fth-bench=... --fth-run-dir=... uut/SunCamRef/test/int/test_L2_5.py   # one test
fth audit --tests dry-1                                                                          # replay == live, no DIVERGENCE
```

The DpWriter directory is `<rundir>/DpCat` (`bench.json` `vars.rundir`); `dump` copies it into `record/raw/dp/`, where `decode_image_in_window` reads the Image products and writes `dev-evidence/images/<test>.png` (relative to the campaign root).

## Coverage (development evidence, harness skill §3a)

The RfR runs the pure image; the coverage *reports* are RfR inputs (`fth deliver --ut-coverage --system-coverage
--dev-evidence`). They come from `fth dev-campaign`, which needs three things this directory provides:

- **UT coverage**: a default-config UT project beside the campaign root (`utproj/settings.ini`: `framework_path`
  and `library_locations` pointing into the pinned `uut/lib/*` trees, framework/autocoder UTs off);
  `fth dev-campaign --ut-project utproj` runs `fprime-util check --coverage` there (gcovr).
- **On-target coverage**: the deployment built with `-DSUNCAMREF_COVERAGE=ON` (root `CMakeLists.txt`, separate
  build cache: `fprime-util generate --build-cache uut/build-cov -DSUNCAMREF_COVERAGE=ON && fprime-util build
  --build-cache uut/build-cov`) instruments `SunCamMgr.cpp` only (`-fprofile-filter-files`). The main plan runs
  on that image, then the one-test dump plan `gcov-dump/` on the same image: `SunCamRef.CovDump`'s
  `DUMP_COVERAGE(0, 0)` flushes the hosted libgcov counters (`__gcov_dump`; every earlier process life — the L3-1
  reset, the flash before the dump run — wrote its `.gcda` at exit, libgcov merges them) and streams the files as
  `CoverageChunk` / `CoverageObject` / `CoverageDumpDone` events, 4 chunks per 10 Hz tick, the command response
  after the last chunk. `fth coverage-system --record <dump run>/record --gcno-root uut/build-cov --project-root
  uut --filter lib/fprime-devices/fprime-devices/KissCam/Components/SunCamMgr/ --gcov gcov` places the bytes
  beside the `.gcno` (object matched by the CRC-32 of the `.gcda` path) and runs gcovr. Delete stale `*.gcda`
  under the cache before the plan run. The instrumented image is never the RfR image; in the pure image the
  component is present but `DUMP_COVERAGE` reports "no gcda root".
- **Pure run**: the plan on the RfR image (an ordinary unsealed `fth run`).

`fth dev-campaign --out dev-evidence --plan ... --tests ... --bench ... --ut-project utproj --coverage-run <plan run>
--coverage-manifest <its manifest> --dump-run <dump run> --dump-manifest <its manifest> --dump-plan gcov-dump/plan.json
--dump-tests gcov-dump --gcno-root uut/build-cov --project-root uut --filter <SunCamMgr dir> --gcov gcov --pure-run
<pure run> --pure-manifest <its manifest> --sdd <pinned sdd.md> --dictionary <dict>` exits 0 when every pure verdict is
PASS, runner == replay, and coverage meets `plan.json` `coverage` (`ut.lines_min` 95, `system.lines_min` 75; uncovered
lines must be in `not_covered_ack`).

## Windows and markers

Markers are `cmdDisp.CMD_NO_OP_STRING` / `cmdDisp.NoOpStringReceived` (`Received a NO-OP string=<id>`); the plugin sends the start/end markers of each `with window(start, end)` block; multi-window tests share the edge marker as the plan declares (L2-1, L3-1, L6-1, L6-2).
