#!/usr/bin/env bash
# collect: copy the data products DpWriter has written so far (./DpCat in the SunCamRef working directory) into the
# record's raw/dp/ — run by fth before every live window judge and before the final export (bench `collect`).
set -euo pipefail
rundir="$1"; logs="$2"
mkdir -p "$logs/dp"
if [ -d "$rundir/DpCat" ]; then
    find "$rundir/DpCat" -maxdepth 1 -type f -name '*.fdp' -exec cp -p {} "$logs/dp/" \;
fi
echo "$(find "$logs/dp" -type f | wc -l) product file(s) in $logs/dp"
