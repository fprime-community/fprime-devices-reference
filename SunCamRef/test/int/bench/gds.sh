#!/usr/bin/env bash
# gds: start the installed SunCamRef (recorded PID, cwd $rundir) and run fprime-gds in the foreground; when
# stopped, stop fprime-gds' helpers (comm, data handlers) by their recorded PIDs (children of our own fprime-gds
# PID, never by name pattern) and SunCamRef by its recorded PID.
# usage: gds.sh <dictionary> <gds_host> <gds_port> <zmq-in> <zmq-out> <logs> <rundir> <uart>
source "$(dirname "$0")/common.sh"
set +e
dict="$1"; host="$2"; port="$3"; zin="$4"; zout="$5"; logs="$6"; rundir="$7"; uart="$8"
start_suncamref "$rundir" "$uart" "$host" "$port" | tee -a "$logs/gds-suncamref.log" || exit 1
fprime-gds -n --dictionary "$dict" --ip-address "$host" --ip-port "$port" --gui none --framing-selection fprime --zmq-transport "$zin" "$zout" --logs "$logs" &
gds=$!
sleep 2
pgrep -P "$gds" > "$logs/gds-children.pid" 2>/dev/null || true
stop() {
    kill "$gds" 2>/dev/null
    for p in $(cat "$logs/gds-children.pid" 2>/dev/null); do kill "$p" 2>/dev/null; done
    sleep 2
    for p in $(cat "$logs/gds-children.pid" 2>/dev/null) "$gds"; do kill -0 "$p" 2>/dev/null && kill -KILL "$p" 2>/dev/null; done
    rm -f "${zin#ipc://}" "${zout#ipc://}"
    stop_recorded "$rundir" >> "$logs/gds-suncamref.log" 2>&1
}
trap 'stop; exit 0' TERM INT
wait "$gds"
stop
