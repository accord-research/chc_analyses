"""searchspace.py — the forecast-design search space (AGUv1).

A forecast *configuration* is one point in a labeled multi-axis tensor, and the design problem is
`argmax over the tensor of cross-validated skill(config)`, evaluated identically under leave-one-
year-out CV. The driver maps each `Config` to a scored row; `targets.py` supplies the `target` axis
(each region's discovered rainy seasons), so lead is a property *of a target's best config*.

## The tensor (widened pass)

    target  ×  predictor_source  ×  predictor_domain  ×  transform  ×  method  ×  eof_modes  ×  lead

scored on all four metrics. `downscale` (native resolution here) is the one remaining full-tensor
axis held fixed; promoting it adds a resolution sweep with no change to the machinery.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable


# ─────────────────────────── axis value sets ───────────────────────────
PREDICTOR_SOURCES = ("obs_sst_field", "gcm_mos_sst", "gcm_mos_precip", "persistence",
                     "obs_index", "gcm_index")
METHODS = ("cca", "qm", "regression")
PREDICTOR_DOMAINS = ("indo_pacific", "indian", "pacific")   # SST-field predictors only
INDEX_NAMES = ("nino34", "iod", "wpg", "wvg", "iwhg")       # engineered operational indices
EOF_MODES = (4, 8)                                          # CCA truncation
TRANSFORMS = ("std_anom", "raw")                            # predictand preprocessing
LEADS = (0, 1, 2, 3, 4)                                     # months before the season start
METRICS = ("generalized_roc", "rpss", "pearson_r", "hit_rate")

# markers used when an axis does not apply to a source/method:
_NA_DOMAIN = "region"    # precip-MOS & persistence: predictor domain IS the target region
_NA_EOF = 0             # qm & regression: no EOF truncation
FIXED = dict(downscale="none")

_SST_SOURCES = ("obs_sst_field", "gcm_mos_sst")


@dataclass(frozen=True)
class Config:
    target: str
    predictor_source: str
    method: str
    lead: int
    predictor_domain: str = "indo_pacific"
    transform: str = "std_anom"
    eof_modes: int = 4
    downscale: str = FIXED["downscale"]

    def key(self) -> str:
        return (f"{self.target}|{self.predictor_source}|{self.method}|L{self.lead}"
                f"|{self.predictor_domain}|{self.transform}|m{self.eof_modes}")


def enumerate_configs(targets: Iterable[str]) -> list[Config]:
    """All valid configs in the tensor for the given targets (built directly so no invalid
    source/method/domain/eof combinations are produced)."""
    out = []
    for tgt in targets:
        for lead in LEADS:
            for tr in TRANSFORMS:
                # SST-field predictors: search domain × EOF modes, method = CCA
                for dom in PREDICTOR_DOMAINS:
                    for eof in EOF_MODES:
                        for src in _SST_SOURCES:
                            out.append(Config(tgt, src, "cca", lead, dom, tr, eof))
                # precip-MOS: EOF modes (CCA) + a quantile-mapping variant; domain = region
                for eof in EOF_MODES:
                    out.append(Config(tgt, "gcm_mos_precip", "cca", lead, _NA_DOMAIN, tr, eof))
                out.append(Config(tgt, "gcm_mos_precip", "qm", lead, _NA_DOMAIN, tr, _NA_EOF))
                # engineered scalar indices (observed = perfect-prog, gcm = operational forecast)
                for idx in INDEX_NAMES:
                    for src in ("obs_index", "gcm_index"):
                        out.append(Config(tgt, src, "regression", lead, idx, tr, _NA_EOF))
                # persistence baseline: scalar OLS
                out.append(Config(tgt, "persistence", "regression", lead, _NA_DOMAIN, tr, _NA_EOF))
    return out


def tensor_shape(targets) -> dict:
    tgts = list(targets)
    cfgs = enumerate_configs(tgts)
    return {"axes": {"target": len(tgts), "predictor_source": len(PREDICTOR_SOURCES),
                     "predictor_domain": len(PREDICTOR_DOMAINS), "transform": len(TRANSFORMS),
                     "method": len(METHODS), "eof_modes": len(EOF_MODES), "lead": len(LEADS)},
            "valid_cells": len(cfgs), "metrics_per_cell": len(METRICS)}


if __name__ == "__main__":
    import json, sys
    sys.path.insert(0, ".")
    import targets as T
    tg = [t.name for t in T.discover_targets()]
    print("targets:", tg)
    print(json.dumps(tensor_shape(tg), indent=2))
