# legacy/ — history, contracts, and discarded paths

Not on the live regeneration path (except `reproduce_agu3.py`, which is the AGUv3
provenance check called from `./regenerate.sh`).

| path | what |
|---|---|
| `contracts/` | Pre-result `SPEC.md` + `SPEC_AMENDMENT_1.md` (frozen design contracts) |
| `AGUv3/` | Pinned AGUv3 scripts + published tables (reference for reproduction) |
| `reproduce_agu3.py` | Runs AGUv3 scripts against locked fixtures; diffs tables |
| `v1_snapshot/` | Exact files locked by `atlas-*-v1` / secondary `*-v1` benches |
| `prefix_null/` | Null artifact from before five runner fixes (bit-identical re-run verified) |
| `ungated_discards/` | Atlas produced when a stale gates file passed the guard |
| `probes/` | One-shot / obsolete scripts (`orient`, `smoke_discovery`, old `make_report`) |
| `patches/` | Rosetta `sst/ersst-v5` catalog patch used to fetch ERSST; `src/record_env.py` is a locked benchmark input and its docstring still names the pre-declutter location `patches/` |
| `recover_AGUv2.py` | Earlier AGUv2 recover script, kept for lineage |

Ephemeral sandboxes (recreated by `reproduce_agu3.py`, gitignored): `run/`, `AGUv0/`.
