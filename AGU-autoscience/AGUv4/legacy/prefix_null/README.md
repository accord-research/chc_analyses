# The null produced before the runner was fixed

600 valid unique rows, 200 replicates x 3 arms, 0 errors — it satisfies the completeness
guard exactly. It is archived rather than used because the guard's manifest is supposed to
pin the hash of the code that produced the artifact, and this artifact predates five
runner fixes:

  1. `run_v2_sequence.sh` lacked `set -e`, so failures after the gate did not stop it.
  2. There was no post-null completeness guard.
  3. Restart keyed on `zones-specific` alone, so a replicate missing its other two arms
     looked finished.
  4. `sensitivity()` was defined after the `main()` call, so `--sensitivity` raised
     NameError.
  5. No manifest pinned the producing code at all.

None of those five touches `_job` / `replicate_all_arms`, so the re-run under the corrected
runner is expected to reproduce this file bit-for-bit. `outputs/null_reproduction.json`
records whether it did — which is a stronger statement about the fixes than any argument.

Also here: the field-permutation sensitivity sweep, stopped at 12 of 20 replicates when the
sequence was halted. Superseded, adjudicates nothing, kept only as a record.
