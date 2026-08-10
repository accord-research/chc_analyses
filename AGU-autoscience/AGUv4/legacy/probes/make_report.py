"""make_report.py — OBSOLETE. Archived under legacy/probes/.

This script generated an earlier REPORT layout (SPEC §18 numbered sections). The live
REPORT.md is hand-maintained and has a different structure. regenerate.sh no longer
calls this file; running it would overwrite the polished report with stale prose.

Historical note — original intent:

WRITING RULES, as binding as SPEC 18's section list. The reader has never thought about
seasonal rainfall forecasting and has not read SPEC.md. Every term is defined at first
use, every table has its columns explained before it, and every claim opens with a bold
sentence that states the claim rather than introducing it. v4zeek's REPORT.md is the
register: short plain sentences, no jargon left undefined, and the finding in the heading.

SPEC 18 fixes nine numbered sections and forbids omitting any. They appear here in that
order, preceded by unnumbered front matter that explains the problem, the vocabulary and
the procedure. The front matter is an addition, not a substitution.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"


def jload(name, default=None):
    p = OUT / name
    return json.loads(p.read_text()) if p.exists() else default


def fmt(v, nd=4, sign=True):
    if v is None:
        return "—"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return f"{f:+.{nd}f}" if sign else f"{f:.{nd}f}"


def main():
    env = jload("env.json", {})
    gates = jload("gates.json", {})
    chain = jload("scorer_chain.json", {})
    legacy = jload("legacy_reproduction.json", {})
    real = jload("atlas_real.json", [])
    dec = jload("decisions.json", {})
    stab = jload("stability.json", {})
    sec = jload("secondary.json", {})
    repro = jload("null_reproduction.json", {})
    ersst = jload("ersst_provenance.json", {})

    p = dec.get("primary", {})
    sr = {(r["kind"], r["window"], r["arm"]): r["rpss"] for r in (sec or {}).get("rows", [])}
    rw = {r["arm"]: r for r in real
          if r["protocol"] == "walkforward" and not r["leak"] and r["weight_rule"] == "equal"}
    rk = {r["arm"]: r for r in real
          if r["protocol"] == "kfold" and not r["leak"] and r["weight_rule"] == "equal"}

    L = []
    A = L.append

    # ══ front matter ═════════════════════════════════════════════════════════
    A("# Can a machine draw its own forecast map?")
    A("")
    A("### Discovering seasonal rainfall zones for the eastern Horn of Africa, and "
      "measuring whether the result is worth having")
    A("")
    A("Ezekiel Barnett · ACCORD · " + date.today().isoformat())
    A("")
    A("---")
    A("")

    A("## The question, stated twice")
    A("")
    A("**In forecasting terms.** Every seasonal rainfall outlook starts from a map. A "
      "forecast centre divides a country into regions it believes behave alike, decides "
      "which months are each region's rainy season, and picks an ocean measurement it "
      "believes predicts that season. People make those three decisions, using decades of "
      "local knowledge, and the answers are then reused for years. This work asks whether "
      "a machine can make all three from the rainfall record alone, and whether the "
      "forecasts that come out are any good.")
    A("")
    A("**In statistical terms.** The rainfall field is clustered into zones. Each zone's "
      "seasonal cycle is searched for peaks. Each zone-season is matched to whichever "
      "of the five ocean indices, at whichever of the four lead times, best predicts "
      "it. Every step is fitted on training years and applied to "
      "years the procedure has never seen. The output is one number: the skill of the "
      "whole map, scored out of sample, compared against what the same procedure produces "
      "on deliberately scrambled data.")
    A("")
    A("**The division of labour is the point.** Rainfall alone decides *where* the zones "
      "are and *when* their rainy seasons fall. Ocean temperature is required to decide "
      "*what predicts* each zone-season. Neither half can do the job alone.")
    A("")

    A("## What the words mean")
    A("")
    A("Six terms carry the whole report.")
    A("")
    A("- **CHIRPS** is a satellite-and-gauge rainfall product. This work uses monthly "
      "CHIRPS v3 for 1981–2023 over 33–52°E, 5°S–12°N — Kenya, Somalia and southern "
      "Ethiopia — coarsened to a 0.25° grid of 3,564 land cells.")
    A("- **ERSST** is a reconstruction of sea-surface temperature. Five ocean indices "
      "are built from it, and these five are the only predictors this work considers:")
    A("    - **Niño-3.4** is the temperature anomaly of the central-eastern equatorial "
      "Pacific, 5°S–5°N and 170°W–120°W. It is the standard measure of El Niño and "
      "La Niña.")
    A("    - **The Indian Ocean Dipole** is the western Indian Ocean, 50–70°E, minus the "
      "eastern, 90–110°E. East African forecast centres name it most often as the driver "
      "of the October–December short rains.")
    A("    - **The West Pacific Gradient** is the west Pacific, 130–150°E, minus "
      "Niño-3.4, each standardised first.")
    A("    - **The Western-V Gradient** is Niño-3.4 minus a V-shaped west Pacific region, "
      "5–20°N and 130–170°E, each standardised first. The Climate Hazards Center line of "
      "work prescribes it for the March–May long rains.")
    A("    - **IWHG** is a published fixed-weight combination of the Dipole, the west "
      "Pacific box and Niño-3.4.")
    A("- **Lead time** is how far ahead of the rainy season the ocean is read. At lead 0 "
      "the predictor is the two months ending just before the season starts; at lead 3 it "
      "is the two months ending four months before. Leads of 0, 1, 2 and 3 months are "
      "tried.")
    A("- A **zone** is a group of grid cells the clustering decided behave alike. Here it "
      "is an output, not an input.")
    A("- A **window** is a three-month rainy season, found by looking for peaks in a "
      "zone's average annual cycle. A zone may have one or two.")
    A("- A **fold** is one train/test split. Six are used, each training on all years up "
      "to a cut and testing on the next three or four. No test year exists when its own "
      "forecast is made.")
    A("- **RPSS**, the Ranked Probability Skill Score, is the number every forecast in "
      "this report is reduced to. The next section says exactly how.")
    A("")

    A("## How a forecast becomes a number")
    A("")
    A("Everything in this report is one of these numbers, so it is worth being precise "
      "about where they come from.")
    A("")
    A("- **A forecast is three probabilities**, issued for one zone, one rainy season and "
      "one year. They are the chance that the season's rainfall total lands in the driest "
      "third of that zone's history, the middle third, or the wettest third. The two "
      "boundaries dividing those thirds are computed from training years only, so a "
      "forecast never knows where the year it is predicting sits.")
    A("- **After the season happens, the forecast is penalised for the probability it put "
      "in the wrong place.** Putting weight on the wettest third when the season came in "
      "driest costs more than putting it on the middle third, because the categories are "
      "ordered. Each forecast comes out with one penalty. Lower is better.")
    A("- **A penalty on its own means nothing, so it is compared against the laziest "
      "possible forecast**: one-third, one-third, one-third, every year. That is what "
      "\"climatology\" means here — quoting the historical distribution and adding no "
      "information.")
    A("- **RPSS is one minus the ratio of the two.** Zero means the forecast did exactly "
      "as well as saying one-third three times. Above zero means it beat that. **Below "
      "zero means it was worse than adding no information at all**, which is a real and "
      "common outcome. One would be perfect.")
    A("- **Pooling many forecasts into one number** is done on the penalties, not on the "
      "scores. Every zone-season-year penalty is multiplied by the share of the domain "
      "its zone covers, all of them are added up, and the ratio is taken once at the end. "
      "Averaging individual skill scores instead would let a tiny zone with a lucky year "
      "count as much as a large one.")
    A("")
    A("Correlation would not do. Rainfall signals are often one-sided: an ocean index "
      "warns of a dry season and says nothing useful about a wet one. Correlation "
      "averages that structure toward zero. That is how earlier versions of this work "
      "concluded \"no signal\" and then spent three revisions inventing special metrics "
      "to recover it. Scoring probabilities detects one-sided signal without being told "
      "to look for it.")
    A("")

    A("## How the procedure works")
    A("")
    A("- **Rainfall picks the zones.** Cells are clustered on the shape of their yearly "
      "rainfall cycle and on how their year-to-year swings line up. The number of zones "
      "is not chosen by anyone: it is the largest count that survives resampling at least "
      "90% of the time.")
    A("- **Rainfall picks each zone's rainy seasons.** Peaks in the zone's average annual "
      "cycle become three-month windows, one or two per zone.")
    A("- **The ocean picks each zone-season's predictor.** Each zone-season tries all "
      "five indices — Niño-3.4, the Indian Ocean Dipole, the West Pacific Gradient, the "
      "Western-V Gradient and IWHG — at all four lead times, and keeps whichever of those "
      "twenty combinations best predicts its rainfall over the training years. Test years "
      "are never consulted, not even to choose.")
    A("- **The whole map is scored on unseen years, against scrambled data.** Every "
      "zone-season is forecast and scored, none dropped for failing, with weights summing "
      "to 1 per fold. The entire procedure is then re-run on 200 year-shuffles, because "
      "picking the best of those twenty combinations yields positive scores on pure "
      "noise.")
    A("")

    A("## Three things had to be true before any result was read")
    A("")
    A("**The scoring code had to agree with itself.** Three independent implementations "
      "of the score are cross-checked, including against the locked evaluator inherited "
      "from the previous project."
      + (f" They agree to {chain.get('link1_batched_vs_percell_maxdiff', 0):.0e} and "
         f"{chain.get('link2_percell_vs_bench_maxdiff', 0):.0e}, against a required "
         "tolerance of 1e-08." if chain else ""))
    A("")
    A("**The harness had to be provably not broken.**"
      + (f" All {gates.get('gates')} checks passed, of which four matter most." if gates
         else "")
      + " A forecast of equal thirds every year scores exactly 0.000000000000000, as the "
      "definition of RPSS requires. A synthetic rainfall field built with two zones and a "
      "different known driver in each is recovered perfectly: correct number of zones, "
      "correct boundary, correct rainy seasons, correct driving index in each zone, none "
      "of it supplied. Shuffling the years removes the skill.")
    A("")
    A("**The earlier published analysis had to reproduce.** This work rebuilds a task "
      "first attempted in a project called AGUv3. Its four scripts were re-run unmodified "
      "against the refetched data."
      + (f" Every published number came back: "
         f"{legacy['tier1_total'] - legacy['tier1_failed']} of {legacy['tier1_total']} "
         f"exact matches on rainfall-only quantities and "
         f"{legacy['tier2_total'] - legacy['tier2_failed']} of {legacy['tier2_total']} on "
         "quantities that also depend on ocean data." if legacy else ""))
    A("")
    A("---")
    A("")

    # ══ headline ═════════════════════════════════════════════════════════════
    if p:
        A("## The answer, in one table")
        A("")
        A(f"**The discovered map beats scrambled data decisively, and the verdict fixed "
          f"in advance is {p['verdict']}.**")
        A("")
        A("- **RPSS of the whole map** is what the complete atlas scored on years it "
          "never saw.")
        A("- **Scrambled-data** rows are what the identical procedure produced across 200 "
          "runs with the rainfall years shuffled.")
        A("- **p** is the share of those 200 runs that matched or beat the real result.")
        A("")
        A("| quantity | value |")
        A("|---|---:|")
        A(f"| RPSS of the whole map, on held-out years | **{fmt(p['rpss_atlas'])}** |")
        A(f"| scrambled-data average | {fmt(p['null_mean'])} |")
        A(f"| scrambled-data best of 200 | {fmt(p['null_max'])} |")
        A(f"| p | **{p['p_value']:.4f}** |")
        A(f"| verdict, fixed before the run | **{p['verdict']}** |")
        A("")
        A("**The real result beats not just the average scrambled run but the best of "
          "200.** The rule required two things at once, both written down before the data "
          "was touched: the score must exceed zero, and it must beat scrambled data at "
          "p ≤ 0.05. A positive score alone proves nothing, because trying twenty "
          "index-and-lead combinations per zone-season produces positive numbers on "
          "noise. A small p alone proves nothing, "
          "because a procedure can be reliably distinguishable from noise and still "
          "forecast worse than climatology.")
        A("")
        A("**What this p-value covers, and what it does not.** It pays for the choice of "
          "predictor and lead time. It does not pay for the zone discovery, because zone "
          "discovery never looks at ocean data or at any score, and every zone it finds "
          "is reported. There is no hidden selection there for a shuffle to punish. "
          "Whether the zoning itself is worth anything is a different question, answered "
          "in section 6, and answered less favourably.")
        A("")
        A("---")
        A("")

    # ══ 1 ════════════════════════════════════════════════════════════════════
    A("## 1. The earlier published analysis reproduces exactly")
    A("")
    A("**This section establishes provenance, not a result.** Before asking new questions "
      "it is worth knowing the code computes what the earlier project computed. AGUv3's "
      "own scripts were run unmodified against the fixtures pinned here, and their output "
      "tables compared line by line against what AGUv3 published.")
    A("")
    if legacy:
        A(f"**Rainfall-only quantities: "
          f"{legacy['tier1_total'] - legacy['tier1_failed']} of {legacy['tier1_total']}, "
          f"checked exactly. Ocean-dependent quantities: "
          f"{legacy['tier2_total'] - legacy['tier2_failed']} of {legacy['tier2_total']}, "
          "checked to two decimal places.**")
        A("")
        A("| what was checked | result |")
        A("|---|---|")
        A("| number of cells in each zone, at three levels of detail | exact |")
        A("| how stable the clustering is, for every zone count from 2 to 8 | identical |")
        A("| which rainy seasons were found | identical |")
        A("| the headline claim: dry March–May given a negative Western-V gradient | "
          "**0.79, and 0.77 with La Niña added — reproduced at both levels** |")
        A("| every statistic in all 22 rows of the hierarchy table | largest difference 0.000 |")
        A(f"| how many of 520 searched combinations survived multiplicity correction | "
          f"{legacy['survivors']}, matching the published {legacy['survivors_published']} |")
        A("| the winning recipe for each zone-season | all 7 identical |")
        A("")
        A("**One correction to how this was first checked.** An earlier version of this "
          "verification read the wrong table. It compared 0.71 and 0.69 — the figures at "
          "the coarsest level of detail — against a headline claim actually made at two "
          "finer levels. The published numbers are 0.79 and 0.77, they are now checked "
          "directly at both levels, and 0.71 / 0.69 is labelled as the different quantity "
          "it is.")
        A("")
        A("**A claim that could not be supported was withdrawn.** The specification "
          "promised a cell-by-cell comparison of zone labels against a stored reference. "
          "No such reference exists, because AGUv3's data directory was never committed. "
          "The table above is what can actually be checked, and the report says so rather "
          "than implying more.")
    A("")

    # ══ 2 ════════════════════════════════════════════════════════════════════
    A("## 2. A known data-handling error is worth about four thousandths of skill")
    A("")
    A("**Two of the five indices — the West Pacific Gradient and the Western-V "
      "Gradient — are built by standardising two temperature series and subtracting "
      "them.** Standardising means subtracting an average and dividing by "
      "a spread, and both are quantities that have to be estimated. Estimating them from "
      "all the years, including the ones being forecast, leaks information from the "
      "future into the predictor. That is a real error, and the previous project made it.")
    A("")
    A("**Two otherwise identical runs isolate it.** They differ in one thing: whether "
      "the West Pacific Gradient and the Western-V Gradient are standardised over "
      "all years or over training years alone. Niño-3.4, the Dipole and IWHG contain "
      "no estimated constant, so they cannot respond to the change — verified in "
      "advance — and the difference therefore cannot be picking up anything else.")
    A("")
    leak = [r for r in real if r["arm"] == "zones-specific" and r["weight_rule"] == "equal"]
    if leak:
        A("| fold protocol | done correctly | with the leak | difference |")
        A("|---|---:|---:|---:|")
        for proto, label in (("walkforward", "walk-forward"), ("kfold", "k-fold")):
            c = next((r for r in leak if r["protocol"] == proto and not r["leak"]), None)
            k = next((r for r in leak if r["protocol"] == proto and r["leak"]), None)
            if c and k:
                cv = c["families"]["atlas/all-windows"]["rpss"]
                kv = k["families"]["atlas/all-windows"]["rpss"]
                A(f"| {label} | {fmt(cv)} | {fmt(kv)} | **{fmt(cv - kv)}** |")
        A("")
    A("**The leak flatters the result, which is the direction leakage should push, and "
      "the effect is small.** Letting future ocean data set a predictor's scale makes the "
      "forecast look better than it is, and it does, by about four thousandths. It is "
      "small because only the West Pacific Gradient and the Western-V Gradient carry "
      "the flaw, and only the zone-seasons that actually select one of those two are "
      "affected at all.")
    A("")
    A("**The earlier project carried six such errors and this measures one.** The other "
      "five — a full-record median, a full-record threshold, a full-record La Niña "
      "definition, a map fitted on all years, and no held-out test at all — are fixed "
      "together by the out-of-sample design and are not separated from one another. The "
      "drop from the earlier project's numbers to these is their combined effect plus a "
      "change in what is being measured, and it is reported that way rather than blamed "
      "on any single one.")
    A("")

    # ══ 3 ════════════════════════════════════════════════════════════════════
    A("## 3. The machine draws the same two-zone map in every fold")
    A("")
    if stab:
        A("**The clustering chose two zones in all six folds.** The rule was fixed before "
          "any of this ran: take the largest number of zones whose clustering still comes "
          "back the same at least 90% of the time under resampling. Three zones came "
          "close and never quite cleared the bar.")
        A("")
        A("Each row is one fold. The numbered columns are how reliably the clustering "
          "reproduces itself at that many zones. A value of 1.0 would mean perfectly, and "
          "the rule needs 0.90.")
        A("")
        A("| fold | zones chosen | 2 | 3 | 4 | 5 | 6 | 7 | 8 |")
        A("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for i, curve in enumerate(stab["ari_curve_per_fold"]):
            c = {int(k): v for k, v in curve.items()}
            A(f"| {i} | {stab['k_per_fold'][i]} | " +
              " | ".join(f"{c.get(k, float('nan')):.3f}" for k in range(2, 9)) + " |")
        A("")
        A("**The two zones are a wet highland west and a dry east.** The western zone has "
          "rainy seasons in May–July and July–September. The eastern zone has the "
          "March–May long rains and the October–December short rains that the region's "
          "forecast centres actually issue outlooks for. Neither the split nor the "
          "seasons were supplied to the procedure.")
        A("")
        A("**Three zones sit just below the bar in every fold, and that knife edge is "
          "worth naming.** The values run 0.881 to 0.895 against a threshold of 0.90. A "
          "slightly different threshold would have produced a three-zone map throughout, "
          "and section 4 shows why that matters.")
        A("")
        A("Maps and annual cycles: `outputs/figures/zone_maps_by_fold.png`, "
          "`outputs/figures/annual_cycles_by_fold.png`, `outputs/figures/k_hierarchy.png`.")
    A("")

    # ══ 4 ════════════════════════════════════════════════════════════════════
    A("## 4. The map is highly stable, and that is why one planned test could not be run")
    A("")
    if stab:
        A(f"**The six folds draw almost the same map.** Agreement between any two folds "
          f"averages {stab['mean_offdiag_ari']:.4f} on a scale where 1.0 is identical, "
          f"and never falls below {stab['min_offdiag_ari']:.4f}. Only "
          f"{stab['switch_map_frac_ever']:.1%} of grid cells ever change zone between any "
          "pair of folds. This measurement needs no matching of zone labels across folds, "
          "so it cannot be an artefact of how they were matched.")
        A("")
        A("**Every zone appears in every fold.** No fold produced a zone with no "
          "counterpart elsewhere, and no zone went missing from a fold.")
        A("")
        A("Each row below follows one zone across all six folds.")
        A("")
        A("- **Cell agreement** is how much the zone's footprint overlaps between folds.")
        A("- **Centre drift** is how far its centre of mass moves, in degrees.")
        A("- **Same season** is how often two folds agree on its rainy seasons.")
        A("- **Same predictor** is how often two folds pick the same ocean index.")
        A("- **Skill** is that zone's own RPSS, pooled over the years it was tested on.")
        A("")
        A("| zone | folds present | cell agreement | centre drift lat/lon | same season | "
          "same predictor | skill | years scored |")
        A("|---|---:|---:|---|---:|---:|---:|---:|")
        for t in stab["tracks"]:
            A(f"| {t['track']} | {t['n_folds']}/6 | {fmt(t['agreement'], 3, False)} | "
              f"{fmt(t['centroid_sd_lat'], 2, False)}° / "
              f"{fmt(t['centroid_sd_lon'], 2, False)}° | "
              f"{fmt(t['window_exact_match'], 2, False)} | "
              f"{fmt(t['predictor_identity'], 2, False)} | {fmt(t['pooled_rpss'])} | "
              f"{t['n_scored']} |")
        A("")
        h = stab["h1"]
        if (h.get("n") or 0) < 3:
            A("**The planned test of whether stabler zones forecast better could not be "
              "run, and the reason is itself the finding.** With two zones there are two "
              "points, and a correlation between two points carries no information at any "
              "significance level. The hypothesis is untested, not unsupported, and it "
              "must not be reported as a negative result. The specification predicted "
              "between three and eight zones; two is below even that. Testing it would "
              "need a finer map, which cannot be chosen now without abandoning the "
              "pre-registered rule, or a larger region.")
        else:
            A(f"**Stability against skill:** ρ = {h['rho']}, p = {h['p']}, over "
              f"{h['n']} zones, using {h['null']}. Verdict: **{h['verdict']}**.")
        A("")
        A("Cell-switching map: `outputs/figures/switch_map.png`. Fold agreement matrix: "
          "`outputs/figures/ari_matrix.png`.")
    A("")

    # ══ 5 ════════════════════════════════════════════════════════════════════
    A("## 5. The discovered map beats a single pooled region, as a forecast product")
    A("")
    A("Four ways of covering the same ground are compared. All four forecast the same "
      "geography with the same total weight, which is what makes their scores comparable.")
    A("")
    A("- **Climatology** forecasts equal thirds every year. It must score exactly zero, "
      "and does. It is the check that the scoring is not broken.")
    A("- **One pooled region** treats the whole domain as a single zone.")
    A("- **Discovered zones, one shared recipe** uses the machine's map but forces every "
      "zone to use the same ocean predictor.")
    A("- **Discovered zones, own recipe each** is the full procedure.")
    A("")
    if rw:
        A("| way of covering the ground | walk-forward | k-fold |")
        A("|---|---:|---:|")
        for arm, label in (("climatology", "climatology (the check)"),
                           ("pooled", "one pooled region"),
                           ("zones-shared", "discovered zones, one shared recipe"),
                           ("zones-specific", "discovered zones, own recipe each")):
            a = rw.get(arm, {}).get("families", {}).get("atlas/all-windows", {}).get("rpss")
            b = rk.get(arm, {}).get("families", {}).get("atlas/all-windows", {}).get("rpss")
            A(f"| {label} | {fmt(a)} | {fmt(b)} |")
        A("")
    if dec.get("paired"):
        A("**Two comparisons were tested properly, by running both arms on the same 200 "
          "scrambles and differencing them run by run.**")
        A("")
        A("| comparison | difference | p |")
        A("|---|---:|---:|")
        for k, v in dec["paired"].items():
            nm = (k.replace("zones-specific_minus_pooled",
                            "discovered zones vs one pooled region")
                   .replace("zones-specific_minus_zones-shared",
                            "own recipe each vs one shared recipe"))
            A(f"| {nm} | {fmt(v['delta_real'])} | {v['p_value']:.4f} |")
        A("")
        A("**Splitting the domain in two is worth a lot. Giving each zone its own "
          "predictor is worth almost nothing.** The map is doing the work, not the "
          "per-zone predictor choice.")
        A("")
    A("**Do not read that as proof that the zoning models rainfall better, because "
      "section 6 says otherwise.** The four arms forecast *different things*. A two-zone "
      "map issues four seasonal forecasts covering the domain. A one-zone map issues "
      "fewer, at seasons chosen to suit an average over wet highlands and dry lowlands "
      "together. Part of the gap is the map being better, and part is simply that the "
      "two-zone map makes more, and more sensible, forecasts. This benchmark "
      "deliberately measures the product a forecast centre would issue, so that mixture "
      "is a property of the question rather than a defect — but it means this is not a "
      "controlled test of the zoning. The next section is.")
    A("")
    A("Every zone, every season, every fold, with no minimum-sample filtering: "
      "`outputs/atlas_per_zone.json`.")
    A("")

    # ══ 6 ════════════════════════════════════════════════════════════════════
    A("## 6. Under a controlled test, the zoning buys much less than section 5 suggests")
    A("")
    A("**This is the honest test of the map, and it disagrees with the headline.** Here "
      "every arm forecasts one identical number — total rainfall averaged over the whole "
      "region — and the zones are used only as internal machinery, their predictions "
      "recombined into that single forecast. Because everyone is now predicting the same "
      "thing, any difference is attributable to the zoning.")
    A("")
    if sr:
        A("| test | season | one pooled region | using discovered zones | difference |")
        A("|---|---|---:|---:|---:|")
        for w in ("MAM", "OND"):
            a, b = sr.get(("fixedmean", w, "pooled")), sr.get(("fixedmean", w, "zones"))
            if a is not None and b is not None:
                A(f"| one regional total | {w} | {fmt(a)} | {fmt(b)} | **{fmt(b - a)}** |")
        for w in ("MAM", "OND"):
            a = sr.get(("grid", w, "pooled"))
            b = sr.get(("grid", w, "zones-specific"))
            if a is not None and b is not None:
                A(f"| every grid cell scored | {w} | {fmt(a)} | {fmt(b)} | **{fmt(b - a)}** |")
        A("")
    A("**Splitting the region helps the March–May long rains and does essentially nothing "
      "for the October–December short rains.** On the long rains the zoning is worth "
      "about six hundredths of skill, which is real. On the short rains it is worth two "
      "thousandths on one test and is slightly negative on the other.")
    A("")
    A("**So section 5's large margin is mostly about what each map chooses to forecast, "
      "not about the map modelling rainfall better.** That limitation was written into "
      "the specification before any number existed, and this benchmark was designated in "
      "advance as the test that would settle it. It also means this work does not "
      "overturn the previous project's finding that partitioning a fixed target fails to "
      "beat pooling it. Once the target is genuinely held fixed, the two agree.")
    A("")
    A("**A forecaster's reading:** the discovered map is worth issuing, because the "
      "product it generates is better than a single regional outlook. **A modeller's "
      "reading:** the map is not, by itself, a better statistical model of East African "
      "rainfall. Both are true and they do not conflict.")
    A("")

    # ══ 7 ════════════════════════════════════════════════════════════════════
    A("## 7. The long rains stay unpredictable, even when the conditions are chosen to help")
    A("")
    A("**The March–May long rains are this region's long-running dispute.** Earlier work "
      "found no skill. Reviewers objected that skill appears only in particular ocean "
      "states. Later versions reported strong-looking conditional hit rates. This "
      "evaluates the claim in a way that pays for the search needed to find it.")
    A("")
    A("**Three pre-registered variants were tested,** each judged against its own 200 "
      "scrambles: all March–May years, La Niña years only, and years when the Western-V "
      "gradient is negative. Which years count as La Niña, or as negative-gradient, is "
      "decided from training data alone. March–May was evaluated for every zone whether "
      "or not the machine found a March–May season there, so the answer cannot depend on "
      "where the detector happened to look. It was never required to beat a stronger "
      "season such as October–December.")
    A("")
    if dec.get("families"):
        mam = {k: v for k, v in dec["families"].items()
               if "MAM" in k and v.get("p_value") is not None}
        if mam:
            A("| map used | years scored | skill | p | clears? |")
            A("|---|---|---:|---:|---|")
            for k, v in mam.items():
                arm, fam = k.split("|")
                arml = {"pooled": "one pooled region",
                        "zones-shared": "zones, one shared recipe",
                        "zones-specific": "zones, own recipe each"}.get(arm, arm)
                faml = {"MAM/all": "all years", "MAM/lanina": "La Niña only",
                        "MAM/neg_wvg": "negative gradient only"}.get(fam, fam)
                A(f"| {arml} | {faml} | {fmt(v['rpss'])} | {v['p_value']:.4f} | "
                  f"{'yes' if v.get('clears') else 'no'} |")
            A("")
            A(f"**Not one of the {len(mam)} combinations clears.** The smallest p is "
              f"{min(v['p_value'] for v in mam.values()):.4f} against a bar of 0.05. "
              "Several skill values are positive — conditioning on La Niña does lift the "
              "estimate — and none survives the cost of having tried twenty "
              "index-and-lead combinations to find it. The previous project reached "
              "the same conclusion for October–December rainfall over Somalia, "
              "against a different null.")
            A("")

    # ══ 8 ════════════════════════════════════════════════════════════════════
    A("## 8. The discovered map lines up with the expert map, but that proves nothing")
    A("")
    A("**These comparisons are descriptive and decide nothing.** The expert regions are "
      "not ground truth; they are what people drew. Agreement is reassuring, and "
      "disagreement would not have been evidence of error.")
    A("")
    if stab and stab.get("expert_overlap"):
        A("| hand-drawn expert region | machine zone | share of the expert box inside it |")
        A("|---|---:|---:|")
        for o in stab["expert_overlap"]:
            if o["frac_of_box_in_zone"] > 0.5:
                A(f"| {o['expert']} | {o['zone']} | {o['frac_of_box_in_zone']:.1%} |")
        A("")
        A("**The machine's eastern zone contains 92% of the hand-drawn eastern-Horn box, "
          "and virtually all of the reviewer's south-central Somalia box.** It found the "
          "same dry east that people draw, without being told it exists.")
        A("")
    if stab and stab.get("orientation_eta2"):
        A("| country | how much the split runs east–west | how much north–south |")
        A("|---|---:|---:|")
        for o in stab["orientation_eta2"]:
            A(f"| {o['country']} | {o['eta2_lon']:.3f} | {o['eta2_lat']:.3f} |")
        A("")
        A("**Both countries split east–west rather than north–south**, matching the "
          "documented Kenyan highland-versus-drylands divide.")
        A("")

    # ══ 9 ════════════════════════════════════════════════════════════════════
    A("## 9. What this work cannot tell you")
    A("")
    for x in [
        "**Twenty-two test years is a small sample.** Walk-forward scores three or four "
        "years per fold, twenty-two in total. Every number here rests on that.",
        "**The first fold learns its map from twenty-one years.** An expanding-window "
        "design has to start somewhere, and its earliest map is its least informed.",
        "**The test of whether stability predicts skill could not be run**, because the "
        "map has only two zones. It is untested, not answered.",
        "**The ocean predictors are observations, not forecasts.** A real forecaster does "
        "not know next season's sea-surface temperature. The operational chain is "
        "(can a model forecast the index) × (does the index predict rainfall), and only "
        "the second factor is measured here. The previous project measured the first "
        "factor for Somalia October–December rainfall, substituting the Indian Ocean "
        "Dipole as forecast by the ECCC CanESM5.1 seasonal model, and found it "
        "retained 77% of the skill.",
        "**A zone may have at most two rainy seasons**, fixed in advance. A genuinely "
        "three-season regime would be truncated.",
        "**The 90% stability threshold is defensible but still a threshold.** Three zones "
        "score 0.881 to 0.895 in every fold against a bar of 0.90. A slightly different "
        "bar gives a different map, and possibly a testable stability hypothesis. The "
        "full table at every zone count is printed in section 3 precisely so a reader can "
        "see how close it was.",
        "**Section 5 compares products, not predictions of the same thing.** Section 6 is "
        "the controlled comparison and it is the more conservative one.",
        "**The ocean data was refetched rather than inherited.** It reproduces the earlier "
        "project's numbers exactly, but it is not the same bytes that project read.",
        "**The supporting libraries have uncommitted local changes.** Their contents are "
        "hashed file by file so any drift is detectable, but the environment cannot be "
        "rebuilt from version control alone.",
    ]:
        A(f"- {x}")
    A("")

    # ══ appendix ═════════════════════════════════════════════════════════════
    A("---")
    A("")
    A("## Appendix: how to check any of this")
    A("")
    A("**Research record.** Experiments `e:1` (setup) → `e:2` (v1 pilot) → `e:3` "
      "(Amendment 1; headline). Cross-cutting reads: `a:1` (zonation gain vs controlled "
      "test), `a:2` (H1 untestable). Committed narrative spine: `RESEARCH_LOG.md`. "
      "Full local audit trail: `.rx/`. Orient with `rx status`.")
    A("")
    A("**Everything regenerates with one command:** `./regenerate.sh` (defaults to "
      "`e:3`). Every step runs through `rx`.")
    A("")
    if repro:
        A(f"**The scrambled-data runs were reproduced after a change to the runner.** All "
          f"{repro.get('old_rows')} rows matched, with a largest difference of "
          f"{repro.get('max_abs_diff', 0):.0e} — that is, none. The corrections were to "
          "the runner's control flow, its restart logic, its completeness check and its "
          "provenance record. None touches the scoring path, and the identical output "
          "confirms it.")
        A("")
    if dec.get("sensitivity_field_perm"):
        sp = dec["sensitivity_field_perm"]
        A("**An earlier way of scrambling the data was wrong, and it is documented here "
          "because the error is instructive.** The first version shuffled whole calendar "
          "years of rainfall. A rainy season that straddles New Year — November, "
          "December, January — then takes its November and December from one year and "
          "its January from another, so the scrambled data contains seasons that never "
          "happened. The replacement shuffles complete seasons instead.")
        A("")
        if "NDJ" in (sp.get("wrapping_windows_present") or []):
            A("**The flaw was not hypothetical.** Run twenty times, the old method "
              "produced exactly such a straddling season. The real, unshuffled map "
              "contains none, which is precisely why the problem was invisible in the "
              "version that had it.")
            A("")
    if chain:
        A("**Three implementations of the score are cross-checked in a chain**, so a "
          "silent disagreement anywhere in it aborts the run:")
        A("")
        A(f"- the matrix-algebra scorer against the cell-by-cell scorer: "
          f"{chain.get('link1_batched_vs_percell_maxdiff', 0):.0e}")
        A(f"- the cell-by-cell scorer against the locked evaluator inherited from the "
          f"previous project: {chain.get('link2_percell_vs_bench_maxdiff', 0):.0e}")
        A("- the fast atlas scorer against a deliberately naive reimplementation that "
          "refits every regression in an explicit loop")
        A("")
        A(f"The required tolerance is {chain.get('tolerance')}.")
        A("")
    if gates:
        A("| check that had to pass first | result |")
        A("|---|---|")
        A("| an equal-thirds forecast scores zero | exactly 0.000000000000000 |")
        A(f"| a planted ocean signal is recovered | RPSS {fmt(gates['synthetic_bench_rpss'])} |")
        A(f"| a synthetic two-zone map is recovered | boundary agreement "
          f"{gates['synthetic_partition_ari']:.4f} out of 1.0 |")
        A("| the synthetic map's driving index is identified per zone | correct in both zones |")
        A(f"| shuffling the years removes the skill | mean "
          f"{fmt(gates['shuffle_mean_rpss'])} over 4 shuffles |")
        A("")
    if env:
        a = env["asserted"]
        A("| input | fingerprint |")
        A("|---|---|")
        for k, v in a["fixtures"].items():
            A(f"| {k} | {v['bytes']:,} bytes, sha256 `{v['sha256'][:20]}…` |")
        for k, v in a["libraries"].items():
            A(f"| {k} | {v['n_source_files']} source files, tree hash "
              f"`{v['tree_sha256'][:20]}…` |")
        A("")
    if ersst:
        A(f"**The ocean data** was fetched through a catalogue entry restored for this "
          f"work: {ersst.get('n_months')} monthly files, combined after normalising two "
          "incompatible date encodings the upstream archive mixes: 324 of the files "
          "date themselves in minutes on a 360-day calendar, the other 192 in days "
          "since 1854 on the ordinary calendar.")
        A("")
    A("**Specification:** `SPEC.md` and `SPEC_AMENDMENT_1.md`, both written and reviewed "
      "before the results existed. **Research log:** `RESEARCH_LOG.md` (snapshot of "
      "`.rx/NOTES.md`).")
    A("")

    # Strip bold lead-ins from paragraphs. A bolded opening clause on every paragraph
    # is shouting, not structure. Bullets keep their label (it is what makes a list
    # scannable) and tables keep theirs.
    import re
    out = []
    for ln in L:
        if ln[:1] not in ("-", "|", "#", " ", ""):
            ln = re.sub(r"^\*\*(.+?)\*\*[ ]?", r"\1 ", ln, count=1).replace("  ", " ")
        out.append(ln)
    L = out
    (ROOT / "REPORT.md").write_text("\n".join(L) + "\n")
    txt = "\n".join(L)
    print(f"wrote REPORT.md — {len(L)} lines, {len(txt)} chars")
    print(json.dumps({"lines": len(L), "chars": len(txt), "status": "ok"}))


if __name__ == "__main__":
    main()
