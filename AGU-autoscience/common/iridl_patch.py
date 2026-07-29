"""Transient IRIDL fallback for the NMME layer, while the CCSR endpoint is down.

The AGU analyses fetch NMME models from `forecast.ccsr.columbia.edu` (CCSR). When that
endpoint is unavailable, `apply()` re-points those products, in rosetta's *in-memory*
catalog only, at the **same models on the IRI Data Library** (the canonical NMME archive
CCSR mirrors). Fetches then land in the nuthatch cache under the ordinary CCSR product
keys, so:

  * analysis code runs unchanged (still calls `rosetta.fetch("nmme/cesm1", ...)`);
  * nothing on disk (catalog.yaml) is modified;
  * on recovery, re-fetching with `cache_mode="overwrite"` **replaces** this IRIDL data
    with canonical CCSR data — so the final product is still IRIDL-free.

Labeled, temporary bridge — not a permanent route. Ported from
`analyses/chc_ethiopia/iridl_patch.py` (see `IRIDL_FALLBACK_NOTES.md` for the full
mechanism, gotchas, and recovery-poller pattern). Confirmed live on IRIDL 2026-07-28
for CCSM4 / CESM1 / CanSIPS-IC4 (SST + precip, both CanSIPS streams).

NOTE — model coverage: this covers 3 of the 4 models AGUv0 used. **GEOSS2S** (NASA-GMAO)
is *not* included: its IRIDL NMME sub-collection name could not be confirmed during the
outage (candidates `.NASA-GMAO-GEOSS2S`, `.NASA-GEOSS2S`, `.NASA-GMAO-GEOS-S2S` all 404).
Under the fallback the MME therefore runs on {CESM1, CCSM4, CanSIPS-IC4}; since the model
set is one of the searchable axes, a 3-model MME is an acceptable default. To add GEOSS2S,
confirm its IRIDL path (`…/dods.dds` → 200) and append a `_flat(...)`/split entry below.
"""
import urllib.request
import rosetta.catalog as _cat
from nuthatch.nuthatch import set_global_cache_variables as _scv

_B = "https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME"


def _flat(model):
    """CCSM4 / CESM1: one flat .MONTHLY collection (S/L/M/Y/X); SST already in Celsius."""
    return {
        "adapter": "opendap",
        "source_url": f"{_B}/.{model}/.MONTHLY",
        "variables": {
            "sst":    {"native_name": "sst",  "units": "C",      "target_units": "C"},
            "precip": {"native_name": "prec", "short_name": "pr", "units": "mm/day", "target_units": "mm/day"},
            "temp":   {"native_name": "tref", "units": "K",      "target_units": "C"},
        },
        "grid": {"lat_res": 1.0, "lon_res": 1.0, "forecast_members": 10, "hindcast_members": 10,
                 "hindcast_range": [1982, 2026], "forecast_range": [2014, None]},
    }


# CanSIPS-IC4: split HINDCAST / FORECAST streams; SST in Kelvin -> convert to C.
_CANSIPS = {
    "adapter": "opendap", "split_streams": True, "append_streams": True,
    "source_url": f"{_B}/.CanSIPS-IC4/.{{stream}}/.MONTHLY",
    "variables": {
        "sst":    {"native_name": "sst",  "units": "K",      "target_units": "C"},
        "precip": {"native_name": "prec", "short_name": "pr", "units": "mm/day", "target_units": "mm/day"},
        "temp":   {"native_name": "tref", "units": "K",      "target_units": "C"},
    },
    "grid": {"lat_res": 1.0, "lon_res": 1.0, "forecast_members": 20, "hindcast_members": 20,
             "hindcast_range": [1980, 2025], "forecast_range": [2024, None]},
}

IRIDL_ENTRIES = {
    "nmme/ccsm4":      _flat("COLA-RSMAS-CCSM4"),
    "nmme/cesm1":      _flat("COLA-RSMAS-CESM1"),
    "nmme/cansipsic4": _CANSIPS,
}

# Models that HAVE an IRIDL fallback here (use to filter a MODELS list under the patch).
FALLBACK_MODELS = list(IRIDL_ENTRIES.keys())

_CCSR_PROBE = "https://forecast.ccsr.columbia.edu/data/NMME/COLA-RSMAS/CESM1/sst.dds"


def ccsr_reachable(url: str = _CCSR_PROBE, timeout: int = 20) -> bool:
    """True if the canonical CCSR endpoint is serving (HTTP 200) — for recovery pollers.
    A direct HTTP probe, NOT a rosetta.fetch (which would return the cached IRIDL data)."""
    try:
        return urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=timeout
        ).status == 200
    except Exception:
        return False


def apply(verbose: bool = True):
    """Route the NMME products to IRIDL and set cache_mode so writes never block on the
    interactive overwrite prompt. Call once at startup, before any NMME fetch."""
    _scv(cache_mode="overwrite")
    _cat._catalog.update(IRIDL_ENTRIES)

    # The opendap (IRIDL) adapter normalizes precip to the CF short name `pr`; the ccsr
    # adapter keys it as `precip` (what analysis code indexes). Wrap fetch to rename back.
    import rosetta as _r
    if not getattr(_r.fetch, "_iridl_wrapped", False):
        _orig = _r.fetch

        def _fetch(*a, **k):
            ds = _orig(*a, **k)
            try:
                if "pr" in ds and "precip" not in ds:
                    ds = ds.rename({"pr": "precip"})
            except Exception:
                pass
            return ds
        _fetch._iridl_wrapped = True
        _r.fetch = _fetch

    if verbose:
        print("[IRIDL PATCH] nmme/{ccsm4,cesm1,cansipsic4} -> IRI Data Library "
              "(transient fallback; CCSR overwrites on recovery). GEOSS2S not covered.")


if __name__ == "__main__":
    print("CCSR reachable:", ccsr_reachable())
    print("Fallback models:", FALLBACK_MODELS)
