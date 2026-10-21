"""HUNT_TIMESFM ROUND 5 evaluation: 4 pre-registered configs through the FULL V2 battery.

Grid (pre-registered, no post-hoc cells): {NKY, PROP} x {h1, h5}. Per config:
  - full admitted span + champion-window secondary span (labeled)
  - gates.run(r=per-unit, sig=held weights, leak_check=True EXPLICIT, ref=champion,
    beats_passive=True + pinned spy/ief/cta trio)  [V2 0/6/7]
  - c1 dead-family probe: agreement with naive weekly momentum
  - per-benchmark SRs published; span_class printed
Run under the SYSTEM python (no timesfm import needed — reads forecast CSVs).
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r5")
import tfm_r5_lib as L

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_TIMESFM/work_r5"
ANN = 252.0

CHAMP_PATH = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
SRC = {
    "NKY": (f"{ROOT}/tools/quant/data/newdata/NIKKEI225.csv", None),
    "PROP": (f"{ROOT}/tools/quant/data/more_fred/DPROPANEMBTX.csv", "value"),
}


def load_benchmarks():
    spy = pd.read_csv(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv")["close"]
    spy.index = pd.to_datetime(pd.read_csv(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv")["date"])
    spy = pd.to_numeric(spy, errors="coerce").dropna()
    spy = spy[~spy.index.duplicated(keep="last")].sort_index()
    SPY = spy.pct_change().rename("ret")
    ief = pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/IEF.csv")
    IEF = pd.to_numeric(ief["close"], errors="coerce").values
    IEF = pd.Series(IEF, index=pd.to_datetime(ief["date"])).dropna()
    IEF = IEF[~IEF.index.duplicated(keep="last")].sort_index().pct_change().rename("ret")
    cta = pd.read_csv(f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv")
    CTA = pd.to_numeric(cta["ret"], errors="coerce").values
    CTA = pd.Series(CTA, index=pd.to_datetime(cta["date"])).dropna().sort_index()
    return SPY, IEF, CTA


def champ():
    df = pd.read_csv(CHAMP_PATH, index_col=0, parse_dates=True)
    return df.iloc[:, 0].astype(float)


def build_config(asset, hcol, s, fcst):
    """Pre-registered pipeline: sign(m) at weekly decisions, VT frozen at decision,
    held weights over calendar, costed book + per-unit contract series."""
    r = s.pct_change()
    m = fcst[hcol] - fcst["last"]
    dec = fcst.index
    pos = pd.Series(np.sign(m.values), index=dec)
    v = L.vt_frozen(r, dec)                      # trailing-only, frozen through week
    w = L.held_weights(s.index, pos, v)
    net, rpu, sig = L.book_net(w, r)
    return pos, v, w, net, rpu, sig, r


def naive_agree(pos, s, fcst):
    """c1 dead-family probe: agreement with naive weekly momentum sign(sum of last 5 d).
    (Weekly-cadence analog of the R4 daily control.)"""
    r = s.pct_change()
    mom5 = r.rolling(5).sum()
    naive = pd.Series(np.sign(mom5.reindex(fcst.index).fillna(0.0).values), index=fcst.index)
    both = (pos != 0) & (naive != 0)
    return float((pos[both] == naive[both]).mean()) if both.any() else float("nan")


def span_class(start):
    if start < pd.Timestamp("2007-01-01"):
        return "pre2007"
    if start >= pd.Timestamp("2013-01-01"):
        return "inception_fail"
    return "2007plus"


def eval_config(asset, hcol, SPY, IEF, CTA, CH, span_lo=None, span_hi=None, tag="full"):
    src, vcol = SRC[asset]
    s = L.load_index_csv(src, vcol)
    fcst = pd.read_csv(f"{OUT}/fcst_r5_{asset}.csv", parse_dates=["date"]).set_index("date")
    if span_lo:
        s = s[s.index >= span_lo]
        fcst = fcst[fcst.index >= span_lo]
    if span_hi:
        s = s[s.index <= span_hi]
        fcst = fcst[fcst.index <= span_hi]
    pos, v, w, net, rpu, sig, r = build_config(asset, hcol, s, fcst)
    agree = naive_agree(pos, s, fcst)
    res = L.run_battery(net, rpu, sig, ref=CH, spy=SPY, ief=IEF, cta=CTA)
    g = dict(n=len(net), span_start=str(net.index[0].date()), span_end=str(net.index[-1].date()),
             span_class=span_class(net.index[0]), agree_naive=round(agree, 3),
             leak_same_corr=(res["leak"] or {}).get("same_period_corr"),
             leak_verdict=res["leak_ok"], bp_best=(res["beats_passive"] or {}).get("best_passive_sr"),
             bp_name=(res["beats_passive"] or {}).get("best_passive_name"))
    for k in ("sr", "h1", "h2", "neg_years", "worst", "corr", "scr_p", "ac1", "uniq"):
        g[k] = round(float(res[k]), 4) if res[k] is not None and np.isfinite(res[k]) else res[k]
    g["sr_ok"] = res["sr_ok"]; g["halves_ok"] = res["halves_ok"]
    g["neg_ok"] = res["neg_ok"]; g["corr_ok"] = res["corr_ok"]; g["scr_ok"] = res["scr_ok"]
    g["bp_ok"] = res["beats_passive_ok"]; g["leak_ok_"] = res["leak_ok"]
    g["PASS"] = res["pass"]
    # book ann return for context
    g["ann"] = round(float(np.prod(1 + net) ** (ANN / len(net)) - 1), 4)
    return g, net, w


def main():
    SPY, IEF, CTA = load_benchmarks()
    CH = champ()
    print(f"benchmarks: SPY n={len(SPY.dropna())} IEF n={len(IEF.dropna())} CTA n={len(CTA.dropna())}")
    print(f"champion n={len(CH)} {CH.index[0].date()}..{CH.index[-1].date()}")
    rows = []
    books = {}
    for asset in ("NKY", "PROP"):
        for hcol in ("f1", "f5"):
            g, net, w = eval_config(asset, hcol, SPY, IEF, CTA, CH)
            key = f"{asset}_{hcol}"
            rows.append((key + " [full]", g)); books[key] = net
            print(f"\n== {key} FULL admitted span ==")
            print({k: g[k] for k in ("n", "span_start", "span_end", "span_class", "sr", "h1", "h2",
                                     "neg_years", "worst", "ann", "corr", "scr_p", "ac1", "uniq",
                                     "agree_naive", "leak_same_corr", "leak_verdict",
                                     "bp_best", "bp_name", "bp_ok",
                                     "sr_ok", "halves_ok", "neg_ok", "corr_ok", "scr_ok", "PASS")})
            # champion-window secondary (benchmarks measurable; labeled secondary)
            g2, _, _ = eval_config(asset, hcol, SPY, IEF, CTA, CH,
                                   span_lo="2007-03-31", span_hi="2026-08-31", tag="champwin")
            rows.append((key + " [champwin]", g2))
            print(f"== {key} CHAMPION-WINDOW (secondary) ==")
            print({k: g2[k] for k in ("n", "span_class", "sr", "h1", "h2", "neg_years", "worst",
                                      "ann", "corr", "scr_p", "bp_ok", "bp_best", "agree_naive",
                                      "leak_verdict", "PASS")})
    import json
    with open(f"{OUT}/eval_r5_results.json", "w") as f:
        json.dump({k: v for k, v in rows}, f, indent=1, default=str)
    # save books as evidence (V2 10a: signal/positions published)
    pd.DataFrame(books).to_csv(f"{OUT}/books_r5.csv")
    print("\nsaved eval_r5_results.json + books_r5.csv")


if __name__ == "__main__":
    main()
