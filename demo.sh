#!/usr/bin/env bash
set -euo pipefail

echo "== KProvEngine V1 demo =="

# 1) Clean workspace
rm -rf demo_runs demo_input.txt
mkdir -p demo_runs

# 2) Create an input artifact
echo "Hello provenance world" > demo_input.txt

# 3) Run the pipeline
python -m kprovengine.cli demo_input.txt --out demo_runs

# 4) Locate run directory
RUN_DIR="$(find demo_runs -maxdepth 1 -type d | grep -v demo_runs | head -n 1)"
echo "Run directory: $RUN_DIR"

# 5) Show generated evidence artifacts
echo
echo "== Evidence artifacts =="
ls -1 "$RUN_DIR"

echo
echo "== run_summary.json =="
cat "$RUN_DIR/run_summary.json" | sed 's/^/  /'

echo
echo "== provenance.json =="
cat "$RUN_DIR/provenance.json" | sed 's/^/  /'

echo
echo "== toolchain.json =="
cat "$RUN_DIR/toolchain.json" | sed 's/^/  /'

echo
echo "== human_review.json =="
cat "$RUN_DIR/human_review.json" | sed 's/^/  /'

echo
echo "Demo complete."
