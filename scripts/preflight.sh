#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"

echo "== preflight: env =="
$PY -V
$PY -m pip -V

echo "== preflight: install (editable + dev) =="
$PY -m pip install -U pip
$PY -m pip install -e ".[dev]"

echo "== preflight: lint =="
$PY -m ruff check .

echo "== preflight: tests =="
$PY -m pytest -q

echo "== preflight: build (sanity) =="
$PY -m build -q

echo "OK: preflight passed"