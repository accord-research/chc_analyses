# Discarded: produced without a passing v2 gate

`run_v2_sequence.sh`'s first version waited on the gate RUN and then read
`outputs/gates.json`. When that run was killed the wait returned, and the file it read was
the **v1** gates file left over from an earlier suite — so the guard passed on stale
evidence and the sequence went on to compute a real atlas.

Nothing here reached a benchmark leaderboard: `rx leaderboard atlas-wf-v2` had no
submissions at the time these were discarded, and they were never read by
`probes/decide.py`. They are kept only so the mistake is on the record.

The guard now: deletes `gates.json` before running the suite, requires the fresh file to
carry `spec_version == "amendment-1"`, and requires `failed == 0`.
