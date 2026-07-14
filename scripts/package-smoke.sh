#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

mkdir "$tmp/source"
(cd "$root" && git ls-files -z | tar --null -cf - --files-from=-) | tar -xf - -C "$tmp/source"
python3 -m build --sdist --wheel --outdir "$tmp/dist" "$tmp/source"

smoke_artifact() {
  local artifact="$1"
  local name="$2"
  local venv="$tmp/venv-$name"
  local work="$tmp/work-$name"

  python3 -m venv "$venv"
  "$venv/bin/python" -m pip install "$artifact"
  mkdir "$work"
  cd "$work"
  PYTHONWARNINGS=error "$venv/bin/egmo" --help >/dev/null
  PYTHONWARNINGS=error "$venv/bin/egmo" create-task packet --mission-id "package-smoke-$name"
  PYTHONWARNINGS=error "$venv/bin/egmo" validate packet/*.yaml --no-sanitization
  PYTHONWARNINGS=error "$venv/bin/egmo" judge \
    packet/mission.yaml packet/execution.yaml packet/evidence.yaml \
    packet/review.yaml packet/final-report.yaml
}

smoke_artifact "$tmp"/dist/*.whl wheel
smoke_artifact "$tmp"/dist/*.tar.gz sdist

echo "Built, clean-installed, and smoke-tested the wheel and sdist with bundled schema data and deprecation warnings treated as errors."
