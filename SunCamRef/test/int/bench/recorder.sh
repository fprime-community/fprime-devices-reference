#!/usr/bin/env bash
# recorder: see the Python below (kept inside a shell script: fth verify-plan lints every *.py under test/int).
# fprime-gds 4.4.0 logs `<wall>,(<tb>(<ctx>)-<sec>:<usec>),<name>,<id>,...`; fth v0.1.2 export expects
# `TB_PROC_TIME: <sec>.<usec>s, context=<ctx>,(<tb>(<ctx>)-<sec>:<usec>),<name>,<id>,...`. fprime-cli events logs
# natively under {logs}/.native; its event.log / channel.log rows are re-written live into {logs}/fprime-cli-<ts>/.
# usage: recorder.sh <dictionary> <zmq-in> <zmq-out> <logs>
set -uo pipefail
exec python3 - "$1" "$2" "$3" "$4" <<'PY'
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ROW = re.compile(r"^(?P<wall>\S+),\((?P<tb>\d+)\((?P<ctx>\d+)\)-(?P<sec>\d+):(?P<usec>\d+)\),(?P<rest>.*)$")


def convert(line):
    m = ROW.match(line)
    if not m:
        return None
    return (f"TB_PROC_TIME: {int(m['sec'])}.{int(m['usec']):06d}s, context={m['ctx']},"
            f"({m['tb']}({m['ctx']})-{m['sec']}:{m['usec']}),{m['rest']}")


def main(dictionary, zin, zout, logs):
    logs = Path(logs)
    native = logs / ".native"
    native.mkdir(parents=True, exist_ok=True)
    out = logs / time.strftime("fprime-cli-%Y_%m_%d-%H_%M_%S")
    out.mkdir(parents=True, exist_ok=True)
    child = subprocess.Popen(["fprime-cli", "events", "--dictionary", dictionary, "--zmq-transport", zin, zout,
                              "--logs", str(native)], stdin=subprocess.DEVNULL,
                             stdout=open(out / "fprime-cli-events.out", "ab"), stderr=subprocess.STDOUT)
    (logs / "recorder-children.pid").write_text(f"{child.pid}\n", encoding="utf-8")
    stop = []
    signal.signal(signal.SIGTERM, lambda *_: stop.append(1))
    signal.signal(signal.SIGINT, lambda *_: stop.append(1))
    offsets = {}
    sinks = {name: open(out / name, "a", encoding="utf-8") for name in ("event.log", "channel.log")}

    def pump():
        for name, sink in sinks.items():
            for src in sorted(native.glob(f"fprime-cli-*/{name}")):
                key = str(src)
                pos = offsets.get(key, 0)
                with open(src, "r", encoding="utf-8", errors="replace") as fh:
                    fh.seek(pos)
                    while True:
                        line = fh.readline()
                        if not line.endswith("\n"):
                            break
                        pos = fh.tell()
                        row = convert(line.rstrip("\n"))
                        if row is not None:
                            sink.write(row + "\n")
                offsets[key] = pos
            sink.flush()

    while not stop and child.poll() is None:
        pump()
        time.sleep(0.25)
    if child.poll() is None:
        child.terminate()
        try:
            child.wait(5)
        except subprocess.TimeoutExpired:
            child.kill()
    time.sleep(0.5)
    pump()
    for sink in sinks.values():
        sink.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
PY
