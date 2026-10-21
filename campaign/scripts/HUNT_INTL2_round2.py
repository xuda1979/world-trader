#!/usr/bin/env python3
"""HUNT_INTERNATIONAL2 round 2 — SPY/EWH/EWM relative-strength rotation + VIXCLS de-risk gate.

Charter (round 2, the LAST international attempt): rotate US-vs-HK-vs-China equity exposure
(SPY/EWH/EWM) by 126d RS momentum with vol-targeting and a VIXCLS de-risk gate. Max ~9 configs.

Honesty per GATES_CONTRACT.md:
 T+1 (weights = target.shift(1)); costs 6.4bps on FULL |dW| + 0.5%/yr borrow on short notional;
 vol-target 10% trailing expanding (clip <= 3.0); scramble 200x on FINAL weights with re-costing;
 halves H1,H2 >= 0.5; <= 2 neg years each > -5%; FULL net SR >= 1.0; |corr| < 0.15 vs champion.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
from bt import engine, metrics
import bt.gates as bgates

ROOT = "/Users/daxu/software/world-trader"
COST_BPS = 6.4
COLS = ["SPY", "EWH", "EWM"]
CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]


def load_close(path, col="close"):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df[col].astype(float)


def px_frame():
    """SPY (twelvedata) + EWH/EWM (more_etf), aligned on common dates >= 2006-10-19."""
    spy = load_close(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv")
    ewh = load_close(f"{ROOT}/tools/quant/data/more_etf/EWH.csv")
    ewm = load_close(f"{ROOT}/tools/quant/data/more_etf/EWM.csv")
    px = pd.concat({"SPY": spy, "EWH": ewh, "EWM": ewm}, axis=1).sort_index().dropna()
    return px


# ---------------- machinery (TDD-tested) ----------------
def rs_signal(px, lookback):
    """Relative strength of SPY vs the HK/CN basket, trailing only:
       RS_t = (SPY/basket).shift(lb) / (SPY/basket).shift(2*lb) - 1.
       Uses only prices <= t (shifted), so a t-dated row is T+1-safe as a trade input."""
    rel = px["SPY"] / px[["EWH", "EWM"]].mean(axis=1)
    return rel.shift(lookback) / rel.shift(2 * lookback) - 1.0


def vix_gate(vix, threshold, window=21, floor=0.25):
    """Trailing mean of VIX (last `window` obs up to t-1) below threshold -> 1.0, else floor.
       shift(1) so state_t uses VIX <= t-1 only. Fail-CLOSED: unknown state -> floor."""
    trail = vix.rolling(window, min_periods=window).mean().shift(1)
    return trail.map(lambda v: floor if (pd.isna(v) or v >= threshold) else 1.0)


def apply_vix_gate(W, vix, threshold, window=21, floor=0.25):
    """Scale weights by 1.0 (calm) or `floor` (stressed), using trailing-only VIX state."""
    trail = vix.rolling(window, min_periods=window).mean().shift(1)
    state = trail.map(lambda v: 1.0 if (pd.isna(v) or v < threshold) else floor)
    return W.mul(state.reindex(W.index).fillna(1.0), axis=0)


def rotation_weights(px, lookback=126, gross=1.0, mode="LS"):
    """Monthly-rebalanced rotation: rank SPY vs HK/CN basket by trailing RS momentum.
       If SPY RS >= basket RS -> long SPY (LS: short basket half); else long basket.
       Weights are set on the first trading day of each month from the PREVIOUS day's signal."""
    R = px.pct_change()
    spy_px = px["SPY"]
    bsk_px = px[["EWH", "EWM"]].mean(axis=1)
    mom_spy = spy_px.shift(lookback) / spy_px.shift(2 * lookback) - 1
    mom_bsk = bsk_px.shift(lookback) / bsk_px.shift(2 * lookback) - 1
    rs = mom_spy - mom_bsk                     # >0 => SPY stronger over trailing window
    idx = px.index
    reb = set(pd.Series(idx, index=idx).groupby(idx.to_period("M")).first().values)
    W = pd.DataFrame(0.0, index=idx, columns=COLS)
    prev = None
    for i in range(len(idx)):
        if idx[i] in reb and i > 0 and np.isfinite(rs.iloc[i - 1]):
            # build on W's own index — positional .values assignment mis-lands columns
            prev = pd.Series(0.0, index=COLS)
            if rs.iloc[i - 1] >= 0:
                prev["SPY"] = gross if mode == "LO" else gross / 2
                if mode == "LS":
                    prev[["EWH", "EWM"]] = -gross / 4
            else:
                prev[["EWH", "EWM"]] = gross / 2 if mode == "LO" else gross / 4
                if mode == "LS":
                    prev["SPY"] = -gross / 2
        if prev is not None:
            W.iloc[i] = prev.values
    return W


def net_of(W, R, vt=True, target=0.10):
    """T+1 effective weights, trailing vol-target, 6.4bps full |dW| + borrow on shorts."""
    We = W.shift(1).fillna(0.0)
    gross = (We * R).sum(axis=1)
    if vt:
        s = engine.vol_target_scale(gross.to_frame("g"), target=target)["g"]
        We = We.mul(s, axis=0)
    port = (We * R).sum(axis=1)
    cost = engine.cost_turnover(We, cost_bps=COST_BPS)
    borr = engine.borrow_cost(We)
    return (port - cost - borr).rename("ret"), We, gross


def scramble_p(We_final, R, net, n=200, seed=7):
    """Campaign-standard signal scramble: permute FINAL weight rows (shared permutation across
    assets) against real date-aligned returns, RE-APPLY costs, compare SRs. p = P(SR_scr >= real)."""
    idx = net.index
    We = We_final.reindex(idx).fillna(0.0)
    Re = R.reindex(idx).fillna(0.0)
    real_sr = metrics.sharpe_d(net)
    arrW, arrR = We.values, Re.values
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        Wp = pd.DataFrame(arrW[rng.permutation(len(idx))], index=idx, columns=We.columns)
        book = (Wp * Re).sum(axis=1) - engine.cost_turnover(Wp, cost_bps=COST_BPS) - engine.borrow_cost(Wp)
        if metrics.sharpe_d(book) >= real_sr:
            cnt += 1
    return cnt / n


def trim_warmup(net, We):
    """Trim net series to the first day the book is live (|W|>0) — pre-live flat rows would
    dilute SR with synthetic flat days. Fail-closed: a NEVER-live book is a broken build,
    not a zero-SR book (round-2 crash: int-vs-Timestamp `i in reb` left W all-zero)."""
    live = (We.fillna(0.0) != 0).any(axis=1)
    if not live.any():
        raise AssertionError("never-live book: weights all zero — rotation selection is broken")
    return net[net.index >= live.idxmax()]


def evaluate(name, net, We, R, verbose=True):
    net = trim_warmup(net, We)
    sr = metrics.sharpe_d(net); h1, h2 = metrics.half_split(net)
    neg, worst = metrics.neg_years(net)
    p = scramble_p(We, R, net)
    corr = bgates.corr_to(CHAMP, net)
    vol = net.std() * np.sqrt(252)
    res = dict(sr=sr, h1=h1, h2=h2, neg=neg, worst=worst, p=p, corr=corr, vol=vol,
               ann=metrics.ann_geo(net), n=len(net),
               start=net.index[0].date(), end=net.index[-1].date())
    res["ok"] = dict(
        a_sr=res["sr"] >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
        d_yearly=(neg <= 2 and worst > -0.05),
        e_scramble=(p <= 0.05 and res["sr"] > 0),
        f_corr=abs(corr) < 0.15)
    res["pass"] = all(res["ok"].values())
    if verbose:
        ok = res["ok"]
        print(f"[{name}] n={res['n']} {res['start']}->{res['end']} SR={sr:.2f} ann={res['ann']*100:.1f}% "
              f"vol={vol*100:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={neg} worst={worst*100:.1f}% "
              f"scram_p={p:.3f} corrChamp={corr:.3f}")
        print(f"    gates: SR>=1:{ok['a_sr']} halves>=0.5:{ok['c_halves']} yearly:{ok['d_yearly']} "
              f"scramble:{ok['e_scramble']} |corr|<0.15:{ok['f_corr']}  PASS={res['pass']}")
    return res


def build(px, lookback, mode, gate, vix, gate_floor=0.25, gross=1.0):
    R = px.pct_change()
    W = rotation_weights(px, lookback=lookback, gross=gross, mode=mode)
    if gate:
        W = apply_vix_gate(W, vix, threshold=25.0, window=21, floor=gate_floor)
    return net_of(W, R) + (W,)


if __name__ == "__main__":
    px = px_frame()
    vix = load_close(f"{ROOT}/tools/quant/data/more_fred/VIXCLS.csv", col="value")
    print(f"panel: {px.index[0].date()} -> {px.index[-1].date()}  n={len(px)}")
    print(f"VIXCLS: {vix.index[0].date()} -> {vix.index[-1].date()}  n={len(vix)}")

    print("\n=== no-lookahead spot check (end-to-end, lb126) ===")
    probe = px.index[len(px) // 2]
    W_full = rotation_weights(px, 126)
    W_cut = rotation_weights(px.loc[:probe], 126)
    ok = W_full.loc[:probe].round(10).equals(W_cut.round(10))
    print("weights identical with future truncated:", ok)
    assert ok, "LOOKAHEAD DETECTED"

    print("\n=== config grid (<=9): lookback x mode x VIX-gate ===")
    configs = [
        (126, "LS", False),
        (126, "LS", True),
        (126, "LO", False),
        (126, "LO", True),
        (63, "LS", False),
        (63, "LS", True),
        (252, "LS", False),
        (252, "LS", True),
        (126, "LS", True, 0.0),   # full flat de-risk (floor 0)
    ]
    results = {}
    for cfg in configs:
        lb, mode, gate = cfg[0], cfg[1], cfg[2]
        floor = cfg[3] if len(cfg) > 3 else 0.25
        name = f"RS{lb}_{mode}{'_VIXg' + str(floor) if gate else ''}"
        net, We, _, W = build(px, lb, mode, gate, vix, gate_floor=floor)
        results[name] = evaluate(name, net, We, px.pct_change())

    print("\n=== summary (sorted by SR) ===")
    for nm, r in sorted(results.items(), key=lambda kv: -kv[1]["sr"]):
        print(f"  {nm:22s} SR={r['sr']:5.2f} H1={r['h1']:5.2f} H2={r['h2']:5.2f} negyr={r['neg']:2d} "
              f"worst={r['worst']*100:6.1f}% p={r['p']:.3f} corr={r['corr']:6.3f} PASS={r['pass']}")
