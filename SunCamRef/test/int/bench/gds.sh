#!/usr/bin/env bash
# gds: run fprime-gds in the foreground and, when stopped, stop the helpers it spawned (comm, data handlers)
# by their recorded PIDs (children of our own fprime-gds PID; never by name pattern).
# usage: gds.sh <dictionary> <gds_host> <gds_port> <zmq-in> <zmq-out> <logs>
set -uo pipefail
dict="$1"; host="$2"; port="$3"; zin="$4"; zout="$5"; logs="$6"
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
}
trap 'stop; exit 0' TERM INT
wait "$gds"
stop
