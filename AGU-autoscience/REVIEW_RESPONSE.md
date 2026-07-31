# Response to the review of the AGU abstract (East African long-rains predictability)

*Draft reply. On the substance the review is correct; this is a point-by-point acknowledgement, with
the relevant literature and a re-audit of our own pipeline. Citations flagged for verification at the
end.*

Thank you — this is exactly the review the work needed. Before replying I re-audited our pipeline and
pulled the literature, including your group's. The short version: **the abstract's claim that the MAM
long rains have "little seasonal-scale predictability" is an artifact of two methodological choices in
our automated search, not a property of the climate, and we will not stand behind it as written.**

## 1. "I disagree that the East African long rains have little seasonal-scale predictability."

Conceded. We conflated two statements that must be kept apart:

- A weak *direct, symmetric* MAM–ENSO teleconnection is real and well documented — Nicholson (2017,
  *Rev. Geophys.*) notes the net seasonal El Niño signal in MAM is near-zero because sub-seasonal
  anomalies flip sign within the season; Palmer/Wainwright et al. (2023, *Nat. Rev. Earth Environ.*)
  report the long rains have "little association with ENSO." Our search finding weak *symmetric*
  SST-index skill is consistent with that literature.
- That is not "unpredictable." The operationally decisive signal is the **asymmetric, dry-tail,
  La-Niña-conditioned** predictability captured by the West-Pacific / Western-V gradient — which your
  own work established quantitatively: **Funk et al. (2014, *HESS* 18:4965–4978)** reports
  cross-validated MAM skill of **r ≈ 0.6** from the WPG + Central Indian Ocean indices, *substantially
  outperforming the coupled dynamical models*, and **Funk et al. (2023, *Earth's Future*,
  10.1029/2022EF003454)** formalizes the "frequent but predictable" dry-season mechanism via
  Walker-circulation intensification.

Writing "little seasonal-scale predictability" without that distinction erases the exact signal that
matters. That was our error.

## 2. "I'm not surprised an automated search misses the (admittedly weak) predictability."

Conceded, and I can say *why*, confirmed directly in our code and results:

1. **Spatial aggregation over non-homogeneous regimes** (points 3, 6, 7).
2. **Symmetric skill evaluation over all years**, which dilutes an asymmetric dry-tail signal.

Our search scored every configuration with leave-one-year-out GROC/RPSS/correlation pooled over the
whole domain and all years. It never conditioned on ENSO phase or evaluated the dry tercile
separately, so the WVG's skill — concentrated in the dry, La-Niña seasons — averages out. This is a
genuine limitation of naive "autoscience": optimizing a symmetric, whole-domain metric will
systematically miss asymmetric, regionally-localized predictability. We think that is worth reporting
*as a finding*, not mislabeling as the climate having no signal.

A third pass isolated the two factors quantitatively, and the result sharpens your point. With the
regionalization *discovered from the data* (below) and an unconditional dry-tail metric (below-median
ROC) added to the search, the MAM signal **still fails family-wide multiplicity control** (520
configurations, permutation null, Benjamini–Hochberg) — it becomes detectable only under
La-Niña-conditional evaluation, where it returns at the ~0.8 level. Most years the WVG has nothing to
say about MAM, and a metric that scores every year equally penalizes the forecast for the years it
correctly stays silent. So the decisive missing ingredient was not the domain, nor even the tail
focus, but the conditional framing itself — the way your group actually poses the question.

## 3. "If you lump all of Kenya you'll miss it — limit to central and southern Somalia."

Correct, and confirmed in our configuration:

- **Kenya box: 5°S–5°N, 34–42°E** — includes **western Kenya / the Lake Victoria basin (34–38°E)**, a
  wetter, convectively- and topographically-driven regime off the Walker subsidence branch, treated in
  the literature as a separate, less-predictable regime.
- **Somalia box: 2°S–12°N, 41–51°E** — runs up into **northern Somalia**. (It is why our automated
  season detector returned an SON window rather than the operational OND/Deyr — a symptom of exactly
  the regime-mixing you flag.)

The fix is to restrict to the eastern-Horn domain your forecast papers use — roughly **east and south
of ~38°E, ~8°N** (southern Ethiopia, eastern Kenya, central-southern Somalia), on the **descending
branch of the Indian Ocean Walker cell** (Funk et al. 2014; Hoell & Funk 2013, *J. Climate*
26:9545–9562). We are re-running on that domain (below).

(One nuance from the re-analysis, flagged as a question rather than a correction: within Somalia the
rainfall structure is more coherent than we expected — north–south monthly anomalies correlate at
r ≈ 0.7, our data-driven zonation keeps most of Somalia in a single regime with only the northern
Golis-highland strip separating, and the MAM dry-tail statistics come out identical for the full
eastern-Horn domain and the south-central-Somalia box (0.79 / 0.77 both). Western Kenya is clearly
the destructive inclusion; the everything-north-of-~8°N exclusion may be conservative relative to
the rainfall structure itself, at least for seasonal-total purposes. We would value your read.)

## 4. "The predictability is asymmetric — only dry MAM within/following La Niña, predicted well by the WVG."

Conceded, and this is the crux. Our own WVG MAM result came out at **GROC ≈ 0.52 (r ≈ 0.06–0.11)** —
near no-skill — *because* we evaluated it symmetrically over all years and the whole domain. That
number is an artifact. The record is the opposite:

- The WVG lineage (Hoell & Funk 2013 WPG → the "Western V" gradient) and the **~75% probability of a
  below-normal MAM following post-1997 La Niña vs. a ~46% baseline** (CHC blog p=1240).
- A **verified operational example**: the 18 March 2022 post ("Why tailored forecasts work so well for
  the eastern Horn of Africa March–May rainy season," p=1100) forecast a "very likely" negative-WVG,
  below-normal **MAM 2022** *before the season*, highest dry probability **over southern Somalia and SE
  Ethiopia** — and MAM 2022 verified as the driest in ~70 years (ICPAC/FEWS NET/FAO/WFP Joint
  Statement, 9 June 2022).

For what it's worth, our own synthesis of your blog corpus already recorded the asymmetry ("MAM …
dry seasons predictable, wet seasons not; WVG R²≈0.93 but only for the dry tail"); the automated search
simply didn't act on the domain knowledge we'd assembled.

## 5. The real-world stakes and the OND-2027 / MAM-2028 scenario

Taken seriously — and the current ENSO state makes it more pressing than a base-rate contingency. As
of mid-July 2026 a strong, intensifying El Niño is under way (weekly Niño-3.4 ≈ +2.1 °C; a NOAA
El Niño Advisory is in effect), and the model consensus forecasts a *very strong* peak in OND 2026
(23 of 26 models ≥ +2.0 °C), persisting at ~100% probability through early 2027. Following the
three-tier framing your group uses (June-2020 CHC post, p=757):

- **(i) effectively certain** that no-regrets anticipatory action is warranted on the base rates alone;
- **(ii) conditional but probable** that *if* pre-season SSTs resemble the dry analogs, back-to-back
  OND-2027 and MAM-2028 failures become likely — the WVG "loads the dice" to ~70–90% for the dry tail,
  not to certainty (documented counter-years exist: 1985, 1989, 2006, 2018);
- **(iii) the enabling condition — a following La Niña — is now within the skillful window, not a
  distant hope.** All five "super" El Niños (peak ONI ≥ 2.0) since 1972, and five of the eight strong
  events since 1950, were followed by La Niña via post-El-Niño heat-content discharge (Jin recharge
  oscillator). Critically, Lenssen et al. (2024, *GRL* 10.1029/2023GL106988) show ENSO is skillfully
  predictable 1.5–2 years ahead *precisely when a strong El Niño is currently ongoing* — the skill
  comes almost entirely from anticipating the following La Niña — and **that condition now holds**. So
  a La Niña developing in the second half of 2027, once the 2026–27 event discharges, is a physically
  supported outlook rather than a base-rate guess (with the honest caveats: small analog n, and the
  spring barrier still bounds the transition timing). That places OND-2027 and MAM-2028 in a genuine,
  currently-anticipable action window.

The point stands regardless: a published "MAM is unpredictable" statement could undercut exactly the
dry-tail, anticipatory-action value your WVG forecasts provide — and with a very strong El Niño now in
progress, that value is about to be in demand. That is the last thing we want to do, and it is the
core reason we are correcting the abstract.

## 6–7. "A lot went into picking Eastern East Africa"; "includes western Kenya; conflates regimes."

Both correct, and confirmed — with one encouraging addendum from the third pass. Conflating regimes
and pooling the metric across them is what produced the misleadingly low skill; that stands. But when
we made regionalization a *discovery step* — clustering grid cells on seasonal-cycle shape plus
interannual co-variability, with the cluster count set by bootstrap stability — the first and most
stable partition of the two-country field is essentially your EEA boundary: the bimodal eastern
drylands separate from the highland regimes, western Kenya splits out along a diagonal that crosses
~38°E in the north and lies east of it in the south (closer to your "east and south of ~38°E, ~8°N"
corner than to a straight meridian), and each zone's rainy-season calendar (Gu/Deyr east,
Belg/Kiremt in the highlands) falls out of the data. So the domain knowledge in "a lot went into
picking Eastern East Africa" appears to be *recoverable* from rainfall structure — which credits the
choice rather than diminishing it: the physically-motivated domain is what the data themselves
select. What was **not** recoverable by search was the conditional evaluation framing (point 2
above). That, not the geography, is where your group's expertise proved irreplaceable to the
automated pipeline.

---

## What we found on re-analysis

We re-ran with both corrections — the homogeneous eastern-Horn domain (38–50.5°E, 4.5°S–8.5°N) and
south-central Somalia (42–48°E, 1–6°N), evaluated asymmetrically — on CHIRPS v3 + ERSSTv5, 1981–2023
(n = 43). The result recovers your operational signal:

- The **symmetric all-years WVG→MAM correlation is −0.21** (no linear skill — reproducing the naive
  search's artifact, because the relationship is one-sided and a linear fit over all years captures
  nothing);
- but **P(below-median MAM | strong-negative WVG) ≈ 0.79**, and **≈ 0.77 when the strong-negative WVG
  coincides with La Niña** (13 such years), against a ~0.5 base rate — matching the negative-WVG
  analog statistics your group reports (~75–80% of negative-WVG analog years below-normal). The
  strong-negative-WVG La-Niña years cluster in the dry tail; the wet side carries no clean signal.

So the corrected reading is not "MAM is unpredictable" but its opposite: **the MAM long rains are
asymmetrically predictable for exactly the dry, La-Niña seasons that matter operationally**, and the
naive search missed it only because it pooled over a heterogeneous domain and scored a one-sided
signal with a symmetric, all-years metric.

A third pass then rebuilt the search with those corrections as axes rather than fixes. Zones are
discovered by clustering (they recover your EEA boundary, as above); each zone's season windows are
detected from its own harmonics; and a 520-configuration search over zone × window × five SST
indices (Niño-3.4, IOD, WPG, WVG, IWHG) × lead (0–3 months) × evaluation mode runs under a single
permutation null with Benjamini–Hochberg control. The 79 surviving configurations reproduce the
operational recipe zone by zone — the IOD for the equatorial OND short rains (r ≈ 0.6, holding to
two months of lead), ENSO/IWHG for the Deyr (dry-tail ROC ≈ 0.8, holding to three months), and the
sign-reversed Pacific-gradient teleconnection for the highland Kiremt — none of which was supplied
to the search. The one thing that does *not* survive is MAM, under any unconditional metric; it
returns only under La-Niña-conditional evaluation. We can now state your "I'm not surprised an
automated search misses it" as a measured result: the geography and the predictor set are
discoverable, and the conditional way your forecasts pose the question is the part that is not.

We think the honest, general finding — that automated forecast-design search can recover the
regionalization and the teleconnections, but will discard the asymmetric signal unless conditional,
tail-focused evaluation is built into the searched space — is a stronger and truer thesis, and one
that credits rather than contradicts your group's work.

(Caveats on those numbers: our WVG is an approximation of your operational index, this is a
perfect-prognosis predictor rather than a forecast of the WVG, and the conditional samples are small
— so read them as consistent-with-operational, not as a reproduction of your forecast skill, which is
higher. Full method and figures are in the re-analysis we can share.)

Thank you for the generous close — I'll take you up on the call.

---

### Citations — verified vs. to-check
**Verified:** Funk et al. 2014 (*HESS* 18:4965–4978, 10.5194/hess-18-4965-2014); Funk et al. 2023
(*Earth's Future*, 10.1029/2022EF003454); Hoell & Funk 2013 (*J. Climate* 26:9545–9562,
10.1175/JCLI-D-12-00344.1); Lyon & DeWitt 2012 (*GRL*, 10.1029/2011GL050337); Liebmann et al. 2014/2017
(*J. Climate*); Nicholson 2017 (*Rev. Geophys.*, 10.1002/2016RG000544); Anderson/Funk et al. 2023
(*J. Hydrometeorology*, JHM-D-22-0043.1); Lenssen et al. 2024 (*GRL*, 10.1029/2023GL106988); NOAA
Climate.gov ENSO-transition statistics.
**To-check before sending:** the formal venue of the "Western V" 2017-drought attribution (likely the
*BAMS Explaining Extreme Events of 2017* report, 2019, not a standalone 2018 paper); the full author
list of the 2023 *Tailored Forecasts* paper (10.1029/2023EF003524).
