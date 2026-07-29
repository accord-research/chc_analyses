# Skill and accuracy vs lead for the selected configuration, per target (AGUv1)

Selection metric (from `metric_selection.md`): **`pearson_r`**, usefulness threshold **0.3**. *Realizable* = best GCM-MOS config at that lead; *SST benchmark* = perfect-prognosis obs-SST (a reference, **not** an upper bound — a dynamical precip forecast can and here does exceed it). **COF lead** = the longest lead at which realizable skill still clears the threshold; **issue-by** = the calendar month that lead implies.

| target | season | COF lead (months) | issue outlook by | peak realizable skill |
|---|---|---:|---|---:|
| Kenya:MAM | MAM | 0 | Mar | 0.358 |
| Kenya:OND | OND | 4 | Jun | 0.66 |
| Somalia:MAM | MAM | 3 | Dec | 0.324 |
| Somalia:SON | SON | 4 | May | 0.641 |

**Reading.** For the selected configuration, this reports how skill and accuracy vary with lead — including the longest lead at which skill still clears a usefulness threshold (one operational reading is the latest date by which an outlook could be issued). A target whose skill never clears the threshold is one where a confident seasonal forecast is not statistically supported at these leads.
