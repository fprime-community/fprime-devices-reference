#!/usr/bin/env bash
# send: one command through fprime-cli. The plugin prefixes the plan's short name with the deployment
# (SunCamRef.cmdDisp.CMD_NO_OP_STRING); the dictionary qualifies subtopology instances by their
# subtopology (CdhCore.cmdDisp...), so the name is resolved to the unique dictionary command.
# usage: send.sh <dictionary> <zmq-in> <zmq-out> <logs> <command> [args...]
set -euo pipefail
dict="$1"; zin="$2"; zout="$3"; logs="$4"; cmd="$5"; shift 5
full=$(python3 - "$dict" "$cmd" <<'PY'
import json, sys
dict_path, name = sys.argv[1], sys.argv[2]
names = [c["name"] for c in json.load(open(dict_path, encoding="utf-8"))["commands"]]
if name in names:
    print(name); sys.exit(0)
tail = name.split(".", 1)[1] if "." in name else name
hits = [n for n in names if n == tail or n.endswith("." + tail)]
if len(hits) != 1:
    sys.exit(f"send: {name!r} resolves to {hits} in {dict_path}")
print(hits[0])
PY
)
fprime-cli command-send --dictionary "$dict" --zmq-transport "$zin" "$zout" --logs "$logs" "$full" --arguments "$@"
rc=$?
# fprime-gds 4.4.0 logs the arguments as the CLI strings (`['20']`); fth reads them as values (`[20]`, as the
# fprime-cli the harness was piloted with logged them). Numeric strings become ints, names stay strings.
python3 - "$logs" <<'PY'
import ast, pathlib, sys

def _isint(v):
    try:
        int(v, 0)
        return True
    except ValueError:
        return False

for log in pathlib.Path(sys.argv[1]).glob("*/command.log"):
    out, changed = [], False
    for line in log.read_text(encoding="utf-8").splitlines():
        head, sep, raw = line.rpartition(",[")
        if sep and raw.endswith("]") and "'" in raw:
            try:
                vals = ast.literal_eval("[" + raw)
            except (ValueError, SyntaxError):
                vals = None
            if isinstance(vals, list):
                fixed = [int(v, 0) if isinstance(v, str) and _isint(v) else v for v in vals]
                line, changed = head + "," + repr(fixed), True
        out.append(line)
    if changed:
        log.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
exit $rc
