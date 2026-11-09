#!/usr/bin/env bash
# flash: install the image as the running SunCamRef and (re)start it by recorded PID.
# usage: flash.sh <image> <rundir> <uart> <gds_host> <gds_port>
source "$(dirname "$0")/common.sh"
image="$1"; rundir="$2"
[ -f "$image" ] || { echo "image not found: $image"; exit 1; }
mkdir -p "$rundir"
stop_recorded "$rundir"
install -m 0755 "$image" "$rundir/SunCamRef"
{
    echo "$(date -u +%FT%TZ) install sha256 $(sha256sum "$image" | cut -d' ' -f1) ($image)"
    echo "$(date -u +%FT%TZ) readback sha256 $(sha256sum "$rundir/SunCamRef" | cut -d' ' -f1) ($rundir/SunCamRef)"
} | tee -a "$rundir/flash.log"
start_suncamref "$rundir" "$3" "$4" "$5"
