# Genuinely out-of-sample block test (audit S-F4)

Search re-run on **train 1991–2009 only** (train-only SST climatology); the train-discovered winner per cell is then scored on **test 2010–2023**. Top-5 train-discovered cells per country. OOS r has a 95% bootstrap CI over the 14 test years.

| Country | Season | Zone | Train-discovered winner | train LOO r | OOS r (2010–2023) | 95% CI | n |
|---|---|---|---|---|---|---|---|
| Nigeria | JJA | Middle | atl3 | +0.74 | +0.12 | [-0.25, +0.67] | 14 |
| Nigeria | JJAS | Middle | atl3 | +0.65 | +0.22 | [-0.22, +0.73] | 14 |
| Nigeria | JJAS | National | persistence | +0.53 | -0.09 | [-0.69, +0.57] | 14 |
| Nigeria | JAS | National | persistence | +0.52 | -0.03 | [-0.39, +0.52] | 14 |
| Nigeria | JJA | National | tsa | +0.51 | +0.00 | [-0.48, +0.57] | 14 |
| Ethiopia | OND | South | wvg2 | +0.47 | +0.60 | [+0.23, +0.85] | 14 |
| Ethiopia | AMJ | South | sst_projection | +0.43 | +0.10 | [-0.28, +0.57] | 14 |
| Ethiopia | AMJ | National | sst_projection | +0.36 | +0.07 | [-0.30, +0.48] | 14 |
| Ethiopia | JAS | North | sst_projection | +0.36 | +0.43 | [-0.28, +0.89] | 14 |
| Ethiopia | AMJ | Central | sst_projection | +0.33 | +0.03 | [-0.37, +0.50] | 14 |
| Kenya | OND | South | wvg2 | +0.60 | +0.46 | [+0.18, +0.80] | 14 |
| Kenya | OND | National | wvg2 | +0.58 | +0.50 | [+0.17, +0.82] | 14 |
| Kenya | OND | North | wvg2 | +0.56 | +0.50 | [+0.15, +0.81] | 14 |
| Kenya | OND | Central | wvg2 | +0.51 | +0.51 | [+0.20, +0.82] | 14 |
| Kenya | AMJ | National | wvg2 | +0.47 | +0.10 | [-0.37, +0.61] | 14 |

**Reading.** This is the *procedure* tested out-of-sample, not pre-specified winners. Where the search's train-discovered winner is the East-African OND·IOD signal, it holds up out of sample; but every OOS r at n=14 carries a ±0.4–0.5-wide 95% CI, so an apparent in-sample→OOS *increase* is not evidence of strengthening — the CIs on in-sample and OOS overlap heavily. The honest claim is "the discovered East-African OND signal remains positive out of sample," not "it comes back stronger."
