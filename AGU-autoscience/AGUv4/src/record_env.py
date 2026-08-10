"""record_env.py — write outputs/env.json, the thing every production run asserts against.

A git sha plus a dirty-file COUNT cannot detect source drift: editing a line in a
tracked file leaves both unchanged. Both library checkouts here are dirty (rosetta
13 files, deepscale 15), so the sha is not sufficient and the count is close to
useless. This records the actual content instead.

For each library it stores:
  - the HEAD sha and the branch;
  - a sha256 for EVERY source file under src/, tracked or not, as an explicit map;
  - one `tree_sha256` over the sorted (relpath, filehash) pairs, so a single scalar
    detects any addition, deletion or edit;
  - a `diff_sha256` over `git diff HEAD` for the whole repo, which additionally
    catches edits outside src/.

The uncommitted diffs themselves are deliberately NOT copied into this project.
Ezekiel's instruction on the rosetta checkout was not to absorb its unrelated
work-in-progress, and the per-file hash map detects drift precisely without
duplicating anyone's WIP. The one library change this project depends on —
rosetta's `sst/ersst-v5` catalog entry — is preserved on its own at
patches/rosetta-ersst-v5.patch.

`asserted` holds only content hashes and is what spec_check compares. `recorded`
holds provenance that legitimately varies (timestamps, interpreter path) and is
never asserted.

Run: rx run exec -e e:N -- conda run -n pycpt python src/record_env.py
"""
from __future__ import annotations

import hashlib
import importlib
import json
import platform
import subprocess
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs" / "env.json"

SKIP_DIRS = {"__pycache__", ".git", ".ipynb_checkpoints", ".pytest_cache", ".mypy_cache"}
SKIP_SUFFIX = {".pyc", ".pyo", ".so", ".DS_Store"}

FIXTURES = {"chirps_v3": DATA / "chirps_v3_ea_monthly.nc",
            "ersst_v5": DATA / "ersst_v5_monthly.nc"}

INHERITED = ("bench.py", "batched.py", "candidates/climatology.py",
             "tests/test_wrap.py", "probes/grid_sweep.py")

PACKAGES = ("numpy", "xarray", "scipy", "sklearn", "netCDF4", "matplotlib", "cartopy")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def source_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix in SKIP_SUFFIX:
            continue
        yield p


def hash_tree(root: Path):
    """Per-file hashes plus one scalar over the sorted (relpath, hash) pairs."""
    files = {}
    for p in source_files(root):
        files[str(p.relative_to(root))] = sha256_file(p)
    manifest = "\n".join(f"{k}  {v}" for k, v in sorted(files.items()))
    return files, sha256_text(manifest)


def git(repo: Path, *args) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True)


def library(mod_name: str):
    mod = importlib.import_module(mod_name)
    pkg_dir = Path(mod.__file__).resolve().parent          # .../src/<name>
    src_dir = pkg_dir.parent                               # .../src
    repo = src_dir.parent                                  # repo root
    files, tree = hash_tree(src_dir)
    status = [ln for ln in git(repo, "status", "--short").splitlines() if ln.strip()]
    return {
        "repo": str(repo),
        "head": git(repo, "rev-parse", "HEAD").strip(),
        "branch": git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip(),
        "dirty_files": len(status),
        "dirty_list": sorted(ln[3:] for ln in status),
        "src_dir": str(src_dir.relative_to(repo)),
        "n_source_files": len(files),
        "tree_sha256": tree,
        "diff_sha256": sha256_text(git(repo, "diff", "HEAD")),
        "file_sha256": files,
    }


def main():
    asserted = {
        "fixtures": {k: {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
                     for k, p in FIXTURES.items() if p.exists()},
        "inherited_from_v4zeek": {rel: sha256_file(ROOT / rel) for rel in INHERITED},
        "libraries": {name: library(name) for name in ("rosetta", "deepscale")},
    }
    missing = [k for k, p in FIXTURES.items() if not p.exists()]
    if missing:
        raise SystemExit(f"REFUSING TO WRITE env.json: missing fixture(s) {missing}")

    versions = {}
    for m in PACKAGES:
        try:
            versions[m] = getattr(importlib.import_module(m), "__version__", "?")
        except Exception as e:
            versions[m] = f"UNAVAILABLE ({type(e).__name__})"

    env = {
        "asserted": asserted,
        "recorded": {
            "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "python": platform.python_version(),
            "executable": sys.executable,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "packages": versions,
        },
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(env, indent=2, sort_keys=True) + "\n")

    for name, lib in asserted["libraries"].items():
        print(f"{name:10s} head={lib['head'][:12]}  branch={lib['branch']}  "
              f"dirty={lib['dirty_files']}  files={lib['n_source_files']}")
        print(f"{'':10s} tree_sha256={lib['tree_sha256']}")
        print(f"{'':10s} diff_sha256={lib['diff_sha256']}")
    for k, v in asserted["fixtures"].items():
        print(f"{k:10s} {v['bytes']:>12,} B  sha256={v['sha256']}")
    print(f"\nwrote {OUT}  ({OUT.stat().st_size:,} bytes)")
    print(json.dumps({
        "rosetta_tree_sha256": asserted["libraries"]["rosetta"]["tree_sha256"],
        "deepscale_tree_sha256": asserted["libraries"]["deepscale"]["tree_sha256"],
        "n_source_files": sum(l["n_source_files"] for l in asserted["libraries"].values()),
        "status": "ok",
    }))


if __name__ == "__main__":
    main()
