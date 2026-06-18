#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path
import re
import sys

root = Path.cwd()
diagrams = []

for diagram in sorted((root / 'diagrams').glob('*.mmd')):
    diagrams.append((diagram.relative_to(root), diagram.read_text()))

for md in sorted(root.rglob('*.md')):
    if '.git' in md.parts or 'node_modules' in md.parts:
        continue
    text = md.read_text()
    for i, match in enumerate(re.finditer(r"```mermaid\n([\s\S]*?)\n```", text), start=1):
        diagrams.append((Path(f"{md.relative_to(root)}#inline-{i}"), match.group(1)))

errors = []
allowed_starts = ('flowchart ', 'graph ', 'sequenceDiagram', 'classDiagram', 'stateDiagram', 'erDiagram', 'journey', 'gantt', 'pie', 'mindmap')
for label, source in diagrams:
    stripped = source.strip()
    first = stripped.splitlines()[0] if stripped else ''
    if not stripped:
        errors.append(f"{label}: empty Mermaid diagram")
        continue
    if not first.startswith(allowed_starts):
        errors.append(f"{label}: unsupported or missing Mermaid diagram header: {first!r}")
    for opener, closer in [('(', ')'), ('[', ']'), ('{', '}')]:
        if stripped.count(opener) != stripped.count(closer):
            errors.append(f"{label}: unbalanced {opener}{closer}")
    if 'TODO' in stripped or 'FIXME' in stripped:
        errors.append(f"{label}: unfinished marker present")

if errors:
    print('Mermaid validation failed:')
    for error in errors:
        print(f'- {error}')
    sys.exit(1)

print(f"Validated {len(diagrams)} Mermaid diagram(s).")
PY
