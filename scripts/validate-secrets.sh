#!/usr/bin/env bash
set -euo pipefail

command -v detect-secrets >/dev/null 2>&1 || {
  echo "detect-secrets 1.5.0 is required; install requirements-dev.txt" >&2
  exit 2
}

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
detect-secrets scan --all-files \
  --exclude-files '(^|/)(node_modules|\.git|\.venv)/' \
  --exclude-files 'package(?:-lock)?\.json$' >"$tmp"

python3 - "$tmp" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
results = data.get("results", {})
if results:
    for path, findings in sorted(results.items()):
        for finding in findings:
            print(f"{path}:{finding.get('line_number', '?')}: {finding.get('type', 'secret')}", file=sys.stderr)
    raise SystemExit(1)
print("detect-secrets scan passed.")
PY
