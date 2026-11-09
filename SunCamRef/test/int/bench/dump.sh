#!/usr/bin/env bash
# dump: read back the installed binary and copy the DpWriter directory into the record.
# usage: dump.sh <readback> <rundir>   (fth passes {readback} = record/raw/readback-<deployment>.bin; the
# products land beside it in record/raw/dp/)
set -euo pipefail
readback="$1"; rundir="$2"; logs="$(dirname "$readback")"
mkdir -p "$(dirname "$readback")" "$logs/dp"
cp "$rundir/SunCamRef" "$readback"
if [ -d "$rundir/DpCat" ]; then
    find "$rundir/DpCat" -maxdepth 1 -type f -exec cp -p {} "$logs/dp/" \;
fi
echo "readback sha256 $(sha256sum "$readback" | cut -d' ' -f1); $(find "$logs/dp" -type f | wc -l) product file(s) in $logs/dp"
