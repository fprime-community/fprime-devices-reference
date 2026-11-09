#!/usr/bin/env bash
# flash: install the image as the running SunCamRef and (re)start it by recorded PID.
# usage: flash.sh <image> <rundir> <uart> <gds_host> <gds_port>
source "$(dirname "$0")/common.sh"
image="$1"; rundir="$2"
[ -f "$image" ] || { echo "image not found: $image"; exit 1; }
[ -e "$3" ] || { echo "uart not present: $3"; exit 1; }
# The bench identity fth records as the "debugger serial": the USB serial of the FTDI RS-422 cable the camera hangs on
serial=$(udevadm info -q property -n "$3" 2>/dev/null | sed -n 's/^ID_SERIAL_SHORT=//p')
[ -n "$serial" ] || serial=$(basename "$3" | sed -E 's/.*_([A-Za-z0-9]+)-if[0-9]+-port[0-9]+$/\1/')
echo "FTDI serial = $serial ($(readlink -f "$3"))"
mkdir -p "$rundir"
stop_recorded "$rundir"
install -m 0755 "$image" "$rundir/SunCamRef"
{
    echo "$(date -u +%FT%TZ) install sha256 $(sha256sum "$image" | cut -d' ' -f1) ($image)"
    echo "$(date -u +%FT%TZ) readback sha256 $(sha256sum "$rundir/SunCamRef" | cut -d' ' -f1) ($rundir/SunCamRef)"
} | tee -a "$rundir/flash.log"
start_suncamref "$rundir" "$3" "$4" "$5"
