#!/usr/bin/env python3
"""HUNT_TREASFUT round 5 — TreasuryDirect auction-CYCLE positioning (charter R5 corner (a),
pre-registered). Pre/post-auction drift in futures-proxy tenor books built from FRED CMT
synth TR (R1 machinery), windows anchored on TreasuryDirect auction dates.

NOT a re-test of any dead family:
  - DEAD row 51 (HUNT_AUCTION) = btc/indirect-share z-gates as EQUITY regime gates on
    QQQ/DIA. Nothing here touches an equity leg.
  - DEAD rows 59-62/85 (my R1/R2) = slope/level momentum, fly reversion, intl carry. No
    book here conditions on any moving average, z-score, or momentum of yields: the ONLY
    signal inputs are the auction CALENDAR (event timing) and the auction RESULT (btc vs
    its strictly-prior median, PIT convention (A)).

Pre-registered, locked in tests_tdd_r5.py BEFORE any result was seen:
  DURS: charter R2 futures-proxy {'2': 4.4, '10': 7.7, '30': 15.5}; '5' extension leg =
        linear-in-tenor 4.4 + (7.7-4.4)*3/8 = 5.6375 (disclosed interpolation).
  Events: term exactly {'2-Year','5-Year','10-Year','30-Year'} (fresh issues; reopenings
        like '9-Year 10-Month' excluded). MIN_PRIOR = 4 priors before the demand median
        is defined.
  Windows: POST = k trading days STRICTLY AFTER the auction-day anchor (uniform for ALL
        books incl. unconditional ones, so the leak probe tests the signal rather than a
        same-day convention); PRE = k trading days strictly before. A-priori k=5, plateau
        neighbors {3, 10} on the 10y leg.
  Conditioning (CON demand): btc_a - expanding-median(btc of STRICTLY prior auctions of
        the same type+term). Weak demand (btc < med) -> long (concession reversal);
        strong -> short. Decision at the auction-day close (results publish ~13:00-13:30
        ET), weight rows from the next trading day (T+1 shift(1) earns from e+2nd row).
  PRIMARY signs (economic story: dealers short the when-issued into the auction -> pre-
        auction concession, reversal after): PRE=long, POST=long, COND=weak-demand long.
        ANTI = sign-flip controls run for the 10y trio (dead-both-ways check, per the
        gold-silver R4 audit convention).
Engine: r1.net_of (T+1, vt10 clip3, 6.4bps FULL |dW|, 0.5%/yr borrow) + r1 units/dead-book
guards. Battery: gates.run(sig=, leak_check=True, beats_passive=True) full V2 set + row-
permutation scramble + lagroll scramble + pre/post-2013 era verdict + plateau grid.
"""
import hashlib
import json
import os
import sys

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")
import numpy as np
import pandas as pd
from bt import engine, metrics
import bt.gates as bgates

import HUNT_TREASFUT_round1 as r1

FRED = f"{ROOT}/tools/quant/data/more_fred"
TA_PATH = f"{ROOT}/tools/quant/data/treasury_auctions/tauctions.csv"
COST_BPS = 6.4
DURS = {"2": 4.4, "5": 5.6375, "10": 7.7, "30": 15.5}
TERM_OF = {"2": ("Note", "2-Year"), "5": ("Note", "5-Year"),
           "10": ("Note", "10-Year"), "30": ("Bond", "30-Year")}
MIN_PRIOR = 4
K_APRIORI = 5
PLATEAU_K = (3, 10)
ERAS = ("pre2013", "post2013")

CHAMP = r1.CHAMP
A6R7 = r1.A6R7
A1CR = r1.A1CR

SPY_RET = IEF_RET = CTA_RET = None

_R_CACHE = {}


def benchmark_series():
    global SPY_RET, IEF_RET, CTA_RET
    spy = pd.read_csv(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv",
                      parse_dates=["date"]).set_index("date")["close"].sort_index()
    SPY_RET = spy.pct_change().rename("ret")
    IEF_RET = pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/IEF.csv",
                          parse_dates=["date"]).set_index("date")["close"].sort_index().pct_change().rename("ret")
    CTA_RET = pd.read_csv(f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv",
                          parse_dates=["date"]).set_index("date")["ret"]
    return SPY_RET, IEF_RET, CTA_RET


# ---------------------------------------------------------------- data layer

def load_auctions():
    """Tidy tauctions.csv -> wide frame indexed by auction_date, columns = tenor labels,
    values = bid_to_cover, restricted to the four flagship fresh-issue terms. One row per
    (date, term): tauctions has exactly ONE multi-CUSIP (date,term) group dataset-wide
    (2015-01-28 2-Year: the regular $26.0bn 912828H78 + a $15.0bn additional CUSIP
    912828H60 from the debt-limit-timing double issuance); a-priori rule = keep the
    LARGEST total_accepted_mmn row (the regular auction), disclosed in the .meta."""
    raw = pd.read_csv(TA_PATH, parse_dates=["date"])
    keep = []
    for t, (typ, term) in TERM_OF.items():
        s = raw[(raw["type"] == typ) & (raw["term"] == term)].copy()
        s = (s.sort_values("total_accepted_mmn", ascending=False)
              .drop_duplicates(subset=["date"], keep="first").sort_values("date"))
        assert len(s) >= {"2": 350, "5": 300, "10": 140, "30": 85}[t], (t, len(s))
        assert s.bid_to_cover.notna().mean() >= 0.95, (t, s.bid_to_cover.notna().mean())
        keep.append(pd.Series(s.bid_to_cover.values, index=s.date.values, name=t))
    ev = pd.concat(keep, axis=1, sort=True).sort_index()
    ev.index = pd.DatetimeIndex(ev.index)
    ev.index.name = "date"
    return ev


def event_dates(tenor):
    return load_auctions().index[load_auctions()[tenor].notna()]


def expanding_median_past(s):
    """Convention (A) PIT: value AT row i = median of rows STRICTLY BEFORE i (same series),
    NaN until MIN_PRIOR non-NaN priors. The row's own value never enters its own median."""
    s = s.sort_index()
    v = s.values.astype(float)
    out = np.full(len(v), np.nan)
    for i in range(1, len(v)):
        past = v[:i]
        past = past[np.isfinite(past)]
        if len(past) >= MIN_PRIOR:
            out[i] = float(np.median(past))
    return pd.Series(out, index=s.index, name=s.name)


def _grid(tenor):
    """Single-leg synth-TR frame (common yield grid, dropna), units-guarded. Cached."""
    if tenor not in _R_CACHE:
        R = pd.concat({tenor: r1.synth_tr(r1.load_yield(f"DGS{tenor}"), DURS[tenor])},
                      axis=1).dropna()
        r1.units_guard(R)
        _R_CACHE[tenor] = R
    return _R_CACHE[tenor]


def make_R(durs):
    """Multi-leg synth-TR frame on the common grid (dropna), units-guarded."""
    R = pd.concat({k: r1.synth_tr(r1.load_yield(f"DGS{k}"), d) for k, d in durs.items()},
                  axis=1).dropna()
    r1.units_guard(R)
    return R


# ---------------------------------------------------------------- windows

def _anchor_positions(grid_idx, tenor, end=None):
    """Grid position of each auction anchor. Auction dates are weekdays; if one falls on a
    non-grid day (holiday) the anchor is the NEXT grid day (counted, disclosed)."""
    idx = grid_idx
    if end is not None:
        idx = idx[idx <= end]
    ev = event_dates(tenor)
    if end is not None:
        ev = ev[ev <= end]
    pos = pd.Series(np.arange(len(idx)), index=idx)
    ipos = np.searchsorted(idx.values, ev.values)
    offgrid = int((ipos >= len(idx)).sum() +
                  sum(1 for p, e in zip(ipos, ev) if p < len(idx) and idx[p] != e))
    return ev, ipos, pos, offgrid


def _window_weights(tenor, k, mode, sign, end=None):
    """mode 'post': rows [e+1, e+k] (strictly after the anchor, uniform convention);
    mode 'pre': rows [e-k, e-1] (strictly before). Later windows overwrite earlier on
    overlap (mask semantics, no stacking). sign: +1 base / -1 anti."""
    R = _grid(tenor)
    ev, ipos, pos, _ = _anchor_positions(R.index, tenor, end)
    w = pd.Series(0.0, index=R.index)
    n = len(R)
    for e in ipos:
        if e >= n:
            continue
        if mode == "post":
            lo, hi = e + 1, min(e + k, n - 1)
        else:
            lo, hi = max(e - k, 0), e - 1
        if hi >= lo:
            w.iloc[lo:hi + 1] = float(sign)
    return pd.DataFrame({tenor: w})


def w_post(tenor, k=K_APRIORI, sign=1, end=None):
    return _window_weights(tenor, k, "post", sign, end)


def w_pre(tenor, k=K_APRIORI, sign=1, end=None):
    return _window_weights(tenor, k, "pre", sign, end)


def w_post_cond(tenor, k=K_APRIORI, signed=True, sign=1, end=None):
    """Demand-conditioned POST book. Surprise at anchor e = btc_e - median(strictly-prior
    btc). Weak (<0) -> long, strong -> short (signed=True); signed=False -> always long
    (pure calendar). Weight rows [e+1, e+k]: the surprise is known at the e-close, rows
    start strictly after e, T+1 shift(1) earns from e+2 — no same-day leak by construction.
    sign flips the whole book (anti control)."""
    R = _grid(tenor)
    ev = load_auctions()[tenor]
    if end is not None:
        ev = ev[ev.index <= end]
    med = expanding_median_past(ev)
    surprise = ev - med
    R2 = R
    if end is not None:
        R2 = R[R.index <= end]
    w = pd.Series(0.0, index=R2.index)
    pos = pd.Series(np.arange(len(R2)), index=R2.index)
    for e, s in surprise.dropna().items():
        i = pos.asof(e)  # anchor grid position (auction day or next grid day)
        if pd.isna(i):
            continue
        i = int(i)
        if i >= len(R2):
            continue
        v = float(sign) * (float(np.sign(s)) if signed else 1.0)
        lo, hi = i + 1, min(i + k, len(R2) - 1)
        if hi >= lo:
            w.iloc[lo:hi + 1] = v
    return pd.DataFrame({tenor: w})


# ---------------------------------------------------------------- drift measurement

def drift_table(tenor, k=K_APRIORI):
    """Per-auction PIT measurement artifact: forward k-trading-day synth-TR sum after each
    auction (drift), the PIT median + surprise, and the strictly-prior mean drift
    (pre_mean, min_periods=1 over DEFINED priors — the decision quantity for the
    demand-independent cycle claim)."""
    R = _grid(tenor)
    ret = R[tenor]
    pos = pd.Series(np.arange(len(R)), index=R.index)
    ev = load_auctions()[tenor]
    ev = ev[ev.notna()]  # BUGFIX r5 (test-pinned): own-tenor auction dates ONLY — the wide
    # frame is union-indexed across tenors (877 dates); iterating it unfiltered pooled other
    # tenors' auction dates into this tenor's unconditional drift stats.
    med = expanding_median_past(ev)
    rows = []
    for a, btc in ev.items():
        i = pos.asof(a)
        if pd.isna(i):
            rows.append(dict(date=a, btc=btc, med=med.asof(a), drift=np.nan,
                             pre_mean=np.nan))
            continue
        i = int(i)
        lo, hi = i + 1, min(i + k, len(R) - 1)
        d = float(ret.iloc[lo:hi + 1].sum()) if hi >= lo else np.nan
        rows.append(dict(date=a, btc=btc, med=med.asof(a), drift=d,
                         pre_mean=np.nan))
    dr = pd.DataFrame(rows).set_index("date")
    dd = dr["drift"].values
    pm = np.full(len(dd), np.nan)
    for i in range(1, len(dd)):
        past = dd[:i][np.isfinite(dd[:i])]
        if len(past):
            pm[i] = float(np.mean(past))
    dr["pre_mean"] = pm
    dr["surprise"] = dr["btc"] - dr["med"]
    return dr


# ---------------------------------------------------------------- book build (r1 engine)

def net_of(W, R, vt=True, target=0.10):
    """r1.net_of (T+1, vt10 clip3, 6.4bps full |dW|, borrow) — re-exported here so the
    round is self-contained; identical semantics, dead-book ValueError preserved."""
    return r1.net_of(W, R, vt=vt, target=target)


def first_live(We):
    live = (We.fillna(0.0) != 0).any(axis=1)
    if not live.any():
        raise ValueError("dead book: 0 live rows — signal pipeline bug")
    return live.idxmax()


def per_unit_feed(R_leg, We):
    """V2 feed contract: (r_pu, sig) with sig*r_pu == the costed held book exactly wherever
    sig != 0 (INTL2-R5 convention; the CMDT2-R5 in-sweep defect class is r=NET)."""
    if isinstance(R_leg, pd.Series):
        Rf = R_leg.to_frame(R_leg.name or "leg")
    else:
        Rf = R_leg
        R_leg = Rf.iloc[:, 0]
    net, We2, _ = net_of(We, Rf)
    net = net[net.index >= first_live(We2)]
    We2 = We2.reindex(net.index).fillna(0.0)
    sig = We2.sum(axis=1)
    # NOTE: multiply frame x frame. (We2 * R_leg) with R_leg a Series aligns the Series on
    # We2's COLUMNS -> all-NaN -> a zero book r_pu (caught by test_per_unit_feed_exactness).
    port = (We2 * Rf.reindex(net.index).fillna(0.0)).sum(axis=1)
    cost = engine.cost_turnover(We2, cost_bps=COST_BPS)
    borrow = engine.borrow_cost(We2)
    raw = port - cost - borrow
    # BUGFIX r5 (leak-probe artifact): flat days must be 0.0, NOT 1.0 (INTL2's fill is
    # harmless for their ~always-in-market books but dominates a 5%-live auction book, and
    # the same-period probe then reads corr(sig, {1.0 outside, ~0 inside}) ~ -0.99 by
    # construction). 0.0 keeps sig*r_pu == the book exact everywhere (0*0 = 0).
    r_pu = (raw / sig.replace(0.0, np.nan)).fillna(0.0)
    return r_pu, sig, net


# ---------------------------------------------------------------- battery

def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def era_verdict(net):
    """Charter span-stability duty: pre-2013 vs post-2013 SR, same sign AND |SR| >= 0.25 in
    BOTH eras required for era_ok (>=8y of effect bar; auction era starts 2000, so the
    sample splits 13y/13y). Disclosure + stability gate, not an alpha claim."""
    out = {}
    for name, lo, hi in [("pre2013", None, "2013-01-01"), ("post2013", "2013-01-01", None)]:
        s = net[(net.index >= pd.Timestamp(lo) if lo else True)
                & (net.index < pd.Timestamp(hi) if hi else True)]
        out[name] = metrics.sharpe_d(s) if len(s) > 60 else np.nan
    pre, post = out["pre2013"], out["post2013"]
    ok = bool(np.isfinite(pre) and np.isfinite(post) and (pre > 0) == (post > 0)
              and min(abs(pre), abs(post)) >= 0.25)
    out["ok"] = ok
    if not ok:
        out["reason"] = f"era imbalance: pre {pre:.2f} vs post {post:.2f}"
    return out


def battery(name, net, We, R, verbose=True):
    """Full V2 battery for one book: gates.run(sig=, leak_check=True, beats_passive=True)
    + row-permutation scramble (r1.scramble_perm) + lagroll scramble (r1.lagroll_p) +
    era verdict + span_class. Returns dict; every number lands in the .meta."""
    from bt import beats_passive as _bp  # noqa: F401  (imported for side-effect parity)
    if SPY_RET is None:
        benchmark_series()
    net = net.dropna()
    net = net[net.index >= first_live(We)]
    r_pu, sig, net2 = per_unit_feed(R, We)
    net = net2  # exactly the window r_pu/sig are built on
    g = bgates.run(r_pu, ref=CHAMP, sig=sig, leak_check=True,
                   beats_passive=True, spy=SPY_RET, ief=IEF_RET, cta=CTA_RET)
    p_perm = r1.scramble_perm(We, R, net)
    lag_p = r1.lagroll_p(We, R, net)
    era = era_verdict(net)
    leak = g.get("leak") or {}
    bp = g.get("beats_passive") or {}
    span_start = net.index[0]
    span_class = ("pre2007" if span_start <= pd.Timestamp("2007-01-01")
                  else "2007plus" if span_start <= pd.Timestamp("2013-01-01")
                  else "inception_fail")
    res = dict(
        name=name, gates=g, n=len(net), start=net.index[0].date(), end=net.index[-1].date(),
        span_class=span_class,
        sr=metrics.sharpe_d(net), ann=metrics.ann_geo(net),
        h1=g["h1"], h2=g["h2"], neg=g["neg_years"], worst=g["worst"],
        ac1=g["ac1"], scr_p=g["scr_p"], corr=g["corr"],
        scr_perm=p_perm, lagroll_p=lag_p,
        leak=leak, leak_ok=g.get("leak_ok"), beats_passive=bp,
        beats_passive_ok=g.get("beats_passive_ok"),
        era=era, c_a6r7=bgates.corr_to(A6R7, net), c_a1credit=bgates.corr_to(A1CR, net),
        vol=float(net.std() * np.sqrt(252)),
    )
    res["pass"] = bool(g["pass"] and res["scr_perm"] <= 0.05 and lag_p is not None
                       and (not isinstance(lag_p, float) or lag_p == lag_p)
                       and (isinstance(lag_p, float) and lag_p <= 0.15) and era["ok"])
    if verbose:
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} ({span_class}) "
              f"SR={res['sr']:+.3f} ann={res['ann']*100:+.2f}% vol={res['vol']*100:.1f}%")
        print(f"   H1 {res['h1']:+.2f} H2 {res['h2']:+.2f} negyr {res['neg']} "
              f"worst {res['worst']*100:.1f}% ac1 {res['ac1']:+.3f}")
        lc = leak.get('same_period_corr')
        lc_s = f"{lc:+.4f}" if isinstance(lc, float) else str(lc)
        print(f"   scr_p {res['scr_p']:.3f} perm_p {p_perm:.3f} lag_p {lag_p:.3f} "
              f"corrChamp {res['corr']:+.3f} cA6R7 {res['c_a6r7']:+.3f} "
              f"leak {lc_s} leak_ok {res['leak_ok']}")
        bpbest = bp.get("best_passive_name")
        bpsr = bp.get("best_passive_sr")
        print(f"   beats_passive {res['beats_passive_ok']} best={bpbest}"
              f"{'' if bpsr is None or not np.isfinite(bpsr) else f':{bpsr:.3f}'} "
              f"reason={bp.get('reason')}")
        print(f"   era pre {era['pre2013']:+.3f} / post {era['post2013']:+.3f} ok={era['ok']}"
              f"{'' if era['ok'] else ' (' + str(era.get('reason', '')) + ')'}")
        print(f"   V2 composite pass = {res['pass']} (gates.pass={g['pass']})")
    return res


def plateau_check(tenor, kind, k_chosen, results):
    """Plateau gate on the k grid for the 10y leg: neighbors {3,10} vs chosen 5 must have
    SR >= (1-0.2) * peak within the SAME family/sign (uses gate-composite SR, not book SR,
    per contract 'SR at that param')."""
    fam = {k: v["sr"] for k, v in results.items()
           if v["meta"]["tenor"] == tenor and v["meta"]["kind"] == kind
           and v["meta"]["sign"] == results_chosen_sign(tenor, kind, results)}
    ok, info = bgates.plateau_ok(fam, k_chosen)
    return ok, info, fam


def results_chosen_sign(tenor, kind, results):
    return 1


# ---------------------------------------------------------------- main

def run_all():
    benchmark_series()
    ev = load_auctions()
    print("auction events (fresh-issue flagship terms):")
    print(ev.notna().sum().to_string())
    print(f"span {ev.index.min().date()} -> {ev.index.max().date()}")
    gap_note = {}
    for t in ev.columns:
        s = ev.index[ev[t].notna()]
        g = pd.Series(s).diff().dt.days.dropna()
        gap_note[t] = dict(n=int(len(s)), first=str(s[0].date()), last=str(s[-1].date()),
                           max_gap_days=int(g.max()), gaps_gt35=int((g > 35).sum()))
    print("gap structure:", json.dumps(gap_note))

    # descriptive drift table (PIT) — the measurement the charter asks for
    drift_summary = {}
    for t in ("2", "5", "10", "30"):
        dr = drift_table(t)
        d = dr["drift"].dropna()
        tstat = float(d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))) if len(d) > 2 else np.nan
        cond = dr.dropna(subset=["surprise"])
        lo = cond[cond["surprise"] < 0]["drift"].dropna()
        hi = cond[cond["surprise"] > 0]["drift"].dropna()
        drift_summary[t] = dict(
            n=int(len(d)), mean_bp_5d=float(d.mean() * 1e4),
            tstat=tstat, hit=float((d > 0).mean()),
            cond_weak_n=int(len(lo)), cond_weak_mean=float(lo.mean()) if len(lo) else np.nan,
            cond_strong_n=int(len(hi)), cond_strong_mean=float(hi.mean()) if len(hi) else np.nan)
        dr.to_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/work_r5/"
                  f"drift_table_DGS{t}_k{K_APRIORI}.csv")
    print("drift summary (synth-TR sum over 5d post window, bp of TR):")
    print(json.dumps(drift_summary, indent=1))

    results = {}
    books = []
    # PRIMARY sign books, k=5, all tenors
    for t in ("2", "5", "10", "30"):
        books.append((f"POST5_{t}_long", t, "post", 1, True,
                      w_post(t, K_APRIORI, sign=1)))
        books.append((f"PRE5_{t}_long", t, "pre", 1, True,
                      w_pre(t, K_APRIORI, sign=1)))
        books.append((f"COND5_{t}", t, "cond", 1, True,
                      w_post_cond(t, K_APRIORI, signed=True, sign=1)))
    # ANTI sign controls (10y trio)
    books.append(("POST5_10_anti", "10", "post", -1, False, w_post("10", K_APRIORI, sign=-1)))
    books.append(("PRE5_10_anti", "10", "pre", -1, False, w_pre("10", K_APRIORI, sign=-1)))
    books.append(("COND5_10_anti", "10", "cond", -1, False,
                  w_post_cond("10", K_APRIORI, signed=True, sign=-1)))
    # plateau neighbors on the 10y leg (primary sign)
    for k in PLATEAU_K:
        books.append((f"POST{k}_10_long", "10", "post", 1, False, w_post("10", k, sign=1)))
        books.append((f"COND{k}_10", "10", "cond", 1, False,
                      w_post_cond("10", k, signed=True, sign=1)))

    for name, t, kind, sign, primary, W in books:
        R = _grid(t)
        net, We, gross = net_of(W, R)
        res = battery(name, net, We, R, verbose=True)
        res["meta"] = dict(tenor=t, kind=kind, sign=sign, primary=primary, k=K_APRIORI)
        results[name] = res
        print()

    # plateau gates on the 10y leg families
    for kind in ("post", "cond"):
        fam = {K_APRIORI: results[f"{'POST' if kind == 'post' else 'COND'}5_10_long" if kind == "post" else "COND5_10"]["sr"],
               PLATEAU_K[0]: results[f"POST{PLATEAU_K[0]}_10_long" if kind == "post" else f"COND{PLATEAU_K[0]}_10"]["sr"],
               PLATEAU_K[1]: results[f"POST{PLATEAU_K[1]}_10_long" if kind == "post" else f"COND{PLATEAU_K[1]}_10"]["sr"]}
        ok, info = bgates.plateau_ok(fam, K_APRIORI)
        print(f"plateau[{kind} 10y k-grid {fam}]: ok={ok} {info}")

    save_artifacts(results, drift_summary, gap_note)
    return results


def save_artifacts(results, drift_summary, gap_note):
    base = f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/sleeves"
    os.makedirs(base, exist_ok=True)
    wrk = f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/work_r5"
    pins = {"tauctions.csv": _sha(TA_PATH),
            "champion": _sha(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"),
            "SPY.csv": _sha(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv"),
            "IEF.csv": _sha(f"{ROOT}/tools/quant/data/more_etf/IEF.csv"),
            "CTA_15vol.csv": _sha(f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv"),
            "DGS2": _sha(f"{FRED}/DGS2.csv"), "DGS5": _sha(f"{FRED}/DGS5.csv"),
            "DGS10": _sha(f"{FRED}/DGS10.csv"), "DGS30": _sha(f"{FRED}/DGS30.csv")}
    metas = {}
    for name, res in results.items():
        net_r = None
        slug = name
        # rebuild net + We for publication (battery consumed them internally)
        t, kind, sign = res["meta"]["tenor"], res["meta"]["kind"], res["meta"]["sign"]
        if kind == "post":
            W = w_post(t, res["meta"]["k"], sign=sign)
        elif kind == "pre":
            W = w_pre(t, res["meta"]["k"], sign=sign)
        else:
            W = w_post_cond(t, res["meta"]["k"], signed=True, sign=sign)
        R = _grid(t)
        net, We, gross = net_of(W, R)
        net = net[net.index >= first_live(We)]
        We = We.reindex(net.index).fillna(0.0)
        pd.DataFrame({"date": net.index.strftime("%Y-%m-%d"), "ret": net.values}).to_csv(
            f"{base}/TREASFUT5_{slug}.csv", index=False)
        pd.DataFrame({"date": We.index.strftime("%Y-%m-%d"),
                      "w": We[We.columns[0]].values}).to_csv(
            f"{base}/TREASFUT5_{slug}_positions.csv", index=False)
        g = res["gates"]
        leak = res["leak"]
        bp = res["beats_passive"]
        meta = {
            "config": slug, "status": "DEAD_NOT_PROMOTED" if not res["pass"] else "PASS",
            "family": "treasury_auction_cycle_r5", "tenor": t, "kind": kind,
            "sign": sign, "primary": res["meta"]["primary"], "k": res["meta"]["k"],
            "span_class": res["span_class"], "n": int(res["n"]),
            "start": str(res["start"]), "end": str(res["end"]),
            "net_sr": round(float(res["sr"]), 4), "ann_geo": round(float(res["ann"]), 4),
            "h1": round(float(res["h1"]), 4), "h2": round(float(res["h2"]), 4),
            "neg_years": int(res["neg"]), "worst_year": round(float(res["worst"]), 4),
            "ac1": round(float(res["ac1"]), 4),
            "scramble_p_gates": None if not np.isfinite(res["scr_p"]) else round(float(res["scr_p"]), 4),
            "scramble_p_perm": round(float(res["scr_perm"]), 4),
            "lagroll_p": round(float(res["lagroll_p"]), 4),
            "corr_to_champion": round(float(res["corr"]), 4),
            "corr_a6r7": round(float(res["c_a6r7"]), 4),
            "corr_a1credit": round(float(res["c_a1credit"]), 4),
            "leak": {"same_period_corr": None if not isinstance(leak.get("same_period_corr"), float)
                     else round(float(leak["same_period_corr"]), 4),
                     "same_period_p": None if not isinstance(leak.get("same_period_p"), float)
                     else float(leak["same_period_p"]),
                     "leak_flag": None if leak.get("leak") is None else bool(leak["leak"]),
                     "leak_ok": None if res["leak_ok"] is None else bool(res["leak_ok"])},
            "beats_passive": bp, "beats_passive_ok": res["beats_passive_ok"],
            "era": {k: (round(float(v), 4) if isinstance(v, float) else v)
                    for k, v in res["era"].items()},
            "gates_full_pass": bool(g["pass"]), "v2_composite_pass": bool(res["pass"]),
            "feed_notes": ("r_pu = costed per-unit book; sig*r_pu == net exactly wherever "
                           "sig!=0; flat-day exit-cost rows are in the published net series "
                           "but not representable as sig*r_pu (<= 1 day's cost, 6.4bps)."),
            "economic_rationale": (
                "Treasury auction-cycle positioning: dealers short the when-issued into "
                "auctions (inventory hedge) -> pre-auction concession and post-auction "
                "reversal; bid-to-cover vs its strictly-prior median times the post window. "
                "Pre-registered corner (charter R5 (a)); NOT row 51 (equity gates) and NOT "
                "any R1/R2 rates momentum/curve config (no MA/z/momentum of yields anywhere)."),
            "data_documentation": {
                "source": "treasurydirect.gov TA-WS via tools/quant/data/treasury_auctions/ta_dl.py (keyless)",
                "disk_file": "tools/quant/data/treasury_auctions/tauctions.csv",
                "gap_structure_by_tenor": gap_note,
                "liveness_probe_2026": (
                    "2026-09-08 re-fetch: 304 rows 2025-12-29..2026-09-10, 0 field "
                    "mismatches vs disk on all 4 audited fields, 0 missing rows; "
                    "work_r5/tauctions_2026_probe.csv sha 275e1853da1a3aa8"),
                "drift_summary_k5": drift_summary.get(t),
            },
            "vintage_pins": pins,
            "files": {"sleeve": f"TREASFUT5_{slug}.csv",
                      "positions": f"TREASFUT5_{slug}_positions.csv"},
        }
        metas[slug] = meta
        with open(f"{base}/TREASFUT5_{slug}.meta.json", "w") as f:
            json.dump(meta, f, indent=1, default=str)
    with open(f"{wrk}/round5_meta.json", "w") as f:
        json.dump(metas, f, indent=1, default=str)
    print(f"published {len(metas)} sleeve csvs + positions + metas (pins ok)")


if __name__ == "__main__":
    run_all()
