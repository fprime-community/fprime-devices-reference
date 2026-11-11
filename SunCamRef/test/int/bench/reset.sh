#!/usr/bin/env bash
# reset: restart SunCamRef by its recorded PID (process restart = the plan's 'bench reset'), settle >= 3 s.
# usage: reset.sh <rundir> <uart> <gds_host> <gds_port>
source "$(dirname "$0")/common.sh"
rundir="$1"
stop_recorded "$rundir"
start_suncamref "$rundir" "$2" "$3" "$4"
