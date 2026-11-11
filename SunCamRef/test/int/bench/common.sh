# Shared by flash.sh / reset.sh: start SunCamRef in $rundir, record its PID; stop only by that PID.
set -euo pipefail

stop_recorded() {  # $1 = rundir
    local pidfile="$1/SunCamRef.pid"
    if [ -f "$pidfile" ]; then
        local pid; pid=$(cat "$pidfile")
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "stopping SunCamRef pid $pid (recorded)"
            kill -TERM "$pid"
            for _ in $(seq 1 50); do kill -0 "$pid" 2>/dev/null || break; sleep 0.1; done
            kill -0 "$pid" 2>/dev/null && kill -KILL "$pid" || true
        fi
        rm -f "$pidfile"
    fi
}

start_suncamref() {  # $1 = rundir, $2 = uart, $3 = gds host, $4 = gds port
    local rundir="$1"
    mkdir -p "$rundir/DpCat"
    ( cd "$rundir" || exit 1
      nohup ./SunCamRef -a "$3" -p "$4" -u "$2" < /dev/null >> SunCamRef.log 2>&1 &
      echo $! > SunCamRef.pid )   # $! is the nohup that execs SunCamRef, not a wrapper shell
    sleep 3
    local pid; pid=$(cat "$rundir/SunCamRef.pid")
    kill -0 "$pid" 2>/dev/null || { echo "SunCamRef exited at start; tail of $rundir/SunCamRef.log:"; tail -20 "$rundir/SunCamRef.log"; exit 1; }
    echo "SunCamRef started pid $pid (uart $2, gds $3:$4)"
}
