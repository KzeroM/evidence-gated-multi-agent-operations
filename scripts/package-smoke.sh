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
  "$venv/bin/python" - "$name" <<'PY'
import sys
import warnings
from importlib.metadata import version

import yaml

warnings.filterwarnings(
    "error", message=r".*RefResolver.*", category=DeprecationWarning
)

from egmo import __version__
from egmo.protocol import TEMPLATE_DIR, _schema_registry, validate_document

artifact_kind = sys.argv[1]
expected_version = "2.1.0"
assert version("egmo-reference") == __version__ == expected_version

_schema_registry.cache_clear()
first = _schema_registry()
review = yaml.safe_load((TEMPLATE_DIR / "critic-review.yaml").read_text(encoding="utf-8"))
assert validate_document(review, f"installed-{artifact_kind}-critic-template") == []
second = _schema_registry()
assert first is second
assert _schema_registry.cache_info().misses == 1
print(
    f"{artifact_kind}: version={__version__}; complete external $ref resolution passed; "
    "RefResolver deprecations absent; registry cache reused"
)
PY
  "$venv/bin/egmo" --help >/dev/null
  "$venv/bin/egmo" create-task packet --mission-id "package-smoke-$name"
  "$venv/bin/egmo" validate packet/*.yaml --no-sanitization
  "$venv/bin/egmo" judge \
    packet/mission.yaml packet/execution.yaml packet/evidence.yaml \
    packet/review.yaml packet/final-report.yaml
}

smoke_artifact "$tmp"/dist/*.whl wheel
smoke_artifact "$tmp"/dist/*.tar.gz sdist

echo "Built, clean-installed, and smoke-tested the wheel and sdist; installed version, Registry cache, external refs, and absence of RefResolver deprecations were proved."
