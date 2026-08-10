"""discovery.py — SPEC 4 (zone discovery) and SPEC 5 (the rainy-season detector).

Rainfall only. No SST, no coordinates, no country boundaries, no expert region enters
anything in this file. Everything is computed from the TRAINING years of an outer fold
and from nothing else, which is the invariance SPEC 6 states and SPEC 14 depends on.

The feature construction is AGUv3's, unchanged:
  block 1 — each cell's standardised 12-month climatological cycle shape (12 columns)
  block 2 — each cell's loadings on the leading 5 EOFs of its monthly anomalies
  blocks equal-weighted by z-scoring columns then scaling block b by 1/sqrt(n_cols_b)

What SPEC changes relative to AGUv3, and only this:
  - every quantity comes from the training years, not the full record;
  - k is the LARGEST k in 2..8 with mean bootstrap ARI >= 0.90 (else argmax), not argmax;
  - plateau peaks are merged and identical windows de-duplicated;
  - wrapping windows are labelled by their LAST month;
  - at most two windows per zone.

The 20 bootstrap resamples are drawn once and shared across k, which is what SPEC 15's
"1 + 20 bootstrap re-featurisations = 21" per discovery run means. AGUv3 redrew them
inside its k loop; the legacy reproduction keeps that behaviour, this does not.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

# ── locked constants (SPEC 4, SPEC 5) ─────────────────────────────────────────
K_RANGE = tuple(range(2, 9))
N_BOOT = 20
N_EOF = 5
TAU = 0.90
KMEANS_KW = dict(n_init=10, random_state=0)
MAX_WINDOWS = 2
PEAK_FRAC = 0.15
DAYS_PER_MONTH = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MONTH_INITIAL = "JFMAMJJASOND"


# ── feature construction ──────────────────────────────────────────────────────
def valid_mask(cyc):
    """SPEC 4: finite 12-month climatology and annual total > 1e-3. `cyc` is (cell, 12)."""
    return np.isfinite(cyc).all(axis=1) & (cyc.sum(axis=1) > 1e-3)


def _z_cols(M):
    return (M - M.mean(0)) / (M.std(0) + 1e-9)


def build_features(monthly, month_of_col, cols, good):
    """Both feature blocks for the cells in `good`, from the columns in `cols`.

    monthly       (n_cell, n_col) float, one column per (year, month) of the record
    month_of_col  (n_col,) int in 1..12
    cols          column indices to use — a fold's training months, or a bootstrap draw
    good          (n_cell,) bool, the valid-cell mask

    Returns X (n_good, 17).
    """
    sub = monthly[:, cols]
    mo = month_of_col[cols]

    # block 1 — standardised climatological cycle shape
    cyc = np.empty((sub.shape[0], 12))
    for m in range(12):
        sel = mo == (m + 1)
        cyc[:, m] = sub[:, sel].mean(axis=1) if sel.any() else np.nan
    X1 = cyc[good]
    X1 = (X1 - X1.mean(1, keepdims=True)) / (X1.std(1, keepdims=True) + 1e-6)

    # block 2 — EOF loadings of per-cell-standardised monthly anomalies
    anom = sub - cyc[:, mo - 1]
    A = anom[good]
    A = np.nan_to_num(A / (A.std(1, keepdims=True) + 1e-6))
    U, _, _ = np.linalg.svd(A, full_matrices=False)
    X2 = U[:, :N_EOF]

    return np.hstack([_z_cols(X1) / np.sqrt(X1.shape[1]),
                      _z_cols(X2) / np.sqrt(X2.shape[1])])


def cycle_mm_per_month(monthly, month_of_col, cols, cells, weights):
    """A zone's area-weighted mean annual cycle in mm/month (SPEC 5)."""
    sub = monthly[np.ix_(cells, cols)]
    w = weights[cells]
    series = (sub * w[:, None]).sum(0) / w.sum()
    mo = month_of_col[cols]
    out = np.empty(12)
    for m in range(12):
        sel = mo == (m + 1)
        out[m] = series[sel].mean() if sel.any() else np.nan
    return out * DAYS_PER_MONTH


# ── SPEC 5: the season detector ───────────────────────────────────────────────
def peak_months(cyc):
    """AGUv3 peak_months, unchanged: circular local maxima above 15% of the maximum."""
    return [i for i in range(12)
            if cyc[i] >= cyc[(i - 1) % 12] and cyc[i] >= cyc[(i + 1) % 12]
            and cyc[i] > PEAK_FRAC * cyc.max()]


def merge_plateau_peaks(peaks, cyc):
    """SPEC 5: merge circularly adjacent peaks, keeping the higher; ties keep the earlier."""
    if len(peaks) < 2:
        return list(peaks)
    kept = []
    for p in sorted(peaks):
        if kept and (p - kept[-1]) % 12 == 1:
            prev = kept[-1]
            kept[-1] = prev if cyc[prev] >= cyc[p] else p
        else:
            kept.append(p)
    # close the circle
    if len(kept) > 1 and (kept[0] - kept[-1]) % 12 == 1:
        a, b = kept[-1], kept[0]
        kept = kept[1:-1] + [a if cyc[a] >= cyc[b] else b]
    return sorted(kept)


def window_for_peak(cyc, p):
    """AGUv3 windows_for, unchanged: the best 3-month window containing peak p."""
    best, best_sum = None, -np.inf
    for s in ((p - 2) % 12, (p - 1) % 12, p):
        idx = [(s + j) % 12 for j in range(3)]
        if p in idx and cyc[idx].sum() > best_sum:
            best_sum, best = cyc[idx].sum(), idx
    return best


def detect_windows(cyc, max_windows=MAX_WINDOWS):
    """SPEC 5 in full: peaks -> plateau merge -> windows -> de-duplicate -> cap at two.

    Returns a list of (label, months) where `months` is 1-based calendar months in
    order and `label` is the initial-letter string, e.g. ("OND", [10, 11, 12]).
    """
    peaks = merge_plateau_peaks(peak_months(cyc), cyc)
    seen, out = set(), []
    for p in peaks:
        idx = window_for_peak(cyc, p)
        key = tuple(idx)
        if key in seen:
            continue
        seen.add(key)
        out.append((float(cyc[idx].sum()), "".join(MONTH_INITIAL[i] for i in idx),
                    [i + 1 for i in idx]))
    out.sort(key=lambda t: -t[0])                       # cap keeps the wettest windows
    out = out[:max_windows]
    out.sort(key=lambda t: t[2][0])                     # then report in calendar order
    return [(lab, months) for _, lab, months in out]


def window_wraps(months):
    return months[0] > months[-1]


# ── SPEC 4: the partition ─────────────────────────────────────────────────────
@dataclass
class Partition:
    k: int
    labels: np.ndarray                  # (n_good,) int in 0..k-1, west->east ordered
    ari_curve: dict                     # k -> mean bootstrap ARI
    ari_sd: dict
    silhouette: dict
    cell_index: np.ndarray              # indices into the full cell axis for `labels`
    weights: np.ndarray                 # cos(lat) of those cells
    windows: dict = field(default_factory=dict)   # zone -> [(label, months), ...]
    cycles: dict = field(default_factory=dict)    # zone -> 12-vector mm/month

    def zone_cells(self, z):
        return self.cell_index[self.labels == z]

    def zone_weight(self, z):
        return float(self.weights[self.labels == z].sum())

    def total_weight(self):
        return float(self.weights.sum())


def cluster(X, k, seed=0):
    return KMeans(n_clusters=k, random_state=seed, n_init=KMEANS_KW["n_init"]).fit_predict(X)


def select_k(ari):
    """SPEC 4: largest k in 2..8 with mean bootstrap ARI >= TAU, else argmax."""
    ok = [k for k in sorted(ari) if ari[k] >= TAU]
    return max(ok) if ok else max(ari, key=ari.get)


def discover(monthly, month_of_col, year_of_col, train_years, lats, lons,
             k_range=K_RANGE, n_boot=N_BOOT, seed=0, force_k=None,
             compute_silhouette=True):
    """One complete discovery run for one outer fold (SPEC 4 + SPEC 5).

    monthly       (n_cell, n_col) precipitation in mm/day on the 0.25 deg grid
    month_of_col  (n_col,) calendar month 1..12
    year_of_col   (n_col,) calendar year
    train_years   the fold's training years
    lats, lons    (n_cell,) cell centres, used ONLY for west->east relabelling and
                  for cos(lat) weights — never as clustering features

    force_k       bypass selection (k=1 pooled arm, or the legacy hierarchy levels)
    """
    cols = np.flatnonzero(np.isin(year_of_col, train_years))

    # valid-cell mask from the training years only
    mo = month_of_col[cols]
    cyc_all = np.empty((monthly.shape[0], 12))
    for m in range(12):
        sel = mo == (m + 1)
        cyc_all[:, m] = monthly[:, cols][:, sel].mean(axis=1) if sel.any() else np.nan
    good = valid_mask(cyc_all)
    cell_index = np.flatnonzero(good)
    weights = np.cos(np.deg2rad(lats[good]))

    if force_k == 1:
        labels = np.zeros(len(cell_index), dtype=int)
        part = Partition(1, labels, {}, {}, {}, cell_index, weights)
        _attach_windows(part, monthly, month_of_col, cols)
        return part

    X0 = build_features(monthly, month_of_col, cols, good)

    # 20 bootstrap resamples, drawn once and shared across k (SPEC 15)
    rng = np.random.default_rng(seed)
    tr_years = np.asarray(sorted(train_years))
    boot_X = []
    for b in range(n_boot):
        ysel = rng.choice(tr_years, size=len(tr_years), replace=True)
        bcols = np.concatenate([np.flatnonzero(year_of_col == y) for y in ysel])
        boot_X.append(build_features(monthly, month_of_col, bcols, good))

    ari, ari_sd, sil, ref = {}, {}, {}, {}
    for k in k_range:
        L0 = cluster(X0, k)
        ref[k] = L0
        scores = [adjusted_rand_score(L0, cluster(Xb, k, seed=b + 1))
                  for b, Xb in enumerate(boot_X)]
        ari[k] = float(np.mean(scores))
        ari_sd[k] = float(np.std(scores))
        sil[k] = (float(silhouette_score(X0, L0, sample_size=3000, random_state=0))
                  if compute_silhouette and len(set(L0)) > 1 else float("nan"))

    k = int(force_k) if force_k else int(select_k(ari))
    labels = ref[k] if k in ref else cluster(X0, k)

    # deterministic west->east relabelling by centroid longitude (SPEC 4)
    zlon = lons[good]
    order = {z: i for i, z in enumerate(sorted(np.unique(labels),
                                               key=lambda z: zlon[labels == z].mean()))}
    labels = np.array([order[z] for z in labels])

    part = Partition(k, labels, ari, ari_sd, sil, cell_index, weights)
    _attach_windows(part, monthly, month_of_col, cols)
    return part


def _attach_windows(part, monthly, month_of_col, cols):
    for z in range(part.k):
        cells = part.zone_cells(z)
        if len(cells) == 0:
            part.cycles[z], part.windows[z] = np.zeros(12), []
            continue
        w = np.cos(np.deg2rad(np.ones(len(cells))))     # placeholder, replaced below
        cyc = _zone_cycle(monthly, month_of_col, cols, cells, part, z)
        part.cycles[z] = cyc
        part.windows[z] = detect_windows(cyc)
        del w


def _zone_cycle(monthly, month_of_col, cols, cells, part, z):
    w = part.weights[part.labels == z]
    sub = monthly[np.ix_(cells, cols)]
    series = (sub * w[:, None]).sum(0) / w.sum()
    mo = month_of_col[cols]
    out = np.empty(12)
    for m in range(12):
        sel = mo == (m + 1)
        out[m] = series[sel].mean() if sel.any() else np.nan
    return out * DAYS_PER_MONTH
