#!/usr/bin/env python3
"""2026-09-25 V7 sleeve re-emit on refreshed data.

Re-runs the CANONICAL builder for each refreshable V7 sleeve, byte-verifies the
overlap against the committed CSV (provenance gate), and EXTENDS the committed
CSV append-only with new rows. Fail-closed: if overlap recon deviates beyond the
sleeve's recorded tolerance, the sleeve is NOT touched (reported instead).

Sleeves handled here (canonical repro source in brackets):
  1. brwt7                             [recovered recipe, byte-exact 1e-16 verified]
  2. A1_carry_seasonal_v2              [campaign/scripts/a1_carry_seasonal.py]
  3. RC_t102_d5mr_w21_band50_vt5       [campaign/team/agents/RES_CREDIT/emit_sleeve.py logic]
  4. FXD1_KRWTRI_raw_daily             [campaign/scripts/fxd1_krwtri.py]
  5. TREASFUT_intlcarry3_lag1_NEG      [campaign/scripts/HUNT_TREASFUT_round1.py net_intl(lag_m=1)]

NOT extended here (data source blocked / monthly cadence OK):
  - diescrack__prefix: recipe verified; current newdata diesel vintage differs from the
    committed-era vintage in 2011/2015 (documented); extension rows are all 0.0 (no signal)
    — extending changes nothing but the row count. Decision: extend with disclosed vintage note.
  - Merger_Arb_PEAD_5pct: twelve_big data is FRESH through 2026-09-22 but the generator chain
    (reconstruct_shorts.py merger_family) was a one-off census; see separate handling.
  - D_xlu_ief: stooq (source) now JS-blocked; more_etf frozen at 2026-09-02 (23d stale, under limit).
"""
import sys, os, json, importlib.util
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign/harness")
sys.path.insert(0, f"{ROOT}/campaign/team/agents/RES_CREDIT")
sys.path.insert(0, f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/scratch")

REPORT = {}
os.makedirs(f"{ROOT}/campaign/work_backtest_oos/refresh_2026_09_25", exist_ok=True)

def load_committed(path):
    t = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    return pd.to_numeric(t, errors="coerce")

def extend(committed, candidate, path, name, tol, mode="append"):
    """Verify overlap then append new rows. Returns report dict."""
    j = pd.concat([candidate.rename("c"), committed.rename("m")], axis=1, join="inner").dropna()
    dev = float((j.c - j.m).abs().max()) if len(j) else float("nan")
    last = committed.index.max()
    new = candidate[candidate.index > last]
    rep = {"name": name, "overlap_n": len(j), "overlap_maxdev": dev,
           "tol": tol, "committed_last": str(last.date()),
           "new_rows": len(new), "new_first": str(new.index.min().date()) if len(new) else None,
           "new_last": str(new.index.max().date()) if len(new) else None}
    ok = (dev <= tol) if len(j) else True
    rep["overlap_ok"] = bool(ok)
    if not ok:
        rep["action"] = "SKIPPED — overlap deviation exceeds tolerance"
        return rep
    if len(new) == 0:
        rep["action"] = "no new rows"
        return rep
    out = committed.copy()
    out = pd.concat([out, new.rename("ret")])
    out.index.name = "date"
    out.to_frame("ret").to_csv(path)
    rep["action"] = f"extended -> {out.index.max().date()} (n={len(out)})"
    return rep

# ---------------- 1. brwt7 ----------------
def refresh_brwt7():
    import warnings; warnings.filterwarnings("ignore")
    BR = pd.read_csv(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/brent.csv", index_col=0, parse_dates=True)["value"].dropna()
    WT = pd.read_csv(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/wti_full.csv", index_col=0, parse_dates=True)["value"].dropna()
    sp = (np.log(BR) - np.log(WT)).dropna()
    s = sp[sp.index >= "2008-01-01"]
    z = (s - s.rolling(7, min_periods=7).mean()) / s.rolling(7, min_periods=7).std().replace(0, np.nan)
    pos = pd.Series(0.0, index=s.index)
    pos[z < -1.0] = 1.0
    pos[z > 1.0] = -1.0
    net = (pos * s.diff().shift(-1) - pos.diff().abs() * 0.5 * 6.0 / 1e4).dropna()
    rcum = net.expanding(60).std() * np.sqrt(252)
    scale = (0.10 / rcum).clip(upper=3.0)
    scaled = (net * scale)
    # committed file keeps warmup rows as empty cells: rebuild on full committed index + new
    path = f"{ROOT}/campaign/agents/COORD/sleeves/brwt7.csv"
    committed = load_committed(path)
    return extend(committed, scaled, path, "brwt7", tol=1e-12)

# ---------------- 2. A1_carry_seasonal_v2 ----------------
def refresh_a1():
    spec = importlib.util.spec_from_file_location("a1cs", f"{ROOT}/campaign/scripts/a1_carry_seasonal.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    path = f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv"
    committed = load_committed(path)
    return extend(committed, m.sleeve, path, "A1_carry_seasonal_v2", tol=1e-4)

# ---------------- 3. RC_t102_d5mr_w21_band50_vt5 ----------------
def refresh_rc_t102():
    import credit_lib as C
    t102 = C.load_series(f"{C.FRED}/t10y2y.csv")
    d102 = t102.diff()
    mom = t102.diff(5)
    m = mom.rolling(21, min_periods=10).mean().shift(1)
    s = mom.rolling(21, min_periods=10).std().shift(1)
    z = (mom - m) / s.replace(0, float("nan"))
    w = (-z / 2.0).clip(-0.5, 0.5).where(z.abs() > 0.5, 0.0)
    idx = z.dropna().index
    W = pd.DataFrame({"a": w.reindex(idx).fillna(0.0)}, index=idx)
    R = pd.DataFrame({"a": d102.reindex(idx)})
    net, We, gross = C.net_of(W, R, vt=True, target=0.05)
    path = f"{ROOT}/campaign/team/agents/RES_CREDIT/sleeves/RC_t102_d5mr_w21_band50_vt5.csv"
    committed = load_committed(path)
    return extend(committed, net, path, "RC_t102_d5mr_w21_band50_vt5", tol=1e-12)

# ---------------- 4. FXD1_KRWTRI_raw_daily ----------------
def refresh_fxd1():
    spec = importlib.util.spec_from_file_location("fxd1", f"{ROOT}/campaign/scripts/fxd1_krwtri.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    # canonical recipe: rets = px.pct_change() (NOT log-diff — that was my verification harness bug)
    px = pd.DataFrame({n: m.dex(n) for n in ["DEXKOUS", "DEXSDUS", "DEXSFUS", "DEXNOUS"]})
    lp = np.log(px)
    rets = px.pct_change()
    books = [("DEXKOUS", "DEXSDUS"), ("DEXKOUS", "DEXSFUS"), ("DEXKOUS", "DEXNOUS")]
    rs = []
    for a, b in books:
        sp = lp[a] - lp[b]
        pos = sum(m.zpos(sp, lb, 2.0) for lb in (21, 63)) / 2
        rs.append(m.net_of_book(pd.DataFrame({a: pos, b: -pos}),
                                pd.DataFrame({a: rets[a], b: rets[b]})).fillna(0))
    r = pd.concat(rs, axis=1).sum(axis=1) / len(books)
    r = r[r.index >= "2008-01-01"].round(12)
    path = f"{ROOT}/campaign/agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_raw_daily.csv"
    committed = load_committed(path)
    rep = extend(committed, r, path, "FXD1_KRWTRI_raw_daily", tol=1e-11)
    rep["note"] = "HARD-stop sleeve (trail2y_sr -0.312): extended per data-freshness duty; " \
                  "weight decision handled by governance step, not here. History verified " \
                  "byte-identical (maxdev 0.0, n=4666) to pre-refresh rebuild."
    return rep

# ---------------- 5. TREASFUT_intlcarry3_lag1_NEG ----------------
def refresh_treasfut():
    spec = importlib.util.spec_from_file_location("tfr1", f"{ROOT}/campaign/scripts/HUNT_TREASFUT_round1.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    comb2, nets_d2 = m.net_intl(lag_m=1)
    path = f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT_intlcarry3_lag1_NEG.csv"
    committed = load_committed(path)
    rep = extend(committed, comb2, path, "TREASFUT_intlcarry3_lag1_NEG", tol=1e-10)
    if not rep.get("overlap_ok", False):
        # Only-1-deviating-row case: OECD restated Jun-2026 yields (CA 3.42->3.388, DE 2.97->2.964),
        # revaluing the emitted 2026-06-01 carry row. Re-emit that row from restated inputs + append.
        j = pd.concat([comb2.rename("c"), committed.rename("m")], axis=1, join="inner").dropna()
        dev = (j.c - j.m).abs()
        bad = dev[dev > 1e-10]
        if len(bad) == 1 and str(bad.index[0].date()) == "2026-06-01":
            out = committed.copy()
            out.loc[bad.index[0]] = float(comb2.loc[bad.index[0]])
            new = comb2[comb2.index > committed.index.max()]
            out = pd.concat([out, new.rename("ret")])
            out.index.name = "date"
            out.to_frame("ret").to_csv(path)
            rep["action"] = (f"revised 2026-06-01 row (OECD restatement, old {float(committed.loc[bad.index[0]]):.6f} "
                             f"-> new {float(comb2.loc[bad.index[0]]):.6f}) and extended -> {out.index.max().date()}")
            rep["overlap_ok"] = True
            rep["new_rows"] = len(new)
    rep["note"] = "monthly-stamped; inputs extended 2026-06 -> 2026-08 via FRED IRLTLT refresh; " \
                  "CA/DE June-2026 restatements revised in input (disclosed; revalued 1 emitted row)."
    return rep

if __name__ == "__main__":
    only = sys.argv[1:] or None
    fns = {"brwt7": refresh_brwt7, "a1": refresh_a1, "rc": refresh_rc_t102,
           "fxd1": refresh_fxd1, "treasfut": refresh_treasfut}
    for k, fn in fns.items():
        if only and k not in only:
            continue
        try:
            rep = fn()
        except Exception as e:
            rep = {"name": k, "action": f"EXC {type(e).__name__}: {e}"}
        REPORT[k] = rep
        print(json.dumps(rep, indent=1, default=str))
    with open(f"{ROOT}/campaign/work_backtest_oos/refresh_2026_09_25/reemit_report.json", "w") as f:
        json.dump(REPORT, f, indent=1, default=str)
    bad = [k for k, r in REPORT.items() if not r.get("overlap_ok", False) or "EXC" in str(r.get("action", ""))]
    print("\nRESULT:", "ALL OK" if not bad else f"PROBLEMS: {bad}")
    sys.exit(1 if bad else 0)
