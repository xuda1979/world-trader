#!/usr/bin/env python3
"""DATA_ETF_MORE round-5: extend the ETF overlay bench for the V2 §8 blend battery.

Charter (a): the pinned spy/ief/cta trio is the minimum; add 1-2 DECORRELATED
PASSIVE benches from keyless sources. No signal hunting: this module only
  1. verifies the §7c pins (trio files byte-identical to the R2-R4 vintage),
  2. lints a pre-registered a-priori candidate list fail-closed (R3 gates),
  3. measures daily-return correlations on COMMON dates only (no fill-forward,
     no synthetic alignment) vs each trio member and the champion of record,
  4. selects <=2 benches by the pre-registered rule (see test_bench_r5 docstring),
  5. writes a deterministic (byte-stable) manifest pinning vintage sha256.

NOT done here, on purpose: no sleeve construction, no gates.run candidate
battery, no blend performance numbers. Consumption is smoke-tested only
(T8): the trio evaluates through bt.beats_passive and a selected bench is
mechanically compatible with bt.blend.blend_nets.
"""
from __future__ import annotations

import hashlib
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{ROOT}/campaign/bt")  # engine ANN only for span math; no gates run

OUT_DIR = f"{ROOT}/tools/quant/data/bench_r5"
MANIFEST = f"{OUT_DIR}/manifest.csv"

CHAMPION_PATH = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

# §7c pins — never re-fetched, only verified byte-identical.
TRIO = [
    ("SPY", f"{ROOT}/tools/quant/data/twelvedata/SPY.csv", "price", "twelvedata(R2 vintage, pinned)"),
    ("IEF", f"{ROOT}/tools/quant/data/more_etf/IEF.csv", "price", "more_etf(R2 vintage, pinned)"),
    ("CTA_15vol", f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv", "ret_curve",
     "sleeve_library(R2 vintage, pinned)"),
]

# Pre-registered a-priori candidate list (decorrelation plausible by asset class).
# TIP deliberately included as a control expected to FAIL the corr gate (rates beta).
CANDIDATES = ["GLD", "SLV", "IAU", "DBC", "GSG", "UUP", "TIP"]
CAND_SOURCE = {c: "more_etf(R2-R4 vintage)" for c in CANDIDATES}

MIN_COMMON_OBS = 1008       # 4y of daily overlap before a corr is measurable
CORR_TRIO_MAX = 0.5         # |corr| vs every trio member must be <= this
MIN_SPAN_YEARS = 8.0        # R4 TimesFM span-gate generalization
PAIR_CORR_MAX = 0.7         # mutual-decorrelation cap between selected benches

R4_FRESH_DAYS = 365 * 3 + 92


# --------------------------------------------------------------------- loading
def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_px(path: str) -> pd.Series:
    """more_etf price convention: [date,close], ascending, unique, positive."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df.set_index("date")["close"], errors="coerce").dropna()
    return s[s > 0][~s.index.duplicated(keep="last")].sort_index()


def load_ret(path: str) -> pd.Series:
    """sleeve-library convention: [date,ret], pass-through (NOT re-differenced)."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df.set_index("date")["ret"], errors="coerce").dropna()
    return s[~s.index.duplicated(keep="last")].sort_index()


def load_any(path: str, lint_mode: str) -> pd.Series:
    return load_px(path) if lint_mode == "price" else load_ret(path)


def load_champion() -> pd.Series:
    return load_ret(CHAMPION_PATH)


# ------------------------------------------------------------------------ lint
def classify(start: pd.Timestamp) -> str:
    if start <= pd.Timestamp("2007-01-01"):
        return "pre2007"
    if start <= pd.Timestamp("2013-01-01"):
        return "2007plus"
    return "inception_fail"


def lint_price(df: pd.DataFrame):
    """R3/R4 fail-closed lint, unchanged semantics. (status, span_class, metrics)."""
    r = dict(n=len(df), start="", end="", maxgap=0, zrun=0, jumps=0, dups=0)
    try:
        s = df.set_index("date")["close"].astype(float).sort_index()
        s = s[s > 0]
        n = len(s)
        r.update(n=n, start=str(s.index[0].date()), end=str(s.index[-1].date()))
        dups = int(s.index.duplicated().sum())
        gaps = s.index.to_series().diff().dt.days.dropna()
        mg = int(gaps.max())
        jr = int((s.pct_change().abs() > 0.5).sum())
        d = s.diff()
        zrun = int((d == 0).groupby((d != 0).cumsum()).cumsum().max())
        r.update(maxgap=mg, zrun=zrun, jumps=jr, dups=dups)
        if n < 250:
            return "FAIL(short)", classify(s.index[0]), r
        if dups > 0:
            return "FAIL(dup)", classify(s.index[0]), r
        if mg > 10:
            return "FAIL(gap)", classify(s.index[0]), r
        if jr > 0:
            return "FAIL(jumps)", classify(s.index[0]), r
        if (pd.Timestamp("2026-09-01") - s.index[-1]).days > R4_FRESH_DAYS:
            return "FAIL(stale)", classify(s.index[0]), r
        cls = classify(s.index[0])
        if cls == "inception_fail":
            return "FAIL(inception)", cls, r
        return ("PASS" if cls == "pre2007" else "PASS_WAIVER"), cls, r
    except Exception as e:
        return f"FAIL(read) {repr(e)[:50]}", "", r


# ------------------------------------------------------------------ correlating
def to_daily_ret(s: pd.Series, lint_mode: str) -> pd.Series:
    """Price series -> pct_change; return curve -> PASS-THROUGH.

    Re-differencing a return curve is the R3 beats_passive real-data bug class
    (SPY returns named 'close' were re-differenced -> SR 0.000): a [date,ret]
    series must never be pct_change'd, and pct_change of a 0.0 return is NaN
    (0/0), which silently poisons the overlap. The convention travels WITH the
    series, exactly as the manifest's px_convention column records it."""
    s = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
    return s.pct_change().dropna() if lint_mode == "price" else s


def corr_common(a: pd.Series, b: pd.Series, mode_a: str = "price",
                mode_b: str = "price") -> tuple:
    """Pearson corr of daily returns on COMMON dates only. No fill, no pad.

    Returns (corr, n_common); (nan, n) when overlap < MIN_COMMON_OBS — a
    correlation measured on a shorter overlap is treated as unmeasurable,
    fail-closed, not silently computed on a thin window."""
    ra = to_daily_ret(a, mode_a)
    rb = to_daily_ret(b, mode_b)
    j = pd.concat([ra, rb], axis=1, join="inner").dropna()
    if len(j) < MIN_COMMON_OBS:
        return (float("nan"), len(j))
    return (float(j.iloc[:, 0].corr(j.iloc[:, 1])), len(j))


def pair_corr(sym_a: str, sym_b: str) -> float:
    """Mutual corr of two manifest-selected benches (via their recorded paths)."""
    mf = _committed()
    pa = mf[mf.symbol == sym_a].iloc[0]
    pb = mf[mf.symbol == sym_b].iloc[0]
    a = load_any(pa.path, pa.lint_mode)
    b = load_any(pb.path, pb.lint_mode)
    c, _ = corr_common(a, b, pa.lint_mode, pb.lint_mode)
    return c


# --------------------------------------------------------------- measurement
def measure_candidates(force_frames: dict | None = None) -> pd.DataFrame:
    """Lint + measure every CANDIDATE against each trio member and the champion.

    force_frames: test hook to inject a fabricated frame under a fake symbol
    (fail-closed path coverage). Real candidates always read from disk pins."""
    trio_series = [(n, load_any(p, m), m) for n, p, m, _ in TRIO]
    champ = load_champion()
    rows = []
    cands = list(CANDIDATES)
    if force_frames:
        cands = cands + [s for s in force_frames if s not in CANDIDATES]
    for sym in cands:
        if force_frames and sym in force_frames:
            df = force_frames[sym]
            path = f"<forced:{sym}>"
        else:
            path = f"{ROOT}/tools/quant/data/more_etf/{sym}.csv"
            if not os.path.exists(path):
                rows.append(_row(sym, path, "FAIL(missing)", "", dict(n=0)))
                continue
            df = pd.read_csv(path)
            df["date"] = pd.to_datetime(df["date"])
        st, cls, m = (lint_price(df) if not (force_frames and sym in force_frames)
                      else lint_price(force_frames[sym]))
        row = _row(sym, path, st, cls, m)
        if st.startswith("PASS"):
            s = load_px(path) if not (force_frames and sym in force_frames) \
                else force_frames[sym].set_index("date")["close"].sort_index()
            span_y = (s.index[-1] - s.index[0]).days / 365.25
            row["span_years"] = round(span_y, 2)
            if span_y < MIN_SPAN_YEARS:
                row["note"] = f"span {span_y:.1f}y < {MIN_SPAN_YEARS}y bar"
                rows.append(row)
                continue
            cs = {}
            for tn, ts, tm in trio_series:
                c, n = corr_common(s, ts, "price", tm)
                cs[tn] = c
                row[f"corr_{tn.lower().replace('_15vol', '')}"] = \
                    round(c, 4) if np.isfinite(c) else np.nan
                row[f"nobs_{tn.lower().replace('_15vol', '')}"] = n
            c, n = corr_common(s, champ, "price", "ret_curve")
            row["corr_to_champion"] = round(c, 4) if np.isfinite(c) else np.nan
            row["nobs_champion"] = n
            finite = [v for v in cs.values() if np.isfinite(v)]
            row["max_corr_trio"] = (round(max(abs(v) for v in finite), 4)
                                    if len(finite) == len(cs) and cs else np.nan)
            if len(finite) < len(cs):
                row["note"] = "corr unmeasurable on >=1 trio member (thin overlap)"
            elif row["max_corr_trio"] > CORR_TRIO_MAX:
                row["note"] = (f"max|corr| vs trio {row['max_corr_trio']} > "
                               f"{CORR_TRIO_MAX} (not decorrelated)")
            else:
                row["note"] = "eligible"
        rows.append(row)
    return pd.DataFrame(rows)


def _row(sym, path, st, cls, m) -> dict:
    return dict(symbol=sym, path=path, status=st, span_class=cls,
                start=m.get("start", ""), end=m.get("end", ""), rows=m.get("n", 0),
                maxgap_days=m.get("maxgap", 0), zero_ret_rows=m.get("zrun", 0),
                jump_days=m.get("jumps", 0), dup_dates=m.get("dups", 0),
                role="candidate_rejected" if str(st).startswith("FAIL") else "",
                note=str(st) if str(st).startswith("FAIL") else "",
                span_years=np.nan, corr_spy=np.nan, corr_ief=np.nan, corr_cta=np.nan,
                corr_to_champion=np.nan, max_corr_trio=np.nan,
                nobs_spy=0, nobs_ief=0, nobs_cta=0, nobs_champion=0)


# ------------------------------------------------------------------- selection
def select_benches(measured: pd.DataFrame) -> tuple:
    """Pre-registered greedy rule (see test_bench_r5 docstring). Returns
    (selected_df, ranked_eligible_df)."""
    ok = measured[(measured.status.str.startswith("PASS"))
                  & (measured.note == "eligible")].copy()
    ok = ok.sort_values(["max_corr_trio", "span_years"],
                        ascending=[True, False], kind="mergesort")
    taken, kept = [], []
    for _, r in ok.iterrows():
        if len(taken) >= 2:
            break
        dup = False
        for t in taken:
            c = _corr_selected(r, t, measured)
            if np.isfinite(c) and abs(c) > PAIR_CORR_MAX:
                dup = True
                break
        if dup:
            continue
        taken.append(r)
        kept.append(r)
    sel = pd.DataFrame(kept) if kept else measured.iloc[0:0].copy()
    return sel, ok


def _corr_selected(a, b, measured) -> float:
    """Corr between two candidate frames on their common dates."""
    fa = _frame_of(a)
    fb = _frame_of(b)
    if fa is None or fb is None:
        return float("nan")
    c, _ = corr_common(fa, fb, a.get("lint_mode", "price"),
                       b.get("lint_mode", "price"))
    return c


def _frame_of(r) -> pd.Series | None:
    p = r.path
    if not os.path.exists(p):
        return None
    return load_px(p)


# -------------------------------------------------------------------- manifest
def _committed() -> pd.DataFrame:
    return pd.read_csv(MANIFEST)


def build(out_path: str = MANIFEST) -> pd.DataFrame:
    """Deterministic manifest: trio rows first (sorted by TRIO order), then
    candidates sorted by symbol; every row pins sha256_16 + vintage source.
    Two builds byte-identical (test_manifest_byte_stable)."""
    rows = []
    for name, path, mode, src in TRIO:
        s = load_any(path, mode)
        rows.append(dict(
            symbol=name, role="trio_pinned", path=path, lint_mode=mode,
            px_convention=("close_price" if mode == "price" else "ret_curve"),
            fetch_source=src, sha256_16=sha256(path)[:16],
            start=str(s.index[0].date()), end=str(s.index[-1].date()),
            rows=len(s), span_years=round((s.index[-1] - s.index[0]).days / 365.25, 2),
            maxgap_days=int(s.index.to_series().diff().dt.days.max()),
            zero_ret_rows=int((s.diff() == 0).sum()),
            # same convention as lint_price: price |pct_change|>0.5, ret |diff|>0.5
            jump_days=int((s.pct_change().abs() > 0.5).sum() if mode == "price"
                          else (s.diff().abs() > 0.5).sum()),
            dup_dates=int(s.index.duplicated().sum()),
            status="PIN", span_class="pinned",
            corr_spy=np.nan, corr_ief=np.nan, corr_cta=np.nan,
            corr_to_champion=np.nan, max_corr_trio=np.nan,
            nobs_spy=0, nobs_ief=0, nobs_cta=0, nobs_champion=0, note="",
        ))
    meas = measure_candidates()
    sel, _ = select_benches(meas)
    sel_syms = set(sel.symbol) if len(sel) else set()
    meas = meas.copy()
    meas["role"] = meas.apply(
        lambda r: "decorrelated_passive" if r.symbol in sel_syms
        else ("candidate_rejected" if str(r.status).startswith("FAIL")
              or r.get("note") != "eligible" else "eligible_not_selected"), axis=1)
    for _, r in meas.iterrows():
        src = CAND_SOURCE.get(r.symbol, "forced_frame(test)")
        path = r.path
        sha = sha256(path)[:16] if os.path.exists(path) else "n/a"
        rows.append(dict(
            symbol=r.symbol, role=r.role, path=path, lint_mode="price",
            px_convention="close_price", fetch_source=src, sha256_16=sha,
            start=r.start, end=r.end, rows=r.rows, span_years=r.span_years,
            maxgap_days=r.maxgap_days, zero_ret_rows=r.zero_ret_rows,
            jump_days=r.jump_days, dup_dates=r.dup_dates,
            status=r.status, span_class=r.span_class,
            corr_spy=r.corr_spy, corr_ief=r.corr_ief, corr_cta=r.corr_cta,
            corr_to_champion=r.corr_to_champion, max_corr_trio=r.max_corr_trio,
            nobs_spy=r.nobs_spy, nobs_ief=r.nobs_ief, nobs_cta=r.nobs_cta,
            nobs_champion=r.nobs_champion, note=r.note,
        ))
    mf = pd.DataFrame(rows)
    mf = mf.sort_values(["role", "symbol"], kind="mergesort").reset_index(drop=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    mf.to_csv(out_path, index=False, lineterminator="\n")
    return mf


if __name__ == "__main__":
    m = build()
    print(m[["symbol", "role", "status", "span_years", "corr_spy", "corr_ief",
             "corr_cta", "corr_to_champion", "max_corr_trio", "note"]].to_string(index=False))
