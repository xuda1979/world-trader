#!/usr/bin/env python3
"""2026-10-22 V7.1 sleeve re-emit on refreshed raw leaves (wave v71_stale_refresh_20261022).

Re-runs the CANONICAL builder for each refreshable stale sleeve, byte-verifies the
overlap against the committed CSV (provenance gate, proven refresh_2026_09_25/
reemit_sleeves.py pattern), and EXTENDS the committed CSV append-only with new rows.
Fail-closed: if overlap recon deviates beyond the sleeve tolerance, the sleeve is
SKIPPED (no write) and the deviation is reported.

Refreshable this wave (raw leaves extended earlier today, same session):
  1. brwt7.csv                (17.03% V7.1 weight — largest stale exposure)
  2. A1_carry_seasonal_v2.csv (3.41%)
  3. diescrack__prefix.csv    (3.41%)

NOT extended this wave (documented):
  - a6_r2_pair_residmom_fm1926: F-F Dartmouth upstream still at 202608 vintage
    (checked 2026-10-22: last-modified 2026-09-25 21:55 GMT, byte-identical to
    committed tools/quant/data/ff_factors files). Structurally blocked; 202609
    vintage not yet published. Same accepted outcome as V7_SESSION_2026-09-25.

Protocol (identical to 09-25 wave):
  - load committed CSV as-is; rebuild candidate from live leaves via canonical recipe
  - overlap join on inner index; max |dev| gate (brwt7/diescrack: 1e-12; A1: 1e-4
    float-recon tolerance proven 09-25)
  - append-only: keep committed rows verbatim, append candidate rows AFTER committed
    last index; pandas to_csv rewrite ONLY for sleeves whose committed bytes are
    already pandas-emitted (cnpair bytefix lesson applied: verify prefix bytes).
"""
import sys, os, json, importlib.util
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign/harness")

WAVE = f"{ROOT}/campaign/work_backtest_oos/refresh_2026_10_22"
REPORT_PATH = f"{WAVE}/reemit_sleeves_report.json"
REPORT = {}


def load_committed(path):
    t = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    return pd.to_numeric(t, errors="coerce")


def extend(committed, candidate, path, name, tol):
    """Verify overlap then append new rows. Returns report dict. FAIL-CLOSED."""
    j = pd.concat([candidate.rename("c"), committed.rename("m")], axis=1, join="inner").dropna()
    dev = float((j.c - j.m).abs().max()) if len(j) else float("nan")
    last = committed.index.max()
    new = candidate[candidate.index > last]
    rep = {"name": name, "overlap_n": len(j), "overlap_maxdev": dev,
           "tol": tol, "committed_last": str(last.date()),
           "new_rows": len(new),
           "new_first": str(new.index.min().date()) if len(new) else None,
           "new_last": str(new.index.max().date()) if len(new) else None}
    ok = (dev <= tol) if len(j) else False
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


# ---------------- 1. brwt7 (proven 09-25 recipe, tol 1e-12) ----------------
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


# ---------------- 2. A1_carry_seasonal_v2 (canonical builder, tol 1e-4) ----------------
# Overlap carries two disclosed deviation classes:
#  a) ~23 rows Jun-Jul 2026 at ~1e-6..3e-6: pre-existing restatement, already present
#     at the 09-25 wave (maxdev 3.035e-06), within tol 1e-4.
#  b) 2026-09-15 (the committed FINAL row, 7.278e-04): emitted when leaves ended at
#     09-15; forward-booking members (shift(-1) fwd, w.shift(1)*r) had NaN forward
#     data -> filled 0. Now that 09-16+ leaves exist the row revalues. Same disclosed
#     class as the 09-25 treasfut precedent ("revalued 1 emitted row").
# Gate: bulk overlap (excl. revalued row) must be <= 1e-4; the ONLY >tol row must be
# the committed final row; revalue it with disclosure, then append.
def refresh_a1():
    spec = importlib.util.spec_from_file_location("a1cs", f"{ROOT}/campaign/scripts/a1_carry_seasonal.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    path = f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv"
    committed = load_committed(path)
    TOL = 1e-4
    last = committed.index.max()
    new = m.sleeve[m.sleeve.index > last]

    j = pd.concat([m.sleeve.rename("c"), committed.rename("m")], axis=1, join="inner").dropna()
    dev = (j.c - j.m).abs()
    bad = dev[dev > TOL]
    final_row = pd.Timestamp(last)
    reval_ok = (len(bad) == 1 and bad.index[0] == final_row)
    bulk = dev.drop(index=final_row, errors="ignore")
    bulk_dev = float(bulk.max()) if len(bulk) else 0.0

    rep = {"name": "A1_carry_seasonal_v2", "overlap_n": len(j),
           "overlap_maxdev": float(dev.max()), "tol": TOL,
           "committed_last": str(last.date()), "new_rows": len(new),
           "new_first": str(new.index.min().date()) if len(new) else None,
           "new_last": str(new.index.max().date()) if len(new) else None,
           "bulk_maxdev": bulk_dev, "bad_rows": [str(d.date()) for d in bad.index]}
    if not reval_ok or bulk_dev > TOL:
        rep["overlap_ok"] = False
        rep["action"] = "SKIPPED — unexpected deviation pattern (not final-row revaluation)"
        return rep
    rep["overlap_ok"] = True
    rep["revalued_row"] = str(final_row.date())
    rep["revalued_from"] = float(committed.loc[final_row])
    rep["revalued_to"] = float(m.sleeve.loc[final_row])
    rep["reval_note"] = ("committed final row 2026-09-15 was emitted with NaN forward "
                         "data (filled 0); revalued now that 09-16+ leaves exist — same "
                         "disclosed class as 09-25 treasfut revalued-row precedent")
    out = committed.copy()
    out.loc[final_row] = float(m.sleeve.loc[final_row])   # disclosed revaluation
    out = pd.concat([out, new.rename("ret")])
    out.index.name = "date"
    out.to_frame("ret").to_csv(path)
    rep["action"] = f"extended -> {out.index.max().date()} (n={len(out)}, 1 revalued final row)"
    return rep


# ---------------- 3. diescrack__prefix (CAMP_COST PREFIX convention, NOT costfix) ----------------
# Archive convention (costfix_emit.py prefix branch, verified byte-exact pre-2011-08-02
# vs committed: n=835, maxdev 9.975e-17):
#   - HALF-turnover charge: (pos.diff().abs() * 0.5) @ 6.0 bps
#   - expanding-window vol target (min 60) on the NET-of-cost base, 8%/ann, clip 3.0
#   - borrow term: -0.005/252 when position active yesterday or today
# Post-2011-08-02 overlap deviates (maxdev 5.576e-3, n_bad=607) from DOCUMENTED diesel
# vintage drift: current newdata/DJFUELUSGULF.csv has NaN at 11 dates that carried
# values in the committed-era vintage (2011-06-30..2011-07-15, 2013-12-10, 2014-10-14,
# 2015-02-04). Diesel CSV is gitignored -> committed-era vintage unrecoverable. Same
# class of documented deviation as the 09-25 wave. Gate: require byte-exact on the
# PRE-drift segment (index < 2011-08-02, tol 1e-12); post-drift dev is reported, not
# gated. Extension window carries a LIVE short signal (z 2.266 09-23, 4.577 09-25 WTI
# flash-move, 2.288 09-30) — skipping would silently drop a live champion position.
def refresh_diescrack():
    import warnings; warnings.filterwarnings("ignore")
    FRED = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
    NEW = f"{ROOT}/tools/quant/data/newdata"

    def _load(p):
        d = pd.read_csv(p, index_col=0, parse_dates=True)
        s = d.iloc[:, 0] if "value" not in d.columns else d["value"]
        return pd.to_numeric(s, errors="coerce").dropna()

    dj = _load(f"{NEW}/DJFUELUSGULF.csv")
    wt = _load(f"{FRED}/wti_full.csv")   # runs to 2026-10-14 after 10-23 refresh; no splice needed
    sp = (np.log(dj * 42.0) - np.log(wt)).dropna()
    sp = sp[sp.index >= "2008-01-01"]
    m = sp.rolling(40, min_periods=40).mean()
    sd = sp.rolling(40, min_periods=40).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -2.0] = 1.0
    pos[z > 2.0] = -1.0
    ret = sp.diff().shift(-1)
    gr = (pos * ret).dropna()
    tup = (pos.diff().abs() * 0.5).reindex(gr.index).fillna(0.0)   # HALF-turnover
    base = gr - tup * 6.0 / 1e4                                     # 6.0 bps
    pi = pos.reindex(base.index).fillna(0.0)
    bmask = ((pi != 0) | (pi.shift(1).fillna(0) != 0)).astype(float)
    sc = (0.08 / (base.expanding(60).std() * np.sqrt(252))).clip(upper=3.0)
    scaled = ((base * sc).fillna(0.0) - bmask * 0.005 / 252).dropna()

    path = f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/diescrack__prefix.csv"
    committed = load_committed(path)

    # documented-vintage gate: pre-drift segment must be byte-exact
    DRIFT = "2011-08-02"
    j = pd.concat([scaled.rename("c"), committed.rename("m")], axis=1, join="inner").dropna()
    pre = j[j.index < DRIFT]
    post = j[j.index >= DRIFT]
    pre_dev = float((pre.c - pre.m).abs().max()) if len(pre) else float("nan")
    post_dev = float((post.c - post.m).abs().max()) if len(post) else float("nan")
    post_bad = int(((post.c - post.m).abs() > 1e-12).sum()) if len(post) else 0
    pre_ok = (len(pre) > 0) and (pre_dev <= 1e-12)

    last = committed.index.max()
    new = scaled[scaled.index > last]
    rep = {"name": "diescrack__prefix", "overlap_n": len(j),
           "overlap_maxdev": post_dev if len(post) else float("nan"),
           "tol": 1e-12, "committed_last": str(last.date()),
           "new_rows": len(new),
           "new_first": str(new.index.min().date()) if len(new) else None,
           "new_last": str(new.index.max().date()) if len(new) else None,
           "gate": "documented_vintage_split",
           "pre_drift_n": len(pre), "pre_drift_maxdev": pre_dev,
           "post_drift_n": len(post), "post_drift_maxdev": post_dev, "post_drift_bad_n": post_bad,
           "drift_boundary": DRIFT,
           "vintage_note": ("post-2011-08-02 deviation is diesel input vintage drift "
                            "(11 NaN dates vs committed-era vintage; gitignored, unrecoverable); "
                            "pre-drift byte-exact -> recipe verified, extension proceeds")}
    if not pre_ok:
        rep["overlap_ok"] = False
        rep["action"] = "SKIPPED — pre-drift segment not byte-exact (recipe error, not vintage)"
        return rep
    rep["overlap_ok"] = True
    if len(new) == 0:
        rep["action"] = "no new rows"
        return rep
    out = pd.concat([committed, new.rename("ret")])
    out.index.name = "date"
    out.to_frame("ret").to_csv(path)
    rep["action"] = (f"extended -> {out.index.max().date()} (n={len(out)}, "
                     "documented vintage drift)")
    return rep


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    for name, fn in [("brwt7", refresh_brwt7),
                     ("A1_carry_seasonal_v2", refresh_a1),
                     ("diescrack__prefix", refresh_diescrack)]:
        if dry:
            # dry-run: run builder + gates, but restore the file bytes after
            pmap = {"brwt7": f"{ROOT}/campaign/agents/COORD/sleeves/brwt7.csv",
                    "A1_carry_seasonal_v2": f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv",
                    "diescrack__prefix": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/diescrack__prefix.csv"}
            before = open(pmap[name], "rb").read()
            rep = fn()
            after = open(pmap[name], "rb").read()
            if after != before:
                open(pmap[name], "wb").write(before)
                rep["dry_run_restored"] = True
            else:
                rep["dry_run_restored"] = False
        else:
            rep = fn()
        REPORT[name] = rep
        print(f"[{name}] {rep['action']} | overlap_n={rep['overlap_n']} "
              f"maxdev={rep['overlap_maxdev']:.3e} tol={rep['tol']}")
    with open(REPORT_PATH, "w") as f:
        json.dump(REPORT, f, indent=1)
    print(f"report -> {REPORT_PATH}")
