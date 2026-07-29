# CHC Regional Reference Wiki — Seasonal Rainfall Predictability & SST Teleconnections

**A consolidated synthesis of 30 UCSB Climate Hazards Center (CHC) blog posts (Oct 2016 – Jul 2026).**

## Purpose

This wiki reorganizes CHC's blog corpus **by region** to serve two concrete goals for our seasonal-forecasting research project:

1. **Region selection.** Identify the ONE country/region where CHC demonstrates the clearest, best-documented, most-studied SST-teleconnection predictability, so we can target our next automated forecast-design analysis pass there. (See [Implications for Region Selection](#implications-for-region-selection) at the end.)
2. **Cross-check reference.** Provide an attributed baseline of CHC's *published* understanding of which predictors, seasons, and skill levels matter where — so we can later compare our own automatically-discovered predictor/season/skill patterns against CHC's and flag agreement or divergence.

**Every substantive claim below is attributed inline to the specific post(s) it came from**, as Markdown links using each post's real `blog.chc.ucsb.edu` URL. Where posts converge, multiple citations are given; where they disagree or a claim is uncertain, that is noted explicitly.

## How to read / provenance

- **Source type.** These are **CHC blog posts** — operational, food-security-oriented analyses tightly linked to the **Famine Early Warning Systems Network (FEWS NET)**, USGS, NOAA, and national met services (Kenya Meteorological Department/KMSA, Ethiopian Meteorological Institute, Somalia SWALIM). They are written to support anticipatory humanitarian action, not as peer-reviewed papers, though they frequently cite the authors' own peer-reviewed work (Funk et al. 2018, 2023a "Frequent but Predictable Droughts…", 2023b "Tailored forecasts…", etc.).
- **Voice.** Most posts are lead-authored by **Chris Funk** (CHC Research Director) or Laura Harrison; the analytical framework is internally consistent across authors.
- **Date range.** Oct 19 2016 ([Kenya/Somalia Short Rains](https://blog.chc.ucsb.edu/?p=10)) → Jul 27 2026 ([Extended Early Estimates JJAS 2026](https://blog.chc.ucsb.edu/?p=2049)). Note several 2026 posts are dated in the near future relative to the corpus's scrape.
- **Geographic weighting.** The corpus is heavily **East Africa / eastern Horn**-centric (~20 of 30 posts). Southern Africa, Central America, South Asia/India, and Afghanistan appear in a handful of posts each. The Sahel / West Africa is essentially absent (see [Sahel / West Africa](#sahel--west-africa)).
- **Citations point to specific posts**, identified by a short title + the post's own URL. A full post index is at the [bottom](#appendix--post-index).
- **Data backbone.** Nearly all rainfall analysis uses **CHIRPS** (v2, now v3.0), temperature uses **CHIRTS-ERA5 Tmax**, SST uses **NOAA ERSSTv5**, forecasts come from the **NMME** and **ECMWF SEAS5/S2S** ensembles, and crop impacts use the **WRSI** model. See [Methods, data & tools](#cross-cutting-methods-data--tools).

---

# Cross-cutting: Climate Drivers

The posts share a common set of SST/atmospheric drivers across regions. This section consolidates each driver's CHC definition, the region/season it controls, its sign→outcome mapping, and the predictor indices CHC computes it from. **This is the most reusable part of the corpus for our purposes** — CHC's entire forecasting philosophy is "predict the driver index from NMME SST forecasts, then regress/analog the index onto regional rainfall."

## Driver → region → season → sign → outcome matrix

| Driver | Index / how computed | Primary region controlled | Season | Sign → rainfall outcome |
|---|---|---|---|---|
| **ENSO (El Niño / La Niña)** | Niño3.4 SST anomaly; increasingly **RONI** (Relative Oceanic Niño Index = Niño3.4 minus global tropical-mean SST) | Ethiopia (Kiremt); eastern Horn (OND); Southern Africa; global | JJAS / OND / DJF | **El Niño → DRY** Ethiopia Kiremt & Southern Africa DJF; **El Niño → WET** eastern Horn OND; **La Niña → DRY** eastern Horn OND & MAM |
| **Indian Ocean Dipole (IOD)** | WIO SST (50–70°E,10°S–10°N) − EIO SST (90–110°E,10°S–0) | Eastern Horn | OND ("short rains") | **Positive IOD → WET**; **negative IOD → DRY** |
| **West Pacific Gradient (WPG)** | Standardized [equatorial West Pacific SST] − [Niño3.4 SST] | Eastern Horn | OND (and lagged MAM) | **Strong negative WPG → DRY** (amplified Walker circulation) |
| **Western V Gradient (WVG)** | Standardized [Niño3.4 SST] − [Western V region SST]; WVG is the WPG extended to include the N. Pacific "V" | Eastern Horn | MAM ("long rains" / Gu) | **Strong negative WVG → DRY** |
| **Indo-Warm Pool Heating Gradient (IWHG)** | ERA5 atmospheric heating: [western IOD box 50–70°E] − [Indo-Pacific Warm Pool 90–150°E]. Estimated from SST as `b0 + b1·IOD + b2·WestPac + b3·Niño3.4` | Eastern Horn | OND | **Strong negative IWHG (< −100 Wm⁻²) → DRY**; **strong positive (> +200 Wm⁻²) → WET**. Symmetric — captures both extremes |
| **Western Indian Ocean (WIO) SST** | WIO box SST | Eastern Horn | OND / SOND | **Very warm WIO → WET/flood** (dominant wet driver, independent of El Niño) |
| **Subtropical Indian Ocean Dipole (SIOD)** | Western vs eastern subtropical S. Indian Ocean SST | Southern Africa | DJF/Feb | **Negative SIOD → DRY** (amplifies El Niño drought) |
| **Madden-Julian Oscillation (MJO)** | Sub-seasonal convective phase | East Africa | MAM / any | Active favorable phase → **WET** spells (e.g. MAM 2018); unpredictable > ~2–3 wk |
| **West Pacific Warming Mode / warming trend** | Long-term West Pacific SST rise | Eastern Horn / SW US | OND & MAM | Warming → **more frequent negative WPG/WVG → more DRY seasons** |
| **VPD / air temperature (Tmax)** | CHIRTS-ERA5 Tmax; Vapor Pressure Deficit | All (amplifier) | All | High Tmax/VPD → amplifies drought impact (desiccation), not a rainfall driver per se |

### Key convergence rule CHC uses everywhere
CHC's operational logic is a **"defense-in-depth / staged" convergence**: long-lead driver-index forecast → observations → weather forecasts → sub-seasonal outlooks. Confidence rises when independent lines (empirical analogs, dynamical NMME/ECMWF rainfall forecasts, and reanalysis circulation diagnostics) agree ([Pessimistic MAM 2025](https://blog.chc.ucsb.edu/?p=1566); [Converging Evidence OND 2024](https://blog.chc.ucsb.edu/?p=1464); [Ethiopia Very Poor 2026 Kiremt](https://blog.chc.ucsb.edu/?p=2013)).

---

## Driver detail

### ENSO — El Niño / La Niña
- **Definition (CHC usage).** Warm/cold phase of the tropical Pacific coupled ocean-atmosphere system, monitored via **Niño3.4** SST and, increasingly, **RONI** — recently adopted by several official agencies as the primary ENSO index because it removes the global tropical-mean warming signal ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982); [Ethiopia Very Poor 2026 Kiremt](https://blog.chc.ucsb.edu/?p=2013)). "Strong" El Niño = 3-month Niño3.4 > +1.5 °C ([Exceptionally Intense IOD Oct 2023](https://blog.chc.ucsb.edu/?p=1345); [Strong El Niño Persist 2023](https://blog.chc.ucsb.edu/?p=1338)).
- **Sign → outcome, by region/season:**
  - **Ethiopia Kiremt (JJAS): El Niño → DRY** over central/northern/northeastern/eastern Ethiopia. RONI explains ~50% of year-to-year Kiremt rainfall variance in the central-northern focus box, but the dry signal comes mostly from **moderate-to-strong** events (RONI > +1 °C); weak El Niños look like normal years ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982)).
  - **Eastern Horn OND (short rains): El Niño → WET** (2002, 2015, and esp. when co-occurring with positive IOD: 1997, 2006, 2023) ([Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315); [IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
  - **Eastern Horn OND/MAM: La Niña → DRY**, especially back-to-back seasons (2010, 2016/17, 2020–2022) ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
  - **Southern Africa DJF/main season: El Niño → DRY** (2002/03, 2015/16, 2023/24) ([Southern Africa Driest February 2024](https://blog.chc.ucsb.edu/?p=1375); [El Niño to Early Action](https://blog.chc.ucsb.edu/?p=1493); [Rapid El Niño & pIOD 2023](https://blog.chc.ucsb.edu/?p=1272)).
- **Analog years (El Niño, JJAS/boreal-summer, since 1981):** 1982, 1987, 1991, 1994, 1997, 2002, 2004, 2015, 2023 (RONI ≥ +0.5 °C in both JJA and JAS; 1993 excluded as a decaying event) ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982); [Extended Early Estimates JJAS 2026](https://blog.chc.ucsb.edu/?p=2049)).
- **Predictor variables:** Niño3.4 SST (observed + NMME/ECMWF forecast), RONI, September Niño3.4 persistence (Sept→OND correlation +0.99) ([Strong El Niño Persist 2023](https://blog.chc.ucsb.edu/?p=1338)).

### Indian Ocean Dipole (IOD)
- **Definition.** West-minus-east Indian Ocean SST gradient: **WIO (50–70°E, ~10–15°S–10°N) − EIO (90–110°E, 10°S–0)** ([Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315); [IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
- **Region/season controlled:** Eastern Horn **OND** short rains (IOD teleconnection strongest in SOND) ([Rapid El Niño & pIOD 2023](https://blog.chc.ucsb.edu/?p=1272)).
- **Sign → outcome:** **Positive IOD → WET/flooding** eastern Horn (1997, 2006, 2019, 2023); **negative IOD → DRY** (often co-occurs with La Niña: 2010, 2016, 2021, 2022) ([Exceptionally Intense IOD Oct 2023](https://blog.chc.ucsb.edu/?p=1345); [Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873)).
- **Notable:** the Oct 2023 forecast IOD was the **strongest positive on record (+2.9Z)**, driven by −5 °C subsurface anomalies in the eastern equatorial Indian Ocean ([Exceptionally Intense IOD Oct 2023](https://blog.chc.ucsb.edu/?p=1345)). NMME IOD forecasts at short lead are very skillful (R ≈ 0.92–0.95 with observed) ([Converging Evidence OND 2024](https://blog.chc.ucsb.edu/?p=1464)).
- **Caveat CHC flags:** 1994 was a strong +IOD but with a *neutral WIO / very cold EIO* structure — physically different, so CHC **excludes it as a wet analog** despite a similar index value ([Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315); [Crop Water 2023 Kenya](https://blog.chc.ucsb.edu/?p=1327)).

### West Pacific Gradient (WPG) & Western V Gradient (WVG)
- **Definition.** **WPG** = standardized [equatorial West Pacific SST] − [Niño3.4 SST], first defined by FEWS NET scientists in 2013 (Hoell & Funk). **WVG** = an updated version adding the **North Pacific "Western V"** region; computed as standardized [Niño3.4] − [Western V] ([La Niña & Western V MAM 2021](https://blog.chc.ucsb.edu/?p=946); [GHACOF69 Negative WVG MAM 2025](https://blog.chc.ucsb.edu/?p=1516)).
- **Mechanism (CHC's causal story).** During La Niña-like states, a warm West Pacific/Western V (amplified by human-caused warming — the "West Pacific Warming Mode") strengthens Pacific trade winds and **intensifies the Indian Ocean branch of the Walker Circulation**, driving dry subsiding air over the Horn ([GHACOF69 Negative WVG MAM 2025](https://blog.chc.ucsb.edu/?p=1516); [La Niña & Western V MAM 2021](https://blog.chc.ucsb.edu/?p=946); "Frequent but Predictable Droughts" Funk et al. 2023, cited throughout).
- **Region/season:** **WPG → eastern Horn OND**; **WVG → eastern Horn MAM (long rains / Somali *Gu*)**.
- **Sign → outcome:** **Strong negative → DRY**. When WPG < −1Z, 6 of 7 historical OND seasons were dry (2017 the exception) ([Converging Evidence OND 2024](https://blog.chc.ucsb.edu/?p=1464); [Sept NMME eHorn OND 2024](https://blog.chc.ucsb.edu/?p=1457)). For MAM, negative-WVG analogs (1989, 1999, 2000, 2008, 2011, 2012, 2018, 2021, 2022) gave below-normal rains in ~6–7 of 9 (2018 wet via MJO; 2012 normal) ([GHACOF69 Negative WVG MAM 2025](https://blog.chc.ucsb.edu/?p=1516)).
- **Predictability (quantitative):** NMME **MAM WVG forecasts are extremely skillful — R² ≈ 0.93** from February initial conditions ([GHACOF69 Negative WVG MAM 2025](https://blog.chc.ucsb.edu/?p=1516)); OND WPG R ≈ 0.92 from October ICs ([Converging Evidence OND 2024](https://blog.chc.ucsb.edu/?p=1464)).
- **Important caveat / documented "bust":** The strong WVG signal can **collapse if ENSO flips**. The MAM 2023 strong-WVG forecast busted when the climate transitioned into El Niño; MAM 2025 similarly weakened as Niño3.4 warmed ~+0.8 °C and rains came in wetter than expected ([Converging Evidence OND 2024](https://blog.chc.ucsb.edu/?p=1464); [MAM 2025 Update](https://blog.chc.ucsb.edu/?p=1648)).

### Indo-Warm Pool Heating Gradient (IWHG) — CHC's flagship OND index
- **Definition.** Difference in **ERA5 atmospheric heating** (diabatic heating + heat convergence, Wm⁻²) between the **western Indian Ocean box (50–70°E, 10°S–10°N)** and the **Indo-Pacific Warm Pool (90–150°E, 15°S–15°N)**. It integrates IOD + WPG + Niño3.4 influences (plus potentially MJO) into one physically-grounded index. SST-based estimate: `IWHG_est = 12 + 323·IOD − 193·WestPac + 94·Niño3.4` (R² = 0.84), quantile-matched to the observed distribution ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
- **Why CHC built it.** Because eastern-Horn OND SST teleconnections are **non-stationary** (Nicholson 2015) and the Indo-Pacific is warming fast; atmospheric heating is a more direct measure of forcing than SST, and the relationship is **symmetric** — it captures both droughts and floods, unlike the asymmetric SST picture ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
- **Sign → outcome (quantitative thresholds):**
  - IWHG < **−100 Wm⁻²** → 22/33 seasons (73%) below-normal.
  - IWHG > **+200 Wm⁻²** → 14/17 seasons (82%) above-normal.
  - 1950–2023 IWHG↔eHorn-OND-SPI **R² = 0.69**; ~100 Wm⁻² ≈ 0.3Z SPI shift ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
- **Forecast skill (headline result):** NMME-based IWHG forecasts correlate with observed OND IWHG at **R = 0.82 (July), 0.84 (Aug), 0.92 (Sep/Oct)**; correlation with eHorn SPI up to 0.93. July forecasts reliably flag the "< −100 Wm⁻² danger zone" (11 hits, few false alarms over 1991–2023) ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
- **Spatial footprint:** IWHG regression influence spans all of Somalia, southern Ethiopia, most of Kenya & Tanzania; slopes peak (~0.6 mm/Wm⁻²) in coastal Kenya/Tanzania, southern-central Somalia, and central Kenya highlands ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
- **Operational use:** IWHG drove the OND 2024 outlooks month-by-month (July −256, Aug −189, Sep −252, Oct −243 Wm⁻²) and generated the analog sets ([Aug OND 2024](https://blog.chc.ucsb.edu/?p=1444); [Sept NMME eHorn OND 2024](https://blog.chc.ucsb.edu/?p=1457); [Converging Evidence OND 2024](https://blog.chc.ucsb.edu/?p=1464)).

### Western Indian Ocean (WIO) SST — the dominant *wet* driver
- Very warm WIO SST is the strongest single predictor of **wet/flood** eastern-Horn OND seasons, and can act **independently of El Niño** (2019 was an extreme +IOD/wet season without El Niño) ([Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315); [Rapid El Niño & pIOD 2023](https://blog.chc.ucsb.edu/?p=1272)). This is why CHC includes non-El Niño WIO-warm years (2019) among wet analogs.

### Subtropical Indian Ocean Dipole (SIOD) — Southern Africa
- Western-minus-eastern subtropical S. Indian Ocean SST. **Negative SIOD amplifies El Niño-driven Southern Africa drought** (Dec–Mar). In Feb 2024 a strong negative SIOD + weakened Angola Low produced the driest February on record in central Southern Africa; the same pairing appeared in Feb 1992 ([Southern Africa Driest February 2024](https://blog.chc.ucsb.edu/?p=1375)).

### Madden-Julian Oscillation (MJO) & Kelvin waves
- Sub-seasonal driver of **wet** spells; responsible for extreme MAM 2018 Kenya rains and part of MAM 2025's better-than-forecast start ([Early March Kenya 2026](https://blog.chc.ucsb.edu/?p=1923); [Pessimistic MAM 2025](https://blog.chc.ucsb.edu/?p=1566); [MAM 2025 Update](https://blog.chc.ucsb.edu/?p=1648)). Not predictable beyond ~2–3 weeks — a key reason **wet MAM seasons lack a clean long-lead SST signature** (see [Kenya](#kenya)).

### Warming / VPD / temperature (impact amplifier)
- Not a rainfall driver, but CHC repeatedly stresses that **above-normal Tmax and VPD desiccate soils and rangeland**, amplifying the impact of any given rainfall deficit (El Niño Kiremt heat, OND 2025 Somalia >38 °C, Southern Africa Feb 2024). Warming also intensifies the WPG/WVG mechanism itself ([Warming World Desiccation](https://blog.chc.ucsb.edu/?p=1300); [2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982); [CHIRPS3 Oct-Nov 2025 Drought](https://blog.chc.ucsb.edu/?p=1905)).

---

# Regions

## Region → season → predictability summary table

| Region | Season (months) | Dominant drivers | Predictability | Best predictor index (skill) |
|---|---|---|---|---|
| Eastern Horn | **OND "short rains"** | IOD, WPG, El Niño, WIO SST → IWHG | **HIGH** (CHC's most predictable season) | IWHG (R up to 0.92); WPG (R 0.92); NMME rainfall (R ~0.9) |
| Eastern Horn | **MAM "long rains" / Gu** | WVG, La Niña, Walker circulation | **Asymmetric:** dry seasons predictable, wet seasons NOT | WVG (R² 0.93, Feb) — but only skillful for the *dry* tail |
| Ethiopia | **Kiremt (JJAS)** | El Niño (dry), temperature | **MODERATE-HIGH** (central-N box) | RONI (R² ~0.5 obs); ECMWF SEAS5 JJAS (75% hit rate) |
| Ethiopia | **Belg (FMAM)** | La Niña, complex | LOW-MODERATE | — (less documented) |
| Kenya | MAM & OND (as eHorn) + early-onset | WVG/IOD; **sub-seasonal** for wet MAM | Onset & wet-MAM newly shown predictable via S2S | Downscaled ECMWF S2S March (R² 0.69–0.86) |
| Somalia | Gu (MAM) & Deyr (OND) | same as eHorn; strongest IWHG footprint | **HIGH** (best spatial NMME skill) | IWHG / NMME rainfall (peak skill S. Somalia) |
| Greater Horn / EA | all | ENSO/IOD/WPG | HIGH for OND | GHACOF/ICPAC multi-model consensus |
| Southern Africa | **Oct–May main season** (esp. DJF) | El Niño (dry), SIOD | MODERATE-HIGH at long lead via ENSO | ENSO-based preseason crop-yield forecast |
| Central America | **primera/postrera (Jun–Sep)** | El Niño (dry) | MODERATE (mentioned, less quantified) | El Niño analogs |
| South Asia / India | **Kharif monsoon (JJAS)** | El Niño (dry) | MODERATE (analog-based) | El Niño analogs |
| Afghanistan | Oct–May winter wheat + spring | La Niña (dry) | LOW-MODERATE | NMME/CPC precip outlooks |

---

## Eastern Horn of Africa

**Definition (CHC's "eHorn"):** Kenya, Ethiopia, and Somalia **east and south of ~38°E, 8°N** — sometimes given as 38–50°E, 4.5°S–8.5°N ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418); [Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873)). This is the corpus's single most-analyzed region and the clearest showcase of teleconnection-based predictability.

**Two rainy seasons:**
- **OND "short rains"** (Oct–Nov–Dec; sometimes SOND) — the **more predictable** season.
- **MAM "long rains"** (Mar–Apr–May; Somali *Gu*) — the primary/larger season for many areas but **harder to predict**, especially wet outcomes.

**Recent volatility:** Since OND 2016, the eHorn has whipsawed — of 16 seasons, **8 dry, 6 wet, only 2 normal** ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)). The 2020–2022 multi-year La Niña produced **five consecutive failed seasons**, killed >8 million livestock, and required >$2 billion in relief ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418); [Warming World Desiccation](https://blog.chc.ucsb.edu/?p=1300)).

### Eastern Horn — OND "short rains" (the predictable season)

- **Drivers & sign:** Wet ← positive IOD, El Niño, very warm WIO SST, strong positive IWHG (> +200 Wm⁻²). Dry ← negative IOD, La Niña, strong negative WPG, strong negative IWHG (< −100 Wm⁻²). SST signatures of both wet and dry seasons are **large and clear**, making the season **highly predictable** ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418); [Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315)).
- **Asymmetry CHC emphasizes:** *dry* seasons are La Niña + warm-West-Pacific (WPG) driven; *wet* seasons are warm-WIO / +IOD driven ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
- **Predictors & skill (quantitative):**
  - **IWHG:** R = 0.82–0.92 (Jul→Oct); eHorn-SPI correlation up to 0.93 ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
  - **WPG:** R ≈ 0.92 (Oct); WPG < −1Z ⇒ dry in 6/7 cases ([Converging Evidence OND 2024](https://blog.chc.ucsb.edu/?p=1464)).
  - **NMME rainfall:** EEA OND regional average R ≈ 0.9 (Sep ICs); peak spatial skill in **southern Somalia**, SE Ethiopia, NE Kenya (Shukla et al. 2019) ([Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873); [IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
  - Early literature: Kolstad & MacLeod (2022) — Aug IOD+Niño3.4 explain ~40% of OND variance ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
- **Analog years:**
  - **Dry OND:** 1998, 2005, 2010, 2016, 2020, 2021, 2022 ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
  - **Wet OND:** 1997, 2002, 2006, 2011, 2015, 2019, 2023 ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418); [Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315)).
  - **OND 2024 dry analog set (from IWHG):** 1983, 1984, 1985, 1995, 1996, 2000, 2001, 2005, 2008, 2016, 2017, 2020, 2021, 2022 ([Sept NMME eHorn OND 2024](https://blog.chc.ucsb.edu/?p=1457)).
  - **OND 2025 dry analog set:** 1995, 1996, 1998, 1999, 2005, 2010, 2016, 2020, 2021, 2022, 2024 ([Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873)).
- **Operational/COF context:** Outlooks are anchored to **GHACOF** (Greater Horn of Africa Climate Outlook Forum) / **ICPAC** and KMD — e.g. GHACOF 71 (OND 2025), GHACOF 69 (MAM 2025), and multi-agency "Preparedness Planning Needed" alerts ([Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873); [GHACOF69 Negative WVG MAM 2025](https://blog.chc.ucsb.edu/?p=1516); [Aug OND 2024](https://blog.chc.ucsb.edu/?p=1444)).
- **Case histories in corpus:** dry OND 2016 (first blog, WPG-based, R≈2× West-Pacific vs central-Pacific weighting) ([Kenya/Somalia Short Rains 2016](https://blog.chc.ucsb.edu/?p=10)); extreme wet OND 2023 (record +IOD + strong El Niño) ([Exceptionally Intense IOD Oct 2023](https://blog.chc.ucsb.edu/?p=1345); [Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315)); dry OND 2024 (negative WPG/IOD without a strong La Niña) ([Converging Evidence OND 2024](https://blog.chc.ucsb.edu/?p=1464)); catastrophic dry OND/Deyr 2025 (La Niña + record negative IOD −1.49 °C; Somalia Nov rain 9% of normal) ([Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873); [CHIRPS3 Oct-Nov 2025 Drought](https://blog.chc.ucsb.edu/?p=1905)).

### Eastern Horn — MAM "long rains" / Gu (the harder season)

- **Drivers & sign:** **Dry ← strong negative WVG + La Niña**, via Walker-circulation intensification and delayed onset. The "long rains decline" is a documented multi-decadal drying trend ([La Niña & Western V MAM 2021](https://blog.chc.ucsb.edu/?p=946); [East Africa Rainy Seasons Changing](https://blog.chc.ucsb.edu/?p=1997)).
- **The predictability asymmetry (critical for us):** **Dry MAM seasons have a clear SST signature (negative WVG) and are predictable; wet MAM seasons do NOT have a clean SST signature** and depend on sub-seasonal MJO/Kelvin-wave activity that isn't predictable far ahead ([Early March Kenya 2026](https://blog.chc.ucsb.edu/?p=1923); [GHACOF69 Negative WVG MAM 2025](https://blog.chc.ucsb.edu/?p=1516)).
- **Predictor & skill:** **NMME/WVG (Feb ICs) is extremely skillful — R² ≈ 0.93** for the WVG index itself; negative-WVG analogs give ~66% regional chance of below-normal MAM ([GHACOF69 Negative WVG MAM 2025](https://blog.chc.ucsb.edu/?p=1516)). But skill is concentrated in the *dry tail* and can bust if ENSO flips ([Converging Evidence OND 2024](https://blog.chc.ucsb.edu/?p=1464); [MAM 2025 Update](https://blog.chc.ucsb.edu/?p=1648)).
- **MAM analog years (negative-WVG/dry):** 1989, 1999, 2000, 2008, 2011, 2012, 2018, 2021, 2022 ([GHACOF69 Negative WVG MAM 2025](https://blog.chc.ucsb.edu/?p=1516); [Pessimistic MAM 2025](https://blog.chc.ucsb.edu/?p=1566)); an earlier 2021 analog set: 1999, 2000, 2001, 2008, 2009, 2011, 2012, 2017 ([La Niña & Western V MAM 2021](https://blog.chc.ucsb.edu/?p=946)).
- **Circulation diagnostics CHC uses:** 200 hPa geopotential-height/wind anomalies (Matsuno-Gill La Niña low + N. Pacific high driving equatorial convergence/subsidence near the dateline), equatorial vertical-velocity, low-level moisture transport ([La Niña & Western V MAM 2021](https://blog.chc.ucsb.edu/?p=946); [Pessimistic MAM 2025](https://blog.chc.ucsb.edu/?p=1566)).
- **Structural change:** MAM long rains in the eastern Horn are becoming **shorter and less reliable** — fewer rainy days, earlier cessation (Kisembe et al. 2026) ([East Africa Rainy Seasons Changing](https://blog.chc.ucsb.edu/?p=1997)).

---

## Ethiopia

**Rainy seasons:**
- **Kiremt (JJAS, ~Jun–Sep)** — the main season; contributes **60–70% of annual rainfall over most of Ethiopia, up to 85% in the NW**; underpins the main **Meher** crop harvest ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982)).
- **Belg (~Feb–May)** — secondary season, southern/central Ethiopia; **La Niña-associated** droughts hit drier areas here ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982)).
- **Karma/Karan (Jul–Sep)** — northeastern Afar pastoral rains ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982)).

**Kiremt drivers & predictability:**
- **El Niño → DRY Kiremt** over central, northern, northeastern, eastern Ethiopia (dense-population, high-productivity zones). Western/SW Ethiopia usually still gets adequate rains ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982)).
- **Focus region:** central-northern Ethiopia box **7°–14°N, 36.5°–40.5°E** (from the Funk et al. 2016 BAMS 2015-drought attribution study), chosen for a robust ENSO-rainfall teleconnection ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982); [Rapid El Niño & pIOD 2023](https://blog.chc.ucsb.edu/?p=1272)).
- **Quantitative skill:**
  - Observed JAS RONI ↔ Kiremt rainfall **R² ≈ 0.5** in the focus box (ENSO ≈ half the interannual variance) — but driven by **moderate-strong** events; weak El Niños resemble normal years ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982)).
  - **ECMWF SEAS5** JJAS forecasts (May ICs) correctly called below-normal **75% of the time** (1982–2025) in this box; independent of the empirical RONI analysis ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982)).
  - July sub-seasonal forecasts for the Kiremt region: **R² ≈ 0.48** ([Ethiopia Very Poor 2026 Kiremt](https://blog.chc.ucsb.edu/?p=2013)).
  - 6 of 9 El Niño seasons put Kiremt rainfall in the bottom 20% (< 782 mm in the focus box) ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982)).
- **Analog years (El Niño, JJAS):** 1982, 1987, 1991, 1994, 1997, 2002, 2004, 2015, 2023 (1994 = weak El Niño, wet; 2002 = dry moderate El Niño the model missed) ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982)).
- **Crop-yield signal:** El Niño years → below-normal Meher sorghum/maize, worst in eastern Amhara, Tigray, NE Oromia; national yields only ~2% below average on average but 10–15% in bad cases; sorghum/maize (lower elevation) hit harder than wheat (higher elevation) ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982)).
- **Worst-case reference:** 2015 (El Niño, both Belg and Kiremt failed → national catastrophe) ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982); [Rapid El Niño & pIOD 2023](https://blog.chc.ucsb.edu/?p=1272)).
- **2026 live case:** rapid El Niño onset (RONI +1.25 °C by early June, Niño3.4 +1.8 °C) → convergent obs + July S2S + El Niño analogs → **very poor 2026 Kiremt** projected, comparable to/worse than 1987/2015 ([Ethiopia Very Poor 2026 Kiremt](https://blog.chc.ucsb.edu/?p=2013); [Extended Early Estimates JJAS 2026](https://blog.chc.ucsb.edu/?p=2049)).
- **Operational context:** Ethiopian Meteorological Institute (EMI) station network + **SMPG** tool; GHACOF 73 consolidated forecast; EDRMC vulnerability mapping ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982); [Ethiopia Very Poor 2026 Kiremt](https://blog.chc.ucsb.edu/?p=2013)).

---

## Kenya

**Seasons:** MAM long rains + OND short rains (shares eHorn drivers). Highlands W/E of Rift, Lake Victoria basin, SE lowlands, coast (Kilifi/Kwale) have distinct onset behavior ([Early March Kenya 2026](https://blog.chc.ucsb.edu/?p=1923)).

**Distinctive Kenya themes in the corpus:**
- **The "wet long-rains conundrum."** OND has clear SST signatures; **wet MAM seasons do NOT** — the corpus's clearest statement that wet long-rains are the hard forecasting problem ([Early March Kenya 2026](https://blog.chc.ucsb.edu/?p=1923)).
- **New sub-seasonal opportunity (novel CHC result):** downscaled **ECMWF S2S March forecasts predict monthly Kenya rainfall very well — R² 0.69 (whole-month) up to 0.86 (Mar 1–10)**; very-wet and very-dry Marches discriminated with 100% hits / no false alarms in-sample. Wet March **persists into wet April** (9/13 years), giving an early read on good/bad growing seasons and flood risk ([Early March Kenya 2026](https://blog.chc.ucsb.edu/?p=1923); [Pamoja Ni Bora](https://blog.chc.ucsb.edu/?p=1968)).
- **Onset/Start-of-Season forecasting** via WRSI (25 mm/10-day + 20 mm/next 20 days) driven by CHIRPS3 + SubC/ECMWF; validated hits/misses/false-alarms show reliable capture of wet events at 0.05° ([Early March Kenya 2026](https://blog.chc.ucsb.edu/?p=1923); [Pamoja Ni Bora](https://blog.chc.ucsb.edu/?p=1968)).
- **Very wet OND 2023 case:** strong El Niño + record +IOD → ~2× normal short rains in central/eastern Kenya; WRSI modeling showed ~40% fewer poor-season outcomes, +20–30% WRSI ([Crop Water 2023 Kenya](https://blog.chc.ucsb.edu/?p=1327); [Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315)).
- **Catastrophic OND/Deyr 2025:** central-eastern Kenya Oct–Nov rain 53% of normal, rainfall-minus-RefET ≈ −298 mm (near record); WRSI failure across most of Kenya; verified with 3D-PAWS dual-gauge stations ([CHIRPS3 Oct-Nov 2025 Drought](https://blog.chc.ucsb.edu/?p=1905); [Field Assessments](https://blog.chc.ucsb.edu/?p=1949)).
- **2026 Kiremt-adjacent dryness:** western Kenya (W/N of 37°E, 0.5°N) Jun–Jul 2026 the lowest on record (38 mm/2 mo); maize failures by planting date ([Extended Early Estimates JJAS 2026](https://blog.chc.ucsb.edu/?p=2049)).
- **Institutional model:** deep **KMD/KMSA + CHC + KIT + Rhiza + UCAR ICDP** collaboration (3D-PAWS network — 54–57 stations; GitHub-Actions S2S system; Nimbus AI forecasting). The strongest "operational partnership" story in the corpus ([Pamoja Ni Bora](https://blog.chc.ucsb.edu/?p=1968); [3D-PAWS](https://blog.chc.ucsb.edu/?p=1840); [Early March Kenya 2026](https://blog.chc.ucsb.edu/?p=1923)).

---

## Somalia

**Seasons:** **Gu (MAM)** and **Deyr (OND)** — shares eHorn drivers; **Somalia has the single strongest NMME/IWHG predictability footprint** in the region ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418); [Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873)).

- **Peak spatial forecast skill:** NMME OND rainfall skill and IWHG regression slopes are highest over **southern/central Somalia** (plus SE Ethiopia, NE Kenya) ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).
- **Crop signal:** in OND analog years, Somalia **Deyr sorghum yields below average >80% of the time** (8/10 analogs; deficits >40% in five: 1996-97, 2005-06, 2010-11, 2016-17, 2022-23); maize similar (~22% below) ([Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873)). But wet +IOD/El Niño years can *also* fail via flooding (1997 Deyr) ([Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315)).
- **Bay/Bakool** agropastoral zone repeatedly flagged; **Famine (IPC Phase 5) risk** after failed 2025 OND + poor 2026 Gu ([East Africa Rainy Seasons Changing](https://blog.chc.ucsb.edu/?p=1997); [Field Assessments](https://blog.chc.ucsb.edu/?p=1949)).
- **Record drought Oct–Nov 2025:** Somalia rain **33 mm (31% of normal), November ~4 mm (9%)**; rainfall-minus-RefET ≈ −338 mm; NDVI lowest on record (since 2012); as bad as any season back to 1981; national emergency declared ([CHIRPS3 Oct-Nov 2025 Drought](https://blog.chc.ucsb.edu/?p=1905); [Field Assessments](https://blog.chc.ucsb.edu/?p=1949)).
- **Data partners:** SWALIM + Somalia Dept. of Meteorology stations feed CHIRPS/SMPG ([CHIRPS3 Oct-Nov 2025 Drought](https://blog.chc.ucsb.edu/?p=1905); [3D-PAWS](https://blog.chc.ucsb.edu/?p=1840)).

---

## Greater Horn / East Africa (general)

- **Structural rainfall change (Kisembe et al. 2026):** East Africa's rainy seasons are shifting in *character*, not just totals — **N. East Africa (Sudan, NW Ethiopia): wetter via more rainy days; S. East Africa (Tanzania): wetter via more intense events; eastern Horn (E. Kenya, C/S Somalia): shorter, drier MAM** ([East Africa Rainy Seasons Changing](https://blog.chc.ucsb.edu/?p=1997)).
- **Regional forecasting architecture:** **GHACOF/ICPAC** consensus forums (68th–73rd referenced), KMD/EMI national forums, and the CHC **East Africa Agroclimate Special Report** (Ethiopia/Kenya/Somalia) built on the **SMPG** tool + **Improved Rainfall Estimates (IRE)** ([3D-PAWS](https://blog.chc.ucsb.edu/?p=1840); [2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982); [Crop Water 2023 Kenya](https://blog.chc.ucsb.edu/?p=1327)).
- **Climate-change framing:** warming West Pacific / Indian Ocean makes La Niña droughts more frequent but **more predictable** at long lead (up to 8 months) — the recurring thesis of Funk's "predictable extremes" argument ([Warming World Desiccation](https://blog.chc.ucsb.edu/?p=1300); [IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).

---

## Sahel / West Africa

**Essentially absent from this corpus.** West Africa appears only obliquely: **Ghana and Senegal** are named as Nimbus AI-forecasting testbeds alongside Kenya ([Pamoja Ni Bora](https://blog.chc.ucsb.edu/?p=1968)). No Sahelian JAS-monsoon teleconnection analysis, driver index, or skill statement appears in any of the 30 posts. **This is a notable corpus gap** — if our project needs Sahel/West Africa coverage, CHC's blog does not supply it here.

---

## Southern Africa

**Season:** Oct–May main season (maize), peaking **DJF**; critical window Jan–Feb ([Southern Africa Driest February 2024](https://blog.chc.ucsb.edu/?p=1375); [El Niño to Early Action](https://blog.chc.ucsb.edu/?p=1493)).

- **Drivers & sign:** **El Niño → DRY** (higher pressure/subsidence, weakened **Angola Low**; Hoell et al.); **negative SIOD amplifies** the El Niño drought (Hoell et al. 2017) ([Southern Africa Driest February 2024](https://blog.chc.ucsb.edu/?p=1375)).
- **Focus box:** central Southern Africa **20–35°E, 13–22.5°S** (SE Angola, S. Zambia, Zimbabwe, N. Botswana, NE Namibia) ([Southern Africa Driest February 2024](https://blog.chc.ucsb.edu/?p=1375)).
- **Predictability & lead time:** **ENSO-based preseason maize/wheat-yield forecasts** are operational and skillful in **SE Africa** (and SE Asia, S/C Asia wheat), issued up to ~1 year ahead — e.g. the June 2023 below-average Southern Africa maize outlook that verified as the 2023/24 El Niño drought ([El Niño to Early Action](https://blog.chc.ucsb.edu/?p=1493); Anderson et al. 2024).
- **Analog/case:** Feb 2024 = **driest February on record** in central areas, rivaled only by Feb 1992 (both strong El Niño + negative SIOD + weak Angola Low); Zambia/Malawi declared national disasters, ~20.9 M food-insecure ([Southern Africa Driest February 2024](https://blog.chc.ucsb.edu/?p=1375); [El Niño to Early Action](https://blog.chc.ucsb.edu/?p=1493)). Zimbabwe NDJF El Niño analogs: 1982, 1986, 1991, 1994, 1997, 2002, 2009, 2015 (6/8 dry) ([Rapid El Niño & pIOD 2023](https://blog.chc.ucsb.edu/?p=1272)).
- **Contrast (2025/26):** a *good* Southern Africa season (La Niña context) with above-normal Nov–Dec rains and localized flooding — while East Africa's OND failed ([Field Assessments](https://blog.chc.ucsb.edu/?p=1949)).
- **Operational context:** GEOGLAM Crop Monitor, SADC Agromet, national met services; 3D-PAWS extending to Zimbabwe (16 stations) ([El Niño to Early Action](https://blog.chc.ucsb.edu/?p=1493); [3D-PAWS](https://blog.chc.ucsb.edu/?p=1840)).

---

## Central America

**Season:** boreal-summer wet season (primera/postrera, ~Jun–Sep) in the Central American Dry Corridor (Guatemala, Honduras, Nicaragua) ([Extended Early Estimates JJAS 2026](https://blog.chc.ucsb.edu/?p=2049)).

- **Driver & sign:** **El Niño boreal-summer → DRY** (negative rainfall teleconnection); part of the same El Niño analog set (1982, 1987, 1991, 1994, 1997, 2002, 2004, 2015, 2023) used globally by CHC's Extended Early Estimates ([Extended Early Estimates JJAS 2026](https://blog.chc.ucsb.edu/?p=2049)).
- **2026 case:** exceptional dryness projected — Guatemala/Honduras/Nicaragua Jun–Jul the 2nd-driest on record; FEWS NET food-crisis conditions; but noted that CA hydroclimatology varies over small spatial scales so impacts are localized ([Extended Early Estimates JJAS 2026](https://blog.chc.ucsb.edu/?p=2049)).
- **Predictability:** treated via El Niño analogs, **less quantified** than East Africa — no dedicated skill statistics or driver-index regression in the corpus.
- **Operational context:** **Mesas Agroclimáticas** (agroclimatic roundtables, held 3×/yr) — a strong farmer-feedback co-production loop; crop-calendar shifts (maize→coffee/vegetables in Guatemala) ([Field Assessments](https://blog.chc.ucsb.edu/?p=1949)).

---

## South Asia / India

- **Season:** Kharif / SW monsoon (JJAS). **El Niño → DRY** (same global analog logic) ([Extended Early Estimates JJAS 2026](https://blog.chc.ucsb.edu/?p=2049)).
- **2026 case:** driest June in 12 yrs / 5th-driest since 1901 (IMD); southern India Jun–Jul potentially driest on record since 1981; El Niño analog August–September fill → season comparable to the severe 1987/2002 droughts ([Extended Early Estimates JJAS 2026](https://blog.chc.ucsb.edu/?p=2049)).
- **Predictability:** analog-based, **not quantified** with a driver index in the corpus. Also flagged as an ENSO-based **preseason wheat-yield** skill region (S/C Asia) ([El Niño to Early Action](https://blog.chc.ucsb.edu/?p=1493)).

---

## Other

### Afghanistan
- **Season:** Oct-start winter wheat + spring crops. **La Niña → below-average precipitation** + above-average temperature ([Afghanistan Climate & Food Prices](https://blog.chc.ucsb.edu/?p=1590)).
- Mostly a **food-security/markets** post (Torkham border closure, wheat prices) rather than a teleconnection analysis; predictor detail is limited to NOAA/CPC/NMME seasonal precip outlooks. Low added value for teleconnection-design purposes.

### Methods, data & tools posts
These carry no regional teleconnection content but define the toolchain our cross-check will implicitly rely on:
- **CHIRPS v3.0** — improved satellite algorithm (higher variance, better extremes), 60°S–60°N, gauge-undercatch corrected, ~90 station sources; recommend comparing to Legates-corrected gauges ([CHIRPS v3.0](https://blog.chc.ucsb.edu/?p=1510)).
- **3D-PAWS** — low-cost ($400–500) 3D-printed automatic weather stations, dual rain gauges; 54–57 in Kenya, 16 in Zimbabwe; fill declining African station networks ([3D-PAWS](https://blog.chc.ucsb.edu/?p=1840)).
- **SMPG / Early Estimates / Extended Early Estimates** — combine CHIRPS3 observations + CHIRPS-GEFS (15-day) + SubC (30-day) + analog years into end-of-season percentile outlooks ([Ethiopia Very Poor 2026 Kiremt](https://blog.chc.ucsb.edu/?p=2013); [Extended Early Estimates JJAS 2026](https://blog.chc.ucsb.edu/?p=2049)).
- **Crop-area mapping** — Sentinel-2 spectral-mixture + Random Forest on Google Earth Engine; validated in Malawi, Tigray, Zimbabwe ([Crop Area Mapping](https://blog.chc.ucsb.edu/?p=1829)).
- **Field assessments / WRSI validation** — ground-truthing satellite/model estimates across East, Southern Africa, Central America ([Field Assessments](https://blog.chc.ucsb.edu/?p=1949)).

---

## Cross-cutting: Methods, data & tools (reference)

| Element | What it is | Used for |
|---|---|---|
| **CHIRPS v2/v3** | Satellite-IR + station blended rainfall, 0.05° | All rainfall analysis; analogs; WRSI |
| **CHIRTS-ERA5 Tmax / VPD** | Temperature reanalysis matched to CHIRTS | Heat/desiccation amplification |
| **NOAA ERSSTv5** | SST reconstruction | Driver indices (Niño3.4, IOD, WPG, WVG) |
| **ERA5 atmospheric heating** | Diabatic heating + convergence, Wm⁻² | IWHG index |
| **NMME (6–7 models)** | Multi-model SST/precip ensemble | Skill-weighted index forecasts, analog selection |
| **ECMWF SEAS5 / S2S (Cycle 49)** | Seasonal & sub-seasonal | Ethiopia Kiremt; Kenya onset; downscaled to 0.05° via quantile matching |
| **CHIRPS-GEFS / SubC** | 15–30 day downscaled forecasts | Early Estimates, SMPG, WRSI |
| **WRSI** | Water Requirement Satisfaction Index (maize/sorghum) | Crop-water outcome scenarios |
| **RONI** | Relative Oceanic Niño Index | Preferred ENSO monitor (removes global warming trend) |
| **SMPG** | Seasonal Monitoring & Probability Generator (QGIS) | Ethiopia/Kenya/Somalia dekadal outlooks |

**CHC's skill-weighted NMME method (reusable recipe):** for each ocean index region, extract 6-model NMME SST forecasts, standardize (1982–2022 base), regress each model on observed ERSSTv5, weight by R², combine, then bivariate-regress onto the observed index — yielding a forecast + empirical 80th-percentile confidence bound ([Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315); [Rapid El Niño & pIOD 2023](https://blog.chc.ucsb.edu/?p=1272)).

---

# Implications for Region Selection

**Recommendation: the Eastern Horn of Africa OND "short rains" — operationalized on Somalia (with southern/eastern Kenya as the immediate extension) — is the single best-supported target for a rich teleconnection-based forecast-design study.**

**Why (grounded in the corpus):**

1. **It is the season CHC itself calls the most predictable**, with multiple *independent, quantified* predictors: IWHG (R up to 0.92 with the observed index; 0.93 with SPI), WPG (R 0.92), IOD (R 0.92–0.95), and NMME rainfall (R ~0.9) — more skill statistics than any other region/season in the corpus ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418); [Converging Evidence OND 2024](https://blog.chc.ucsb.edu/?p=1464); [Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873)).
2. **The driver physics are explicit and multi-index** (ENSO + IOD + WPG/WVG + WIO SST, integrated by the IWHG), giving a rich, well-labeled predictor space to compare our automated discovery against — including CHC's non-trivial, testable claims (asymmetry of wet vs dry drivers; symmetric IWHG; the "1994 excluded" structural nuance; the WVG "bust when ENSO flips") ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418); [Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315)).
3. **Within the eHorn, southern/central Somalia has the highest spatial forecast skill** and the densest crop-yield validation (Deyr sorghum below-average >80% of analog years), making it the sharpest single-country testbed ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418); [Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873)).
4. **Deep, dense analog record** (well-defined wet and dry analog year lists for OND back to the 1980s) and abundant recent extreme cases (2016, 2019, 2020–22, 2023, 2024, 2025) for out-of-sample checking ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)).

**Strong secondary option — Ethiopia Kiremt (JJAS):** if a *single-country, single-season, ENSO-dominated* problem is preferred, Ethiopia's central-northern Kiremt box is the best-documented alternative — one clean dominant driver (El Niño, R² ~0.5 obs; SEAS5 75% hit rate), a fixed focus region, and a rich 2026 live case ([2026 El Niño & Ethiopia Kiremt](https://blog.chc.ucsb.edu/?p=1982); [Ethiopia Very Poor 2026 Kiremt](https://blog.chc.ucsb.edu/?p=2013)). It trades the eHorn's richer multi-index predictor space for cleaner attribution.

**Regions to deprioritize for this purpose:** Central America, South Asia, and Southern Africa are covered only via El Niño analogs with little index-level skill quantification; Afghanistan is a markets post; the **Sahel/West Africa is absent** from the corpus.

---

## Notable gaps & disagreements found in the corpus

- **Wet-MAM unpredictability (an internal tension, not a contradiction):** CHC repeatedly states wet long-rains lack an SST signature ([Early March Kenya 2026](https://blog.chc.ucsb.edu/?p=1923)) yet simultaneously reports newly-found **sub-seasonal** predictability of wet March/April Kenya rains via ECMWF S2S (R² 0.69–0.86) ([Early March Kenya 2026](https://blog.chc.ucsb.edu/?p=1923); [Pamoja Ni Bora](https://blog.chc.ucsb.edu/?p=1968)). Reconciled as: *seasonal-SST* predictability is asymmetric (dry only), but *sub-seasonal* skill exists for wet onsets. Worth testing in our own runs.
- **WVG/WPG "busts":** CHC candidly documents that strong negative WVG/WPG forecasts fail when ENSO transitions (MAM 2023, MAM 2025) — a real limit on the flagship MAM predictor ([Converging Evidence OND 2024](https://blog.chc.ucsb.edu/?p=1464); [MAM 2025 Update](https://blog.chc.ucsb.edu/?p=1648)).
- **Analog-set instability:** OND analog lists differ year-to-year and between posts (e.g. OND 2024 vs OND 2025 sets; the MAM 2021 vs MAM 2025 sets), because they are re-derived from each forecast's index value ± confidence interval — expected, but means "analog years" are not a fixed ground truth ([Sept NMME eHorn OND 2024](https://blog.chc.ucsb.edu/?p=1457); [Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873); [GHACOF69 Negative WVG MAM 2025](https://blog.chc.ucsb.edu/?p=1516)).
- **Sign complexity for Somalia OND:** *both* extreme-dry (La Niña/−IOD) and extreme-wet (+IOD/El Niño, via flooding) OND seasons can crash Deyr crop yields — the yield↔rainfall relationship is non-monotonic ([Sept NMME IOD & El Niño 2023](https://blog.chc.ucsb.edu/?p=1315); [Below-Normal OND 2025](https://blog.chc.ucsb.edu/?p=1873)).
- **Non-stationarity caveat:** CHC explicitly warns eHorn-OND SST teleconnections are non-stationary (Nicholson 2015) and shift with Indo-Pacific warming — a reason they moved to atmospheric-heating (IWHG) over raw SST ([IWHG OND 2024](https://blog.chc.ucsb.edu/?p=1418)). Any fixed-relationship model (ours or theirs) should be validated across sub-periods.
- **Geographic gaps:** no Sahel/West Africa teleconnection content; Southern Africa/Central America/India lack index-level skill numbers; Belg (Ethiopia) is mentioned but never quantified.

---

## Appendix — Post Index

| # | Date | Short title | URL |
|---|---|---|---|
| 01 | 2026-07-27 | Extended Early Estimates JJAS 2026 (E. Africa, India, C. America) | https://blog.chc.ucsb.edu/?p=2049 |
| 02 | 2026-06-03 | 2026 El Niño & Ethiopia Kiremt | https://blog.chc.ucsb.edu/?p=1982 |
| 03 | 2026-07-08 | Ethiopia Very Poor 2026 Kiremt | https://blog.chc.ucsb.edu/?p=2013 |
| 04 | 2026-03-05 | Early March Kenya bountiful rains (S2S) | https://blog.chc.ucsb.edu/?p=1923 |
| 05 | 2026-04-28 | Pamoja Ni Bora — Kenya forecasting collaboration | https://blog.chc.ucsb.edu/?p=1968 |
| 06 | 2025-06-26 | 3D-PAWS weather observations | https://blog.chc.ucsb.edu/?p=1840 |
| 07 | 2026-06-24 | East Africa rainy seasons are changing | https://blog.chc.ucsb.edu/?p=1997 |
| 08 | 2025-12-12 | CHIRPS3 Oct–Nov 2025 Somalia/Kenya drought | https://blog.chc.ucsb.edu/?p=1905 |
| 09 | 2023-09-13 | Sept NMME IOD & El Niño 2023 | https://blog.chc.ucsb.edu/?p=1315 |
| 10 | 2023-09-13 | Crop water — wet 2023 short rains Kenya | https://blog.chc.ucsb.edu/?p=1327 |
| 11 | 2025-02-12 | Introducing CHIRPS v3.0 | https://blog.chc.ucsb.edu/?p=1510 |
| 12 | 2026-03-23 | Field assessments strengthen FEWS NET | https://blog.chc.ucsb.edu/?p=1949 |
| 13 | 2025-10-09 | Below-normal OND 2025 eastern East Africa | https://blog.chc.ucsb.edu/?p=1873 |
| 14 | 2024-07-09 | IWHG & extreme short rains (OND 2024 outlook) | https://blog.chc.ucsb.edu/?p=1418 |
| 15 | 2025-05-21 | Crop-area mapping (Sentinel-2/GEE) | https://blog.chc.ucsb.edu/?p=1829 |
| 16 | 2025-04-12 | MAM 2025 rainfall season update | https://blog.chc.ucsb.edu/?p=1648 |
| 17 | 2025-03-13 | Afghanistan climate, border & food prices | https://blog.chc.ucsb.edu/?p=1590 |
| 18 | 2025-02-17 | Pessimistic MAM 2025 long-rains outlook | https://blog.chc.ucsb.edu/?p=1566 |
| 19 | 2021-03-16 | La Niña & Western V — MAM 2021 | https://blog.chc.ucsb.edu/?p=946 |
| 20 | 2025-02-07 | GHACOF69 & negative WVG MAM 2025 | https://blog.chc.ucsb.edu/?p=1516 |
| 21 | 2025-01-13 | El Niño to Early Action (preseason crop-yield) | https://blog.chc.ucsb.edu/?p=1493 |
| 22 | 2024-10-10 | Converging evidence — below-normal OND 2024 | https://blog.chc.ucsb.edu/?p=1464 |
| 23 | 2016-10-19 | Concerns about the Kenya/Somalia short rains | https://blog.chc.ucsb.edu/?p=10 |
| 24 | 2024-09-11 | Sept NMME — below-normal eHorn OND 2024 | https://blog.chc.ucsb.edu/?p=1457 |
| 25 | 2024-08-12 | August OND 2024 outlook (IWHG) | https://blog.chc.ucsb.edu/?p=1444 |
| 26 | 2024-03-24 | Southern Africa driest February on record | https://blog.chc.ucsb.edu/?p=1375 |
| 27 | 2023-10-17 | Exceptionally intense IOD & East African rains | https://blog.chc.ucsb.edu/?p=1345 |
| 28 | 2023-07-18 | Rapid El Niño & +IOD threaten E/SE Africa | https://blog.chc.ucsb.edu/?p=1272 |
| 29 | 2023-10-17 | Strong El Niño to persist through late 2023 | https://blog.chc.ucsb.edu/?p=1338 |
| 30 | 2023-08-23 | Warming world — desiccation & inundation | https://blog.chc.ucsb.edu/?p=1300 |
