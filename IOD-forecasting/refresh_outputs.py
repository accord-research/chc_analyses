"""Regenerate every published artefact for one init: CSVs, facts, and report figures."""
import warnings; warnings.filterwarnings("ignore")
import sys, json; sys.path.insert(0, ".")
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import iod_pipeline as iod, make_maps

def main(init):
    """Regenerate every artefact for one init. Called only from the command line.

    This used to run at import time with init defaulting to the first issuance.
    Importing the module for its helpers therefore re-ran that issuance and
    rewrote its published figure, which is how a report already sent out can
    silently acquire a different figure from the one it was built with.
    """
    INIT = init
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
                             calibrated_C=t.loc[w,"calibrated"],
                             raw_C=t.loc[w,"raw"],
                             anomaly_C=t.loc[w,"calibrated"]-t.loc[w,"obs_clim"],
                             ci80=t.loc[w,"ci80"], slope=t.loc[w,"slope"],
                             z_vs_training=t.loc[w,"z_vs_training"],
                             loyo_r=sk.loc[w,"model_r"],
                             persist30_r=sk.loc[w,"persist30_r"],
                             persist14_r=sk.loc[w,"persist14_r"],
                             gain30=sk.loc[w,"gain30"],
                             gain30_lo=sk.loc[w,"gain30_lo"],
                             gain30_hi=sk.loc[w,"gain30_hi"],
                             gain30_clears_zero=bool(sk.loc[w,"gain30_lo"] > 0)))
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

    # Values are written at full precision. Rounding here and again when the report is
    # written rounds twice, which moved a 0.8548 anomaly to +0.86 instead of +0.85 and
    # shifted three interval bounds. Round once, at the point of display -- report_rows()
    # below does that, and the report should copy its output rather than retype numbers.

    # ---- figure 1: outlook + the persistence sweep, not a single baseline
    # Authored at the report's text width (about 7.2 in), NOT wider. A figure drawn
    # 11 in across has to be scaled to ~0.35 to fit the page, which renders 7.5 pt
    # labels at under 3 pt. Two rows of two keeps every panel legible at close to 1:1.
    plt.rcParams.update({"font.size":8.5,"axes.spines.top":False,"axes.spines.right":False})
    x = np.arange(5)
    fig, axg = plt.subplots(2, 2, figsize=(7.2, 4.8))
    ax = axg.ravel()
    for pole, c, nm in (("wio",CW,"WIO (west)"), ("eio",CE,"EIO (east)")):
        an=[facts["poles"][pole][w][1] for w in W]; ci=[facts["poles"][pole][w][2] for w in W]
        ax[0].errorbar(x+(0.08 if pole=="eio" else -0.08), an, yerr=ci, fmt="o-", color=c,
                       lw=1.6, capsize=2.5, ms=3.5, label=nm)
    ax[0].axhline(0,color="#444",lw=.7); ax[0].set_ylabel("SST anomaly (°C)")
    ax[0].set_title("(a) Pole SST anomalies",fontsize=9,loc="left"); ax[0].legend(frameon=False,fontsize=7.6)
    d=res["dmi"]
    # Deliberately NOT the pole colours: orange/teal mean west/east in the other three
    # panels, and reusing them here for calibrated/raw made panel (b)'s orange read as
    # "the western pole".
    DMI_CAL, DMI_RAW = "#3b3b6d", "#9a9a9a"
    ax[1].errorbar(x-0.06, d["dmi_calibrated"], yerr=d["ci80"], fmt="o-", color=DMI_CAL, lw=1.6,
                   capsize=2.5, ms=3.5, label="calibrated")
    ax[1].plot(x+0.06, d["dmi_raw"], "s--", color=DMI_RAW, lw=1.3, ms=3.5, label="raw model")
    ax[1].axhline(0,color="#444",lw=.7); ax[1].set_ylabel("DMI (°C)")
    ax[1].set_title("(b) Dipole Mode Index",fontsize=9,loc="left"); ax[1].legend(frameon=False,fontsize=7.6)
    for j,(pole,c,nm) in enumerate((("WIO",CW,"(c) WIO skill"),("EIO",CE,"(d) EIO skill"))):
        s=sens.loc[pole]; a=ax[2+j]
        a.plot(x, s["model_r"], "o-", color=c, lw=1.7, ms=3.5, label="ECMWF S2S, calibrated")
        a.plot(x, s["persist30_r"], "s--", color="#6a6a6a", lw=1.3, ms=3.5, label="persistence (30 d)")
        a.plot(x, s["persist14_r"], "^:", color="#b0b0b0", lw=1.1, ms=3, label="persistence (14 d)")
        a.fill_between(x, s["persist30_r"], s["model_r"], where=(s["model_r"]>=s["persist30_r"]),
                       color=c, alpha=.13, interpolate=True)
        a.set_ylim(0,1); a.set_title(nm,fontsize=9,loc="left")
        if j==0: a.set_ylabel("LOYO correlation"); a.legend(frameon=False,fontsize=7.0,loc="lower left")
    for a in ax: a.set_xticks(x); a.set_xticklabels(LAB,fontsize=8); a.grid(axis="y",alpha=.25)
    fig.tight_layout(pad=0.6)
    fig.savefig(f"outputs/figures/fig1_combined_{INIT}.png", dpi=210, bbox_inches="tight"); plt.close(fig)

    make_maps.render(res["calibrated_fields"], f"outputs/figures/fig3_maps_{INIT}.png")
    # Per-init asset names. A weekly product regenerates these every run, and with a
    # single shared filename each run silently repointed every PREVIOUS report's
    # markdown at the newest figures -- the built PDFs were fine, but rebuilding an
    # older report would quietly have produced the wrong document.
    import shutil
    for f in ("fig1_combined", "fig3_maps"):
        shutil.copy(f"outputs/figures/{f}_{INIT}.png", f"report/assets/{f}_{INIT}.png")
    print("refreshed:", ", ".join(sorted(facts["dmi"])))
    print(idx[["index","window","valid_from","valid_to","calibrated_C","anomaly_C","ci80","loyo_r","persist30_r"]].to_string(index=False))




if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else sys.exit("usage: refresh_outputs.py <YYYY-MM-DD>"))


def refresh_alternatives(init, *, years=None, outputs="outputs"):
    """The alternative methods, plus the two diagnostics the report cites.

    interval_coverage and dispersion back numbers quoted in the report proper,
    not in the alternatives section, so they belong to any run that regenerates
    the report. They live here rather than in the main path because both refit
    the calibration many times over and the forecast does not need them.

    Kept here with the rest of the published artefacts. These were built by hand
    for the first issuance that used them, and the ARIMA dipole ended up on a
    different climatology from the other two methods in the same table because
    nothing regenerated all three together.
    """
    import pandas as pd
    import iod_pipeline as iod

    years = list(years or range(iod.BASELINE_START, iod.BASELINE_START + iod.BASELINE_YEARS))
    init = str(pd.Timestamp(init).date())

    fcst, hcst = iod.fetch_model(init)
    fw = iod.a2s.lead_window_reduce(fcst, iod.TENDENCY_WINDOWS)
    hw = iod.a2s.lead_window_reduce(hcst, iod.TENDENCY_WINDOWS)
    ow = iod.fetch_observed_windows(init, years)
    fi, hi = iod.pole_series(fw), iod.pole_series(hw)
    oi = iod.pole_series(ow, ensemble_mean=False)

    tend = []
    for pole in iod.POLES:
        t = iod.calibrate_pole_tendency(init, years, hi[pole], fi[pole], oi[pole], pole,
                                        live_year=pd.Timestamp(init).year)
        t.insert(0, "pole", pole)
        tend.append(t)
    tendency = pd.concat(tend)
    tendency.to_csv(f"{outputs}/tendency_{init}.csv")

    cmp_ = pd.concat([iod.arima_vs_model(p, years, init).assign(pole=p) for p in iod.POLES])
    cmp_.to_csv(f"{outputs}/arima_vs_model_{init}.csv")

    cov = iod.interval_coverage(init, years)
    cov.to_csv(f"{outputs}/interval_coverage_{init}.csv")
    disp = iod.dispersion(init, years)
    disp.to_csv(f"{outputs}/dispersion_{init}.csv")

    dip = iod.arima_forecast_dipole(init, years)
    rows = [dict(pole=p, window=w, **dip[p][w]) for p in iod.POLES for w in iod.WINDOWS]
    rows += [dict(pole="dmi", window=w, anomaly=dip["dmi"][w]) for w in iod.WINDOWS]
    arima = pd.DataFrame(rows).set_index(["pole", "window"])
    arima.to_csv(f"{outputs}/arima_forecast_{init}.csv")
    return dict(tendency=tendency, comparison=cmp_, arima=arima,
                coverage=cov, dispersion=disp)


def report_rows(init, *, outputs="outputs"):
    """Print the report's tables as markdown, rounded once from full precision.

    The report is written by hand, and hand-copied numbers have twice gone wrong
    here, once by rounding an already-rounded CSV value and once by retyping a
    table into a rewrite. Paste these rows instead of typing them.
    """
    import pandas as pd
    init = str(pd.Timestamp(init).date())
    W = ["week1", "week2", "week3", "week4", "day1_30"]
    LAB = {"week1": "Week 1", "week2": "Week 2", "week3": "Week 3",
           "week4": "Week 4", "day1_30": "Days 1–30"}
    sgn = lambda v, n=2: f"{v:+.{n}f}".replace("-", "−")

    idx = pd.read_csv(f"{outputs}/indices_{init}.csv")
    dmi = pd.read_csv(f"{outputs}/dmi_{init}.csv").set_index("window")
    wio = idx[idx["index"] == "WIO"].set_index("window")
    eio = idx[idx["index"] == "EIO"].set_index("window")

    print("## Results\n")
    print("| Horizon | Valid | West box | East box | Dipole |")
    print("|---|---|---|---|---|")
    for w in W:
        a, b = wio.loc[w, "valid_from"], wio.loc[w, "valid_to"]
        vf = f"{pd.Timestamp(a).day} {pd.Timestamp(a):%b} – {pd.Timestamp(b).day} {pd.Timestamp(b):%b}"
        print(f"| {LAB[w]} | {vf} "
              f"| {wio.loc[w,'calibrated_C']:.2f} °C ({sgn(wio.loc[w,'anomaly_C'])}) "
              f"| {eio.loc[w,'calibrated_C']:.2f} °C ({sgn(eio.loc[w,'anomaly_C'])}) "
              f"| {sgn(dmi.loc[w,'dmi_calibrated'])} ± {dmi.loc[w,'ci80']:.2f} |")

    sens = pd.read_csv(f"{outputs}/persistence_sensitivity_{init}.csv")
    print("\n## Accuracy\n")
    print("| | " + " | ".join(LAB[w] for w in W) + " |")
    print("|---|" + "---|" * len(W))
    for box, pole in (("West", "WIO"), ("East", "EIO")):
        s = sens[sens.pole == pole].set_index("window")
        i = (wio if pole == "WIO" else eio)
        print(f"| **{box}** forecast / persistence | " + " | ".join(
            f"{s.loc[w,'model_r']:.2f} / {s.loc[w,'persist30_r']:.2f}" for w in W) + " |")
        print("| gain | " + " | ".join(
            f"{sgn(i.loc[w,'gain30'])} ({sgn(i.loc[w,'gain30_lo'])}, {sgn(i.loc[w,'gain30_hi'])})"
            for w in W) + " |")

    cmp_ = pd.read_csv(f"{outputs}/arima_vs_model_{init}.csv")
    print("\n## ARIMA comparison\n")
    print("| | " + " | ".join(LAB[w] for w in W) + " |")
    print("|---|" + "---|" * len(W))
    for box, pole in (("West", "wio"), ("East", "eio")):
        c = cmp_[cmp_.pole == pole].set_index("window")
        cells = []
        for w in W:
            m, a = c.loc[w, "model_rmse"], c.loc[w, "arima_rmse"]
            cells.append(f"**{m:.3f}** / {a:.3f}" if m < a else f"{m:.3f} / **{a:.3f}**")
        print(f"| **{box}** forecast / ARIMA | " + " | ".join(cells) + " |")
    return None
