#!/usr/bin/env bash
# run_v2_sequence.sh — everything after the gates, under SPEC Amendment 1.
#
# Every step aborts the whole sequence on failure. The first version used
# `set -uo pipefail` WITHOUT -e, so a failed submission printed an error and the script
# carried straight on; that is how ten lock-drift refusals scrolled past while the sweep
# continued regardless. It also read a gates.json a previous suite had left behind, and
# passed on it.
#
# Two rules follow from those mistakes:
#   1. `set -e` plus an ERR trap, so nothing downstream of a failure runs.
#   2. Commands are never piped into grep/head. Under `pipefail`, a grep that matches
#      nothing (exit 1) or a head that closes the pipe (SIGPIPE) would abort a step that
#      actually succeeded. Output goes to a file; the file is grepped separately.
set -euo pipefail
trap 'st=$?; echo; echo "STEP FAILED (exit $st) — sequence aborted, nothing downstream ran."; exit $st' ERR

cd "$(dirname "$0")"
E="${RX_EXPERIMENT:-e:3}"
PY="conda run -n pycpt python"
LOGDIR=outputs/steplogs
mkdir -p "$LOGDIR"

step() { echo; echo "=== $* ==="; }

# Run a command, abort on failure, and surface only the interesting lines.
run() {
  local tag="$1"; shift
  local log="$LOGDIR/${tag}.log"
  if ! "$@" > "$log" 2>&1; then
    echo "  FAILED: $*"
    tail -20 "$log"
    return 1
  fi
  grep -E "Captured metrics|rpss|VERDICT|guard|passed|PASS|FAIL|wrote|Error" "$log" \
    | tail -4 || true
}

# ── the gate guard must not be able to read a stale file ─────────────────────
step "gate suite (Amendment 1)"
rm -f outputs/gates.json
run gates rx run exec -e "$E" --include-untracked -- $PY probes/gates.py
GUARD=$(python3 - <<'EOF'
import json, sys
try:
    d = json.load(open("outputs/gates.json"))
except Exception as e:
    print(f"missing ({type(e).__name__})"); sys.exit()
print(f"{d.get('status')}|{d.get('failed')}|{d.get('spec_version')}|{d.get('passed')}/{d.get('gates')}")
EOF
)
echo "gate guard: $GUARD"
case "$GUARD" in
  ok\|0\|amendment-1\|*) : ;;
  *) echo "GATE FAILURE OR STALE GATE FILE — stopping before any scientific number is read."
     exit 1 ;;
esac

step "real atlas, all arms, both protocols"
run real rx run exec -e "$E" --include-untracked -- $PY run_atlas.py --real

step "atlas v2 submissions"
for proto in walkforward kfold; do
  bench=atlas-wf-v2; [ "$proto" = kfold ] && bench=atlas-kf-v2
  for arm in climatology pooled zones-shared zones-specific; do
    run "sub_${proto}_${arm}" rx run benchmark "$bench" -e "$E" --include-untracked \
      -p "arm=$arm" -- --arm "$arm" --protocol "$proto" \
      --per-zone "outputs/perzone_v2_${proto}_${arm}.json"
  done
done

step "secondary v2 submissions"
for w in mam ond; do
  for arm in pooled zones; do
    run "sec_fixedmean_${w}_${arm}" rx run benchmark "fixedmean-${w}-v2" -e "$E" \
      --include-untracked -p "arm=$arm" -- --arm "$arm"
  done
  for arm in climatology pooled zones-specific; do
    run "sec_grid_${w}_${arm}" rx run benchmark "grid-${w}-v2" -e "$E" \
      --include-untracked -p "arm=$arm" -- --arm "$arm"
  done
done
run collect_secondary rx run exec -e "$E" --include-untracked -- $PY probes/collect_secondary.py

# The null pins its own code manifest before running and enforces the 200 x 3 = 600
# completeness guard afterwards. A partial sweep exits non-zero and the ERR trap stops
# everything downstream.
step "primary null: 200 complete-season target permutations"
run null rx run exec -e "$E" --include-untracked -- $PY run_atlas.py --null

step "sensitivity: superseded field permutation, adjudicates nothing"
run sensitivity rx run exec -e "$E" --include-untracked -- $PY run_atlas.py --sensitivity 20 --workers 4

step "decisions, stability, figures"
run decide rx run exec -e "$E" --include-untracked -- $PY probes/decide.py
run stability rx run exec -e "$E" --include-untracked -- $PY probes/stability.py

echo
echo "SEQUENCE COMPLETE"
echo "REPORT.md is hand-maintained — not overwritten. See README.md."
