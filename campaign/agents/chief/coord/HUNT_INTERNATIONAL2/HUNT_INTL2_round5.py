#!/usr/bin/env python3
"""HUNT_INTERNATIONAL2 round 5 — NKY 77-year span-class sleeve (charter pre-registered corner).

Corner: the `NKY calendars` DEAD_IDEAS row is status data-acquired/ready-for-hunt
(20,166 daily rows 1949-05-16..2026-08-31, span_class pre2007 per V2 §9). Families:
calendar effects (TOM / TOY / sell-in-May) and single-market time-series momentum on the
77y span, each judged with the MANDATORY pre-1990 vs post-1990 sub-span stability analysis.
NOT a re-test of any dead family (calendar-seasonal-equity-book was perm-SR-failed on a
different universe; international cross-momentum was cross-country, not single-market).

Honesty per GATES_CONTRACT_V2:
 T+1 shift(1); 6.4bps full |dW| + 0.5%/yr borrow; vt10 expanding clip3; scramble 200x
 re-costed; gates.run V2 battery with sig= + leak_check=True (V2 §6 Step 1) +
 beats_passive=True trio (V2 §7); mandatory pre-1990 vs post sub-span stability.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np
import pandas as pd
from bt import engine, metrics
import bt.gates as bgates

ROOT = "/Users/daxu/software/world-trader"
COST_BPS = 6.4
NKY_PATH = f"{ROOT}/tools/quant/data/newdata/NIKKEI225.csv"
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]


def load_nky():
    df = pd.read_csv(NKY_PATH, index_col=0, parse_dates=True)
    s = df.iloc[:, 0].astype(float).sort_index()
    s = s[~s.index.duplicated(keep="last")]
    return s.dropna()


def month_zone(idx, k_end, k_start=None):
    """Rank of each date within its month: k_end from month end, k_start from month start."""
    ser = idx.to_series()
    r_end = ser.groupby(ser.index.to_period("M")).rank(method="first", ascending=False)
    r_start = ser.groupby(ser.index.to_period("M")).rank(method="first")
    z = r_end <= k_end
    if k_start:
        z = z | (r_start <= k_start)
    return z.reindex(idx).fillna(False).astype(bool)


def _daily_W(idx, on):
    W = pd.DataFrame({"NKY": on.astype(float)}, index=idx)
    return W


def cal_tom_weights(px):
    """Turn-of-month PRIMARY, date-based: long when day-of-month >= 28 or <= 3.
    Needs no calendar knowledge -> strictly truncation-invariant (the rank variant
    below is calendar-knowable but NOT truncation-invariant in a cut's partial month)."""
    idx = px.index
    on = (idx.day >= 28) | (idx.day <= 3)
    return _daily_W(idx, pd.Series(on, index=idx))


def cal_tom_rank_weights(px, k_end=3, k_start=3):
    """SECONDARY (published-calendar) rank variant: long on the last k_end + first
    k_start TRADING days of each month. Diffs vs full-sample inside a cut's final
    partial month are the documented calendar-knowledge property, not lookahead."""
    idx = px.index
    on = month_zone(idx, k_end, k_start)
    return _daily_W(idx, on)


def cal_toy_weights(px):
    """Turn-of-year PRIMARY, date-based: long Dec 25-31 + Jan 1-5.
    Strictly truncation-invariant."""
    idx = px.index
    on = ((idx.month == 12) & (idx.day >= 25)) | ((idx.month == 1) & (idx.day <= 5))
    return _daily_W(idx, pd.Series(on, index=idx))


def cal_toy_rank_weights(px, k=5):
    """SECONDARY (published-calendar) rank variant: last k bdays of Dec + first k of Jan."""
    idx = px.index
    ser = idx.to_series()
    r_end = ser.groupby(ser.index.to_period("M")).rank(method="first", ascending=False)
    r_start = ser.groupby(ser.index.to_period("M")).rank(method="first")
    on = ((idx.month == 12) & (r_end <= k)) | ((idx.month == 1) & (r_start <= k))
    return _daily_W(idx, on.reindex(idx).fillna(False))


def cal_sellmay_weights(px):
    """Sell-in-May: long Oct..Apr, flat May..Sep."""
    idx = px.index
    on = ~idx.month.isin([5, 6, 7, 8, 9])
    return _daily_W(idx, pd.Series(on, index=idx))


def mom_weights(px, lookback=252, mode="LF"):
    """Single-market time-series momentum: sign of the trailing lookback-day move
    (LF: long-or-flat; LS: long/short). net_of applies the T+1 shift globally, so a
    day-t decision from px up to day t is causal."""
    if isinstance(px, pd.DataFrame):
        px = px.iloc[:, 0]
    idx = px.index
    mom = px - px.shift(lookback)  # trailing lookback-day move (warmup = lookback)
    up = (mom > 0).reindex(idx).fillna(False)
    dn = (mom < 0).reindex(idx).fillna(False)
    W = _daily_W(idx, up)
    if mode == "LS":
        W.loc[dn, "NKY"] = -1.0
    return W.where((mom.notna()).reindex(idx).fillna(False), 0.0)


def net_of(W, R, vt=True, target=0.10):
    """T+1 effective weights, trailing vol-target, 6.4bps full |dW| + borrow on shorts."""
    We = W.shift(1).fillna(0.0)
    gross = (We * R).sum(axis=1)
    if vt:
        s = engine.vol_target_scale(gross.to_frame("g"), target=target)["g"]
        We = We.mul(s, axis=0)
    port = (We * R).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=COST_BPS)
    borrow = engine.borrow_cost(We)
    return (port - cost - borrow).rename("ret"), We, gross


def per_unit_net(r, We):
    """Per-unit net return series: the costed book return of a 1.0-unit position, so that
    sig * r_pu reproduces the costed book EXACTLY (needed for gates.run's sig*r contract)."""
    r = r.reindex(We.index).fillna(0.0)
    port = We.sum(axis=1) * r
    cost = engine.cost_turnover(We, cost_bps=COST_BPS)
    borrow = engine.borrow_cost(We)
    return (port - cost - borrow) / We.sum(axis=1).replace(0.0, np.nan).fillna(1.0)


def trim_warmup(net, We):
    """Trim to first live day; never-live book = broken build -> fail closed."""
    live = (We.fillna(0.0) != 0).any(axis=1)
    if not live.any():
        raise AssertionError("never-live book: weights all zero — signal selection is broken")
    return net[net.index >= live.idxmax()]


def scramble_p(We, R, net, n=200, seed=7):
    """Campaign-standard row-scramble of FINAL effective weights, re-costed; p = P(SR_scr >= real)."""
    idx = net.index
    We = We.reindex(idx).fillna(0.0)
    Re = R.reindex(idx).fillna(0.0)
    real_sr = metrics.sharpe_d(net)
    arrW, arrR = We.values, Re.values
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        Wp = pd.DataFrame(arrW[rng.permutation(len(idx))], index=idx, columns=We.columns)
        book = (Wp * Re).sum(axis=1) - engine.cost_turnover(Wp, cost_bps=COST_BPS) \
            - engine.borrow_cost(Wp)
        if metrics.sharpe_d(book) >= real_sr:
            cnt += 1
    return cnt / n


def subspan_verdict(srs: dict):
    """V2/charter MANDATORY sub-span stability: pre-1990 and post-1990 SRs. ok=True only when
    BOTH eras clear 0.5 AND the eras agree in sign; a one-era-only sleeve is a FAIL with the
    era named (the R4 TimesFM span-gate bar: >=8y of effect)."""
    pre, post = srs.get("pre1990", np.nan), srs.get("post1990", np.nan)
    out = dict(pre1990_sr=pre, post1990_sr=post, ok=False, reason=None)
    eras = [k for k, v in srs.items() if np.isfinite(v)]
    if len(eras) < 2:
        out["reason"] = f"one-era-only ({','.join(eras) or 'none'})"
        return out
    out["ok"] = bool(pre >= 0.5 and post >= 0.5 and (pre > 0) == (post > 0)
                     and min(pre, post) >= 0.5)
    if not out["ok"]:
        out["reason"] = (f"era imbalance: pre {pre:.2f} vs post {post:.2f}"
                         if (pre > 0) == (post > 0) else
                         f"era sign-flip: pre {pre:.2f} vs post {post:.2f}")
    return out


# ------------------------------------------------------------------ V2 battery runner

def battery(name, net, We, R, verbose=True):
    """Full V2 battery: gates.run(sig=, leak_check=True, beats_passive=True) + scramble,
    sub-span stability, span_class print, plateau grid, per-benchmark SRs in .meta."""
    from bt import beats_passive as BP
    net = trim_warmup(net, We)
    r_pu = per_unit_net(R["NKY"], We)
    sig = We.sum(axis=1).reindex(net.index).fillna(0.0)
    span_start = net.index[0]
    span_class = "pre2007" if span_start <= pd.Timestamp("2007-01-01") else (
        "2007plus" if span_start <= pd.Timestamp("2013-01-01") else "inception_fail")
    g = bgates.run(r_pu.reindex(net.index), ref=CHAMP, sig=sig, leak_check=True,
                   beats_passive=True, spy=SPY_RET, ief=IEF_RET, cta=CTA_RET)
    # mandatory sub-span stability
    pre = net[net.index < pd.Timestamp("1990-01-01")]
    post = net[net.index >= pd.Timestamp("1990-01-01")]
    sr_pre = metrics.sharpe_d(pre) if len(pre) > 60 else np.nan
    sr_post = metrics.sharpe_d(post) if len(post) > 60 else np.nan
    ss = subspan_verdict({"pre1990": sr_pre, "post1990": sr_post})
    # plateau: neighbors on the natural family grid
    res = dict(gates=g, ss=ss, span_class=span_class, n=len(net),
               start=net.index[0].date(), end=net.index[-1].date(),
               sr=metrics.sharpe_d(net), ann=metrics.ann_geo(net))
    if verbose:
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} span_class={span_class} "
              f"SR={res['sr']:.2f} ann={res['ann']*100:.1f}% "
              f"gates.pass={g['pass']} leak={g.get('leak', {}).get('leak') if g.get('leak') else None}")
    return res


SPY_RET = IEF_RET = CTA_RET = None


def load_benchmarks():
    global SPY_RET, IEF_RET, CTA_RET
    spy = pd.read_csv(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv",
                      parse_dates=["date"]).set_index("date")["close"].sort_index()
    SPY_RET = spy.pct_change().rename("ret")
    IEF_RET = pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/IEF.csv",
                          parse_dates=["date"]).set_index("date")["close"].sort_index().pct_change().rename("ret")
    CTA_RET = pd.read_csv(f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv",
                          parse_dates=["date"]).set_index("date")["ret"]


# ------------------------------------------------------------------ main: full grid

def run_grid():
    """Charter grid: 3 calendar configs + 4 momentum configs, each with the full V2
    battery, mandatory pre/post-1990 sub-span stability, and beats-passive trio."""
    load_benchmarks()
    pxs = load_nky()
    print(f"NKY: {pxs.index[0].date()} -> {pxs.index[-1].date()}  n={len(pxs)} "
          f"(span_class pre2007)")
    R = pxs.pct_change().to_frame("NKY")
    champ = CHAMP

    grid = [
        ("CAL_TOM_dates", cal_tom_weights(pxs)),
        ("CAL_TOM_rank3", cal_tom_rank_weights(pxs, 3, 3)),
        ("CAL_TOY_dates", cal_toy_weights(pxs)),
        ("CAL_TOY_rank5", cal_toy_rank_weights(pxs, 5)),
        ("CAL_SELLMAY", cal_sellmay_weights(pxs)),
        ("MOM_252_LS", mom_weights(pxs, 252, "LS")),
        ("MOM_252_LF", mom_weights(pxs, 252, "LF")),
        ("MOM_126_LF", mom_weights(pxs, 126, "LF")),
        ("MOM_63_LF", mom_weights(pxs, 63, "LF")),
    ]
    rows = []
    keep = []
    for name, W in grid:
        net, We, gross = net_of(W, R)
        net = trim_warmup(net, We)
        keep.append((name, W, net, We))
        # exact per-unit feed of the POST-VT book: sig * r_pu == net wherever held
        # (exit-only cost rows bounded by one day's cost, disclosed in meta)
        r_pu = per_unit_net(R["NKY"], We).reindex(net.index)
        sig = We.sum(axis=1).reindex(net.index).fillna(0.0)
        g = bgates.run(r_pu, ref=champ, sig=sig, leak_check=True,
                       beats_passive=True, spy=SPY_RET, ief=IEF_RET, cta=CTA_RET)
        pre = net[net.index < pd.Timestamp("1990-01-01")]
        post = net[net.index >= pd.Timestamp("1990-01-01")]
        sr_pre = metrics.sharpe_d(pre) if len(pre) > 60 else np.nan
        sr_post = metrics.sharpe_d(post) if len(post) > 60 else np.nan
        ss = subspan_verdict({"pre1990": sr_pre, "post1990": sr_post})
        leak = g.get("leak") or {}
        bp = g.get("beats_passive") or {}
        row = dict(
            _g=g,
            name=name, n=len(net), start=net.index[0].date(), end=net.index[-1].date(),
            span_class="pre2007" if net.index[0] <= pd.Timestamp("2007-01-01") else "?",
            sr=metrics.sharpe_d(net), ann=metrics.ann_geo(net),
            h1=g["h1"], h2=g["h2"], neg=g["neg_years"], worst=g["worst"],
            ac1=g["ac1"], scr_p=g["scr_p"], corr=g["corr"],
            leak_corr=leak.get("same_period_corr"), leak_flag=leak.get("leak"),
            leak_ok=g.get("leak_ok"),
            bp_best=(g.get("beats_passive") or {}).get("best_passive_sr"),
            bp_name=(g.get("beats_passive") or {}).get("best_passive_name"),
            bp_margin=(g.get("beats_passive") or {}).get("margin"),
            bp_reason=(g.get("beats_passive") or {}).get("reason"),
            bp_ok=g.get("beats_passive_ok"),
            sr_pre=sr_pre, sr_post=sr_post, ss_ok=ss["ok"], ss_reason=ss.get("reason"),
            pass_=bool(g["pass"]),
        )
        rows.append(row)
        print(f"\n[{name}] n={row['n']} {row['start']}->{row['end']} ({row['span_class']})")
        print(f"  SR {row['sr']:+.3f}  ann {row['ann']*100:+.1f}%  H1 {row['h1']:+.2f} "
              f"H2 {row['h2']:+.2f}  negyr {row['neg']} worst {row['worst']*100:.1f}%")
        print(f"  ac1 {row['ac1']:+.3f}  scr_p {row['scr_p']:.3f}  corrChamp {row['corr']:+.3f} "
              f"| leak same-per-corr {row['leak_corr']:+.4f} flag {row['leak_flag']} "
              f"leak_ok {row['leak_ok']}")
        print(f"  beats-passive: best {row['bp_name']} SR "
              f"{row['bp_best'] if row['bp_best'] is None else round(row['bp_best'],3)} "
              f"margin {'NA' if row['bp_margin'] is None else round(row['bp_margin'],3)} "
              f"reason {row['bp_reason']}")
        for bk, bv in (g.get('beats_passive', {}).get('detail') or {}).items():
            sr_v = bv.get('sr') if isinstance(bv, dict) else None
            print(f"      bp[{bk}] sr {sr_v if sr_v is None or not np.isfinite(sr_v) else round(sr_v,3)}"
                  f" n {bv.get('n') if isinstance(bv, dict) else bv}")
        print(f"  SUB-SPAN: pre-1990 SR {row['sr_pre']:+.3f}  post-1990 SR {row['sr_post']:+.3f}"
              f"  ok={row['ss_ok']}{'  (' + row['ss_reason'] + ')' if row['ss_reason'] else ''}")
        print(f"  gates.run pass = {row['pass_']}")
    save_artifacts(rows, keep)
    out = pd.DataFrame(rows)
    out.drop(columns=['_g'], errors='ignore').to_csv(
        f"{ROOT}/campaign/agents/chief/coord/HUNT_INTERNATIONAL2/work_r5/grid_r5.csv", index=False)
    print("\nsaved work_r5/grid_r5.csv")
    return out


# ------------------------------------------------------------------ artifact publication

import hashlib, json, os


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def save_artifacts(rows_out, sleeves):
    """§10a positions published + §9d/§10b vintage pins in .meta for every config."""
    base = f"{ROOT}/campaign/agents/chief/coord/HUNT_INTERNATIONAL2/sleeves"
    os.makedirs(base, exist_ok=True)
    pins = {
        "NIKKEI225.csv": _sha(NKY_PATH),
        "champion": _sha(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"),
        "SPY.csv": _sha(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv"),
        "IEF.csv": _sha(f"{ROOT}/tools/quant/data/more_etf/IEF.csv"),
        "CTA_15vol.csv": _sha(f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv"),
    }
    metas = {}
    for row, (name, W, net, We) in zip(rows_out, sleeves):
        slug = name
        csvp = f"{base}/INTL_R5_{slug}.csv"
        pd.DataFrame({"date": net.index.strftime("%Y-%m-%d"), "ret": net.values}).to_csv(
            csvp, index=False)
        pd.DataFrame({"date": We.index.strftime("%Y-%m-%d"), "w": We["NKY"].values}).to_csv(
            f"{base}/INTL_R5_{slug}_positions.csv", index=False)
        g = row.pop("_g")
        meta = {
            "config": name, "status": "DEAD_NOT_PROMOTED" if not row["pass_"] else "PASS",
            "span_class": row["span_class"], "n": int(row["n"]),
            "start": str(row["start"]), "end": str(row["end"]),
            "net_sr": round(float(row["sr"]), 4), "ann": round(float(row["ann"]), 4),
            "h1": round(float(row["h1"]), 4), "h2": round(float(row["h2"]), 4),
            "neg_years": int(row["neg"]), "worst_year": round(float(row["worst"]), 4),
            "ac1": round(float(row["ac1"]), 4), "scramble_p": (
                None if not np.isfinite(row["scr_p"]) else round(float(row["scr_p"]), 4)),
            "corr_to_champion": round(float(row["corr"]), 4),
            "leak": {"same_period_corr": (
                None if row["leak_corr"] is None or not np.isfinite(row["leak_corr"])
                else round(float(row["leak_corr"]), 4)),
                "leak_flag": None if row["leak_flag"] is None else bool(row["leak_flag"]),
                "leak_ok": None if row["leak_ok"] is None else bool(row["leak_ok"])},
            "beats_passive": g.get("beats_passive"),
            "beats_passive_ok": g.get("beats_passive_ok"),
            "subspan": {"pre1990_sr": round(float(row["sr_pre"]), 4),
                        "post1990_sr": round(float(row["sr_post"]), 4),
                        "ok": bool(row["ss_ok"]), "reason": row["ss_reason"]},
            "gates_full_pass": bool(row["pass_"]),
            "feed_notes": ("r_pu is the post-VT per-unit net book; sig*r_pu == net exactly "
                           "wherever the position is non-zero. Rows where the book is flat "
                           "but an exit cost was charged cannot be represented by sig*r_pu "
                           "(0*anything=0); that gap is <= one day's cost and is included "
                           "in the published net series used for every performance number."),
            "economic_rationale": (
                "Calendar/seasonal anomalies (turn-of-month, turn-of-year, sell-in-May) and "
                "single-market time-series momentum on the 77y NKY span; the charter's "
                "pre-registered corner after the span blocker cleared."),
            "vintage_pins": pins,
            "files": {"sleeve": f"INTL_R5_{slug}.csv",
                      "positions": f"INTL_R5_{slug}_positions.csv"},
        }
        metas[name] = meta
        with open(f"{base}/INTL_R5_{slug}.meta.json", "w") as f:
            json.dump(meta, f, indent=1, default=str)
    with open(f"{ROOT}/campaign/agents/chief/coord/HUNT_INTERNATIONAL2/work_r5/grid_r5_meta.json",
              "w") as f:
        json.dump(metas, f, indent=1, default=str)
    print(f"published {len(metas)} sleeve csvs + positions + metas (pins {pins})")


if __name__ == "__main__":
    run_grid()
