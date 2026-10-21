"""HUNT_INTERNATIONAL2 ROUND 6(a) — FRAUD-CATCH cross-verification of HUNT_TIMESFM's R5
verdicts (0/4) with MY OWN battery code (tests_tdd_r6.py, 25 checks green).

Independence design:
  1. REBUILD each config's book from SOURCE returns + THEIR published signal CSV
     (decision_date/pos/vt) with MY OWN T+1 held-weights + MY OWN cost model — does their
     published `net` column reproduce? (checks the book construction, not just the metrics)
  2. MY OWN metrics (SR/halves/neg_years/ann), MY OWN leak probe, MY OWN scramble, MY OWN
     beats-passive trio on the rebuilt book.
  3. THEIR published sleeve CSV columns (w/rpu/net) re-metric'd directly (artifact-level).
  4. Cross-reference re-run of bt.gates.run (clearly labeled; the charter wants MY battery
     to be the judge — the bt re-run is only a tiebreaker on any mismatch).
  5. PIT spot-check of their forecast artifact: f_t must not correlate with the target's
     SAME-PERIOD return more than with its own decision-day close (leak-shaped evidence).

Exit 0 = all four verdicts MATCH; exit 1 = MISMATCH (escalate).
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_INTERNATIONAL2")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

import HUNT_INTL2_round6_lib as L

ROOT = "/Users/daxu/software/world-trader"
TM = f"{ROOT}/campaign/agents/chief/coord/HUNT_TIMESFM"
ANN = 252.0

SRC = {
    "NKY": (f"{ROOT}/tools/quant/data/newdata/NIKKEI225.csv", None),
    "PROP": (f"{ROOT}/tools/quant/data/more_fred/DPROPANEMBTX.csv", "value"),
}
CHAMP_PATH = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

# published verdicts (work_r5/eval_r5_results.json) — what I am fraud-catching
PUBLISHED = {
    "NKY_f1": dict(full=dict(sr=0.0284, h1=0.6555, h2=-0.3527, neg_years=36.0, corr=-0.0374,
                             scr_p=0.945, bp_best=0.2801, bp_ok=False, leak_ok=True, PASS=False),
                   champwin=dict(sr=-0.4439, h1=-0.6486, h2=-0.2223, neg_years=15.0, corr=-0.0367,
                                 scr_p=0.835, bp_best=0.5336, bp_ok=False, leak_ok=True, PASS=False)),
    "NKY_f5": dict(full=dict(sr=0.0184, h1=0.4951, h2=-0.2715, neg_years=37.0, corr=-0.0256,
                             scr_p=0.87, bp_best=0.2801, bp_ok=False, leak_ok=True, PASS=False),
                   champwin=dict(sr=-0.3845, h1=-0.6013, h2=-0.1496, neg_years=13.0, corr=-0.0258,
                                 scr_p=0.855, bp_best=0.5336, bp_ok=False, leak_ok=True, PASS=False)),
    "PROP_f1": dict(full=dict(sr=0.4548, h1=0.5812, h2=0.3258, neg_years=10.0, corr=-0.0253,
                              scr_p=0.555, bp_best=0.5643, bp_name="spy_bh", bp_ok=False, leak_ok=True, PASS=False),
                    champwin=dict(sr=0.3865, h1=0.3726, h2=0.4004, neg_years=7.0, corr=-0.0215,
                                  scr_p=0.64, bp_best=0.5839, bp_ok=False, leak_ok=True, PASS=False)),
    "PROP_f5": dict(full=dict(sr=0.2828, h1=0.1905, h2=0.3769, neg_years=11.0, corr=-0.0193,
                              scr_p=0.585, bp_best=0.5643, bp_ok=False, leak_ok=True, PASS=False),
                    champwin=dict(sr=0.2776, h1=0.1375, h2=0.4171, neg_years=6.0, corr=-0.0165,
                                  scr_p=0.62, bp_best=0.5839, bp_ok=False, leak_ok=True, PASS=False)),
}

MISMATCH = []
MATCH = 0


def load_close(path, vcol=None):
    """Own loader: drop NaN/nonpositive, dedupe keep-last, sort. (Their L.load_index_csv
    semantics — re-implemented, not imported.)"""
    df = pd.read_csv(path)
    dcol = df.columns[0]
    v = pd.to_numeric(df[vcol or df.columns[1]], errors="coerce")
    dt = pd.to_datetime(df[dcol])
    ok = v.notna() & (v > 0)
    s = pd.Series(v[ok].values, index=dt[ok])
    return s[~s.index.duplicated(keep="last")].sort_index().astype(float)


def load_benchmarks():
    # SPY is an OHLCV file: the close column must be selected EXPLICITLY (the default
    # second-column heuristic is only valid for [date, close] files; first draft of this
    # audit grabbed 'open' — caught by the bp_best mismatch this audit exists to run down).
    spy = load_close(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv", vcol="close")
    ief = load_close(f"{ROOT}/tools/quant/data/more_etf/IEF.csv")
    cta = pd.read_csv(f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv")
    CTA = pd.to_numeric(cta["ret"], errors="coerce")
    CTA.index = pd.to_datetime(cta["date"])
    return spy.pct_change(), ief.pct_change(), CTA.dropna().sort_index()


def champ():
    df = pd.read_csv(CHAMP_PATH, index_col=0, parse_dates=True)
    return df.iloc[:, 0].astype(float)


def compare(label, mine, pub, tol_sr=0.01, tol_other=0.01, key_pass=True):
    global MATCH
    bad = []
    for k, tol in (("sr", tol_sr), ("h1", 0.01), ("h2", 0.01), ("neg_years", 0.0),
                   ("corr", 0.005), ("scr_p", 0.01), ("bp_best", 0.01)):
        m, p = mine.get(k), pub.get(k)
        ok = (np.isfinite(m) and np.isfinite(p) and abs(m - p) <= tol) if isinstance(p, float) \
            else (m == p)
        if not ok:
            bad.append(f"{k}: mine={m} pub={p}")
    for k in ("bp_ok", "leak_ok", "PASS"):
        if bool(mine.get(k)) != bool(pub.get(k)):
            bad.append(f"{k}: mine={mine.get(k)} pub={pub.get(k)}")
    if bad:
        MISMATCH.append((label, bad))
        print(f"  MISMATCH {label}: {'; '.join(bad)}")
        return False
    MATCH += 1
    print(f"  MATCH {label} (SR mine {mine['sr']:.4f} vs pub {pub['sr']:.4f}; "
          f"negyr {mine['neg_years']:.0f} vs {pub['neg_years']:.0f}; "
          f"scr_p {mine['scr_p']:.3f} vs {pub['scr_p']:.3f}; PASS both {pub['PASS']})")
    return True


def audit_config(asset, hcol, span_lo=None, span_hi=None, tag="full"):
    """Rebuild + re-evaluate one published config on one span.

    Span convention (THEIRS, documented in eval_r5.py): a truncated span REBUILDS the
    pipeline on the truncated data — VT expanding warmup restarts at the cut (verified:
    1013/1013 decisions differ from a slice of the full-span VT). For `full` the rebuild
    must reproduce their published signal CSV exactly; for `champwin` (no sleeve CSV
    published) the rebuild uses my own vt_frozen_own on the truncated span, mirroring
    their eval_config truncation-before-build_config."""
    print(f"\n== {asset}_{hcol} [{tag}] ==")
    s = load_close(*SRC[asset])
    fcst = pd.read_csv(f"{TM}/work_r5/fcst_r5_{asset}.csv", parse_dates=["date"]).set_index("date")
    sig_path = f"{TM}/sleeves/TIMESFM_R5_{asset}_{hcol}_signal.csv"
    if span_lo:
        s = s[s.index >= span_lo]
        fcst = fcst[fcst.index >= span_lo]
    if span_hi:
        s = s[s.index <= span_hi]
        fcst = fcst[fcst.index <= span_hi]
    r = s.pct_change()

    # -- (1) REBUILD the book from source returns + the published pipeline --------------
    pos_fc = L.pos_from_forecast(fcst, hcol)             # MY OWN pos builder
    v = L.vt_frozen_own(r, fcst.index)                   # MY OWN VT (truncated-span warmup)
    w = L.held_weights_own(s.index, pos_fc, v)           # MY OWN T+1 held weights
    net, rpu = L.book_net_own(w, r)                      # MY OWN cost model
    # independent check: on `full`, my rebuilt positions must equal THEIR published signal
    pos_pub = None
    pos_agree = float("nan")
    try:
        sig_pub = pd.read_csv(sig_path, parse_dates=["decision_date"]).set_index("decision_date")
        if span_hi:
            sig_pub = sig_pub[sig_pub.index <= span_hi]
        if span_lo:
            sig_pub = sig_pub[sig_pub.index >= span_lo]
        pos_pub = sig_pub["pos"]
        pos_fc_al = pos_fc.reindex(pos_pub.index)
        pos_agree = float((pos_fc_al.fillna(0) == pos_pub.fillna(0)).mean())
    except FileNotFoundError:
        pass
    # published artifact net column, aligned (full span only — none published for champwin)
    art_path = f"{TM}/sleeves/TIMESFM_R5_{asset}_{hcol}_daily.csv"
    dev = float("nan")
    sr_pub_cols = float("nan")
    try:
        dcol = "observation_date" if asset == "NKY" else "date"
        art = pd.read_csv(art_path, parse_dates=[dcol]).set_index(dcol)
        if span_hi:
            art = art[art.index <= span_hi]
        if span_lo:
            art = art[art.index >= span_lo]
        art = art.reindex(w.index)
        net_pub = art["net"]
        both = w.abs() > 0
        dev = float((net[both] - net_pub[both]).abs().max())
        # artifact-level metrics (their columns, MY metrics)
        sr_pub_cols = L.sr_d(art["w"] * art["rpu"])
    except FileNotFoundError:
        pass

    # -- (2) MY OWN battery on the REBUILT book ----------------------------------------
    SPY, IEF, CTA = load_benchmarks()
    CH = champ()
    res = L.run_battery_own(rpu=rpu, sig=w, ref=CH.reindex(rpu.index), spy=SPY, ief=IEF,
                            cta=CTA, scramble_n=200, seed=0)
    res["ann"] = float(np.prod(1 + net) ** (ANN / len(net)) - 1)
    res["neg_years"] = float(res["neg_years"])
    res["pos_agree"] = pos_agree
    res["net_dev_max_active"] = dev
    res["sr_from_pub_cols"] = sr_pub_cols

    print(f"  rebuild: pos agreement mine-vs-pub {pos_agree:.4f}; |net_dev| max on active days "
          f"{dev:.3e}; SR(their w*rpu cols, my metrics) {sr_pub_cols:.4f}")
    lp = res["leak"]
    print(f"  my battery: SR {res['sr']:.4f} H1 {res['h1']:.4f} H2 {res['h2']:.4f} "
          f"negyr {res['neg_years']:.0f} worst {res['worst']:.4f} corr {res['corr']:.4f} "
          f"scr_p {res['scr_p']:.3f} bp_best {res['bp_best']:.4f} ({res['bp_name']}) "
          f"leak corr {lp['same_period_corr']:.4f} leak_ok {res['leak_ok']} PASS {res['pass']}")

    pub = PUBLISHED[f"{asset}_{hcol}"][tag]
    ok = compare(f"{asset}_{hcol} [{tag}]", res, pub)

    # -- (5) PIT spot-check of the forecast artifact ------------------------------------
    # f_t is a forecast of the close D_{j+h}; a leak would show up as corr(m, r over the
    # SAME window the forecast targets) being enormous AND lag-0-peaked vs the decision
    # window. Check corr(m_j, forward return of the target window) vs corr(m_j, past week).
    m = (fcst[hcol] - fcst["last"]).dropna()
    fwd1 = r.reindex(m.index).shift(-1)             # next day after decision
    past5 = r.rolling(5).sum().reindex(m.index)     # the week ENDING at the decision
    c_fwd = float(pd.concat([m, fwd1], axis=1).dropna().corr().iloc[0, 1])
    c_past = float(pd.concat([m, past5], axis=1).dropna().corr().iloc[0, 1])
    print(f"  PIT: corr(m, next-day ret) {c_fwd:+.4f} vs corr(m, past-week ret) {c_past:+.4f} "
          f"({'suspicious' if abs(c_fwd) > 0.5 else 'normal'})")
    res["pit_fwd"] = c_fwd
    res["pit_past"] = c_past
    return ok, res


def bt_crossref(asset, hcol, span_lo=None, span_hi=None):
    """Clearly-labeled cross-reference: THEIR eval pipeline re-run through bt.gates.run.
    NOT my primary judge — only consulted if my own battery disagrees with the published
    numbers (then the question is 'who is right', and bt is the third opinion)."""
    from bt import gates as G
    s = load_close(*SRC[asset])
    fcst = pd.read_csv(f"{TM}/work_r5/fcst_r5_{asset}.csv", parse_dates=["date"]).set_index("date")
    if span_lo:
        s, fcst = s[s.index >= span_lo], fcst[fcst.index >= span_lo]
    if span_hi:
        s, fcst = s[s.index <= span_hi], fcst[fcst.index <= span_hi]
    r = s.pct_change()
    pos = L.pos_from_forecast(fcst, hcol)
    dec = fcst.index
    v = L.vt_frozen_own(r, dec)
    w = L.held_weights_own(s.index, pos, v)
    net, rpu = L.book_net_own(w, r)
    SPY, IEF, CTA = load_benchmarks()
    CH = champ()
    res = G.run(rpu.dropna(), ref=CH.reindex(rpu.dropna().index),
                sig=w.reindex(rpu.dropna().index), leak_check=True, beats_passive=True,
                spy=SPY, ief=IEF, cta=CTA, scramble_n=200)
    return res


def main():
    print("vintage pins (round-start, must match the metas):")
    import hashlib
    for p in (f"{ROOT}/tools/quant/data/newdata/NIKKEI225.csv",
              f"{ROOT}/tools/quant/data/more_fred/DPROPANEMBTX.csv",
              CHAMP_PATH):
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
        print(f"  {h}  {p}")
    results = {}
    all_ok = True
    for asset in ("NKY", "PROP"):
        for hcol in ("f1", "f5"):
            ok_f, res_f = audit_config(asset, hcol, tag="full")
            ok_c, res_c = audit_config(asset, hcol, span_lo="2007-03-31", span_hi="2026-08-31",
                                       tag="champwin")
            results[f"{asset}_{hcol}"] = dict(full=res_f, champwin=res_c)
            all_ok &= ok_f and ok_c
    print("\n==== SUMMARY ====")
    print(f"{MATCH}/8 published rows reproduced; mismatches: {len(MISMATCH)}")
    for lab, bad in MISMATCH:
        print(f"  ESCALATE {lab}: {bad}")
    with open(f"{ROOT}/campaign/agents/chief/coord/HUNT_INTERNATIONAL2/work_r6/fraudcatch_r6.json", "w") as f:
        json.dump(results, f, indent=1, default=str)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
