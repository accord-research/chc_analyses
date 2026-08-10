# Archived probes

Not on `./regenerate.sh` or `./run_v2_sequence.sh`. Kept so early `rx` runs remain
readable under `rx vc checkout`.

| file | role |
|---|---|
| `orient.py` | Phase 0 inventory (fixtures, inherited harness, environment) |
| `smoke_discovery.py` | One-shot discovery timing / budget check before null registration |
| `make_report.py` | Obsolete generator for an earlier REPORT layout — **does not produce** the current `REPORT.md` |

Live probes stay in `../../probes/` (`gates`, `scorer_chain`, `decide`, `stability`,
`spec_check`, `collect_secondary`, `null_reproduction`, `grid_sweep`).
`grid_sweep.py` remains live because `scorer_chain.py` imports it for SPEC §16 links.
