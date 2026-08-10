#!/usr/bin/env bash
# regenerate.sh — one command that rebuilds every artifact in this project.
#
# Every step runs through rx, so each one is captured with its git sha and attached to an
# experiment. The script is restartable: fixtures and the null sweep skip work already
# done, and the gates and the legacy reproduction are cheap enough to rerun.
#
# Order matters. Fixtures precede the environment record; the environment record precedes
# anything that asserts against it; the gates and the legacy reproduction precede every
# scientific number; the null sweep precedes the decisions. REPORT.md is hand-maintained
# (not regenerated).
#
# Two rules are inherited from run_v2_sequence.sh, and both come from mistakes:
#   1. `set -e` plus an ERR trap, so nothing downstream of a failure runs.
#   2. Commands are never piped into grep/head. Under `pipefail`, a grep that matches
#      nothing (exit 1) or a head that closes the pipe (SIGPIPE) would abort a step that
#      actually succeeded. Output goes to a file; the file is parsed separately.
#
# Usage:  ./regenerate.sh [--skip-null]

set -euo pipefail
trap 'st=$?; echo; echo "STEP FAILED (exit $st) at line $LINENO — "\
      "sequence aborted, nothing downstream ran."; exit $st' ERR
cd "$(dirname "$0")"

E="${RX_EXPERIMENT:-e:3}"
PY="conda run -n pycpt python"
LOGDIR=outputs/steplogs
mkdir -p "$LOGDIR"
SKIP_NULL=0
[ "${1:-}" = "--skip-null" ] && SKIP_NULL=1

step() { echo; echo "=== $* ==="; }

step "1/10  fixtures"
rx run exec -e "$E" --include-untracked -- $PY src/fetch_ersst.py

# outputs/env.json is one of the files every benchmark locks, and record_env.py stamps a
# fresh `recorded.written_utc` on every write. Rewriting it here would therefore drift the
# lock set and every submission in step 8 would be refused. The record is verified against
# the hash the benchmarks were registered with, and written only when it is absent.
step "2/10  environment record (content hashes, SPEC 2) — verified, not rewritten"
if [ ! -f outputs/env.json ]; then
  echo "  outputs/env.json absent — writing it."
  echo "  NOTE: a freshly written record carries a new timestamp and will not match the"
  echo "        hash the *-v2 benchmarks locked. Submissions will refuse until the"
  echo "        benchmarks are re-registered against this machine's record."
  rx run exec -e "$E" --include-untracked -- $PY src/record_env.py
else
  rx benchmark show atlas-wf-v2 > "$LOGDIR/env_lock.log" 2>&1
  ENVCHECK=$(python3 - <<'EOF'
import hashlib, pathlib, re, sys
locked = None
for line in pathlib.Path("outputs/steplogs/env_lock.log").read_text().splitlines():
    m = re.search(r"outputs/env\.json\s+\(([0-9a-f]+)\.\.\.", line)
    if m:
        locked = m.group(1)
        break
if locked is None:
    print("no-lock-entry"); sys.exit()
actual = hashlib.sha256(pathlib.Path("outputs/env.json").read_bytes()).hexdigest()
print("match" if actual.startswith(locked) else f"drift {actual[:12]} vs {locked}")
EOF
)
  echo "  env.json vs locked hash: $ENVCHECK"
  case "$ENVCHECK" in
    match) : ;;
    *) echo "ENVIRONMENT RECORD DRIFT — every *-v2 submission would be refused."
       echo "Restore outputs/env.json to the locked bytes before continuing."
       exit 1 ;;
  esac
fi

step "3/10  specification checks (SPEC, 96 checks)"
rx run exec -e "$E" --include-untracked -- $PY probes/spec_check.py

step "3b/10 all three scorer-agreement links (Amendment 1 section 2)"
rx run exec -e "$E" --include-untracked -- $PY probes/scorer_chain.py

step "4/10  year-wrap test (inherited from v4zeek)"
rx run exec -e "$E" --include-untracked -- $PY tests/test_wrap.py

step "5/10  fast vs slow scorer agreement (SPEC 16, tolerance 1e-8)"
rx run exec -e "$E" --include-untracked -- $PY tests/test_scorer_agreement.py

# The guard must not be able to read a gates.json an earlier suite left behind. An atlas
# was once produced on stale gate evidence; the file is deleted before the suite runs and
# the result is required to carry spec_version == amendment-1.
step "6/10  harness gates (SPEC 17: climatology, synthetic, shuffle)"
rm -f outputs/gates.json
rx run exec -e "$E" --include-untracked -- $PY probes/gates.py
GUARD=$(python3 - <<'EOF'
import json, sys
try:
    d = json.load(open("outputs/gates.json"))
except Exception as e:
    print(f"missing ({type(e).__name__})"); sys.exit()
print(f"{d.get('status')}|{d.get('failed')}|{d.get('spec_version')}|{d.get('passed')}/{d.get('gates')}")
EOF
)
echo "  gate guard: $GUARD"
case "$GUARD" in
  ok\|0\|amendment-1\|*) : ;;
  *) echo "GATE FAILURE OR STALE GATE FILE — stopping before any scientific number is read."
     exit 1 ;;
esac

step "7/10  legacy reproduction (SPEC 9.1 provenance)"
rx run exec -e "$E" --include-untracked -- $PY legacy/reproduce_agu3.py

step "8/10  real atlas — every arm, both protocols, both weightings"
rx run exec -e "$E" --include-untracked -- $PY run_atlas.py --real
for proto in walkforward kfold; do
  bench="atlas-wf-v2"; [ "$proto" = kfold ] && bench="atlas-kf-v2"
  for arm in climatology pooled zones-shared zones-specific; do
    rx run benchmark "$bench" -e "$E" --include-untracked -p "arm=$arm" \
      -- --arm "$arm" --protocol "$proto" \
      --per-zone "outputs/perzone_v2_${proto}_${arm}.json"
  done
done
for w in mam ond; do
  for arm in pooled zones; do
    rx run benchmark "fixedmean-${w}-v2" -e "$E" --include-untracked -p "arm=$arm" \
      -- --arm "$arm"
  done
  for arm in climatology pooled zones-specific; do
    rx run benchmark "grid-${w}-v2" -e "$E" --include-untracked -p "arm=$arm" \
      -- --arm "$arm"
  done
done
rx run exec -e "$E" --include-untracked -- $PY probes/collect_secondary.py

if [ "$SKIP_NULL" = 0 ]; then
  step "9/10  the 6 x 200 paired null sweep (restartable)"
  rx run exec -e "$E" --include-untracked -- $PY run_atlas.py --null
  rx run exec -e "$E" --include-untracked -- $PY run_atlas.py --sensitivity 20
else
  step "9/10  null sweep SKIPPED (--skip-null)"
fi

step "10/10  decisions, stability, figures"
rx run exec -e "$E" --include-untracked -- $PY probes/decide.py
rx run exec -e "$E" --include-untracked -- $PY probes/stability.py

echo
echo "done. outputs/*.json and outputs/figures/ are current."
echo "REPORT.md is hand-maintained — not overwritten. See README.md."
