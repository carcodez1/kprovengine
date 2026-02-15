#!/usr/bin/env bash
set -euo pipefail

# Forbid heredocs / inline python blocks in Makefile recipes.
# Rationale: prevents shell interpreting "import ..." as a command (ImageMagick on macOS).

fail=0

if rg -n '<<' Makefile >/dev/null; then
  echo "FAIL: Makefile contains heredoc (<<). Use scripts/ for multiline logic." >&2
  rg -n '<<' Makefile >&2 || true
  fail=1
fi

# Optional: forbid recipe lines that begin with "import" (paranoia gate)
if rg -n '^\timport\b' Makefile >/dev/null; then
  echo "FAIL: Makefile recipe line begins with 'import' token." >&2
  rg -n '^\timport\b' Makefile >&2 || true
  fail=1
fi

exit "$fail"
