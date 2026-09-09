"""Regenerate every published artefact for one init: CSVs, facts, and report figures."""
import warnings; warnings.filterwarnings("ignore")
import sys, json; sys.path.insert(0, ".")
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import iod_pipeline as iod, make_maps

INIT = "2026-08-31"
CW, CE = "#c4552f", "#1f6f80"
LAB = ["W1", "W2", "W3", "W4", "D1-30"]

res = iod.run(INIT, verbose=False)
years = res["years"]
h = iod.pole_series(res["fields"]["reforecast"])
o = iod.pole_series(res["fields"]["observed"], ensemble_mean=False)
sens = iod.persistence_sensitivity(INIT, years, h, o)

W = list(iod.WINDOWS)
rows = []
for pole in iod.POLES:
    t = res["poles"][pole]; sk = sens.loc[pole.upper()]
    for w in W:
        vs, ve = iod.window_valid_dates(INIT, w)
        rows.append(dict(init=INIT, index=pole.upper(), window=w,
                         valid_from=vs.date(), valid_to=ve.date(),
                         calibrated_C=round(t.loc[w,"calibrated"],3),
                         raw_C=round(t.loc[w,"raw"],3),
                         anomaly_C=round(t.loc[w,"calibrated"]-t.loc[w,"obs_clim"],3),
                         ci80=round(t.loc[w,"ci80"],3), slope=round(t.loc[w,"slope"],3),
                         z_vs_training=round(t.loc[w,"z_vs_training"],2),
                         loyo_r=round(sk.loc[w,"model_r"],3),
                         persist30_r=round(sk.loc[w,"persist30_r"],3),
                         persist14_r=round(sk.loc[w,"persist14_r"],3),
                         gain30=round(sk.loc[w,"gain30"],3)))
idx = pd.DataFrame(rows); idx.to_csv(f"outputs/indices_{INIT}.csv", index=False)
res["dmi"].reset_index().assign(init=INIT).to_csv(f"outputs/dmi_{INIT}.csv", index=False)
sens.to_csv(f"outputs/persistence_sensitivity_{INIT}.csv")
res["calibrated_fields"].to_netcdf(f"outputs/calibrated_fields_{INIT}.nc")

facts = dict(init=INIT, years=[years[0], years[-1]], n=len(years),
             dmi={w: [round(float(res["dmi"].loc[w,"dmi_calibrated"]),2),
                      round(float(res["dmi"].loc[w,"dmi_raw"]),2),
                      round(float(res["dmi"].loc[w,"ci80"]),2)] for w in W},
             poles={p: {w: [round(float(res["poles"][p].loc[w,"calibrated"]),2),
                            round(float(res["poles"][p].loc[w,"calibrated"]-res["poles"][p].loc[w,"obs_clim"]),2),
                            round(float(res["poles"][p].loc[w,"ci80"]),2),
                            round(float(res["poles"][p].loc[w,"slope"]),2)] for w in W} for p in iod.POLES},
             sens=sens.round(3).reset_index().to_dict("records"),
             valid={w: [str(iod.window_valid_dates(INIT,w)[0].date()),
                        str(iod.window_valid_dates(INIT,w)[1].date())] for w in W})
json.dump(facts, open("outputs/report_facts.json","w"), indent=1)

# ---- figure 1: outlook + the persistence sweep, not a single baseline
plt.rcParams.update({"font.size":7.5,"axes.spines.top":False,"axes.spines.right":False})
x = np.arange(5)
fig, ax = plt.subplots(1, 4, figsize=(11.0, 2.3))
for pole, c, nm in (("wio",CW,"WIO (west)"), ("eio",CE,"EIO (east)")):
    an=[facts["poles"][pole][w][1] for w in W]; ci=[facts["poles"][pole][w][2] for w in W]
    ax[0].errorbar(x+(0.08 if pole=="eio" else -0.08), an, yerr=ci, fmt="o-", color=c,
                   lw=1.6, capsize=2.5, ms=3.5, label=nm)
ax[0].axhline(0,color="#444",lw=.7); ax[0].set_ylabel("SST anomaly (°C)")
ax[0].set_title("(a) Pole SST anomalies",fontsize=8,loc="left"); ax[0].legend(frameon=False,fontsize=6.8)
d=res["dmi"]
ax[1].errorbar(x-0.06, d["dmi_calibrated"], yerr=d["ci80"], fmt="o-", color=CE, lw=1.6,
               capsize=2.5, ms=3.5, label="calibrated")
ax[1].plot(x+0.06, d["dmi_raw"], "s--", color=CW, lw=1.3, ms=3.5, label="raw model")
ax[1].axhline(0,color="#444",lw=.7); ax[1].set_ylabel("DMI (°C)")
ax[1].set_title("(b) Dipole Mode Index",fontsize=8,loc="left"); ax[1].legend(frameon=False,fontsize=6.8)
for j,(pole,c,nm) in enumerate((("WIO",CW,"(c) WIO skill"),("EIO",CE,"(d) EIO skill"))):
    s=sens.loc[pole]; a=ax[2+j]
    a.plot(x, s["model_r"], "o-", color=c, lw=1.7, ms=3.5, label="ECMWF S2S, calibrated")
    a.plot(x, s["persist30_r"], "s--", color="#6a6a6a", lw=1.3, ms=3.5, label="persistence (30 d)")
    a.plot(x, s["persist14_r"], "^:", color="#b0b0b0", lw=1.1, ms=3, label="persistence (14 d)")
    a.fill_between(x, s["persist30_r"], s["model_r"], where=(s["model_r"]>=s["persist30_r"]),
                   color=c, alpha=.13, interpolate=True)
    a.set_ylim(0,1); a.set_title(nm,fontsize=8,loc="left")
    if j==0: a.set_ylabel("LOYO correlation"); a.legend(frameon=False,fontsize=6.3,loc="lower left")
for a in ax: a.set_xticks(x); a.set_xticklabels(LAB,fontsize=7); a.grid(axis="y",alpha=.25)
fig.tight_layout(pad=0.5)
fig.savefig("outputs/figures/fig1_combined.png", dpi=210, bbox_inches="tight"); plt.close(fig)

make_maps.render(res["calibrated_fields"], "outputs/figures/fig3_maps.png")
for f in ("fig1_combined.png","fig3_maps.png"):
    import shutil; shutil.copy(f"outputs/figures/{f}", f"report/assets/{f}")
print("refreshed:", ", ".join(sorted(facts["dmi"])))
print(idx[["index","window","valid_from","valid_to","calibrated_C","anomaly_C","ci80","loyo_r","persist30_r"]].to_string(index=False))
