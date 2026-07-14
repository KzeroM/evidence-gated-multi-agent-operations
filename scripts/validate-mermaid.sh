#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Ubuntu's Snap wrapper cannot expose its temporary profile to Puppeteer. Use
# the actual packaged browser binary when present; other environments use the
# browser resolved by Puppeteer (including CI's downloaded compatible build).
snap_chromium="/snap/chromium/current/usr/lib/chromium-browser/chrome"
if [[ -z "${PUPPETEER_EXECUTABLE_PATH:-}" && -x "$snap_chromium" ]]; then
  export PUPPETEER_EXECUTABLE_PATH="$snap_chromium"
fi

python3 - "$root" "$tmp" <<'PY'
from pathlib import Path
import json
import re
import sys

root, target = map(Path, sys.argv[1:])
(target / "puppeteer.json").write_text(json.dumps({
    "args": ["--no-sandbox", "--disable-setuid-sandbox"],
    "userDataDir": str(target / "chrome-profile"),
}), encoding="utf-8")
count = 0
for source in sorted((root / "diagrams").glob("*.mmd")):
    count += 1
    (target / f"diagram-{count}.mmd").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
for markdown in sorted(root.rglob("*.md")):
    if any(part in {".git", "node_modules", ".venv"} for part in markdown.parts):
        continue
    text = markdown.read_text(encoding="utf-8")
    for match in re.finditer(r"```mermaid\s*\n(.*?)\n```", text, re.DOTALL):
        count += 1
        (target / f"diagram-{count}.mmd").write_text(match.group(1), encoding="utf-8")
if count == 0:
    raise SystemExit("No Mermaid diagrams found")
print(count)
PY

count=0
for input in "$tmp"/diagram-*.mmd; do
  count=$((count + 1))
  npx --no-install mmdc --quiet --puppeteerConfigFile "$tmp/puppeteer.json" --input "$input" --output "$tmp/render-$count.svg"
  test -s "$tmp/render-$count.svg"
done

if npx --no-install mmdc --quiet --puppeteerConfigFile "$tmp/puppeteer.json" --input "$root/tests/fixtures/malformed.mmd" --output "$tmp/malformed.svg" >/dev/null 2>&1; then
  echo "Malformed Mermaid regression fixture unexpectedly rendered" >&2
  exit 1
fi

echo "Rendered $count Mermaid diagram(s); malformed regression fixture was rejected."
