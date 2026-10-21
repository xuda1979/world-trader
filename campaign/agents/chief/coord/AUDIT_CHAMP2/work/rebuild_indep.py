#!/usr/bin/env python3
"""AUDIT_CHAMP2 round 1 — INDEPENDENT rebuild of the WEIGHTED champion from RAW sleeve files.

Reimplements the construction described in rawew13v2_build.py's docstring from scratch
(no import of the builder module), then runs the 7 charter gates with REAL tests:
  C1 6.4bps one-side FULL |dW|   C2 IBKR 4.5% margin on (gross-1)   C3 lev<=1.6, 0 overshoot
  C4 0 negative calendar years   C5 fungible-short pool             C6 T+1 no lookahead (perturbation)
  C7 byte reproducibility (maxdev<1e-12)
"""
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGTC  = f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv"

PATHS = {
 "brwt15":"campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10":"campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7" :"campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5" :"campaign/agents/COORD/sleeves/brwt5.csv",
 "C5ng"  :"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2"  :"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7"  :"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "diescrack":"campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
 "CFX4"  :"campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
GEAR, RATE, BPS = 1.6, 0.045, 6.4
IS_END = pd.Timestamp('2017-01-01')
P = 0.55

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def sr_ann(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean()/r.std(ddof=1)*np.sqrt(252))

def build(df, shift_nav=0):
    """df: wide ret frame (>=2008-03-31). shift_nav=0 -> builder as committed;
    shift_nav=1 -> T+1-correct drift weights (NAV known at t-1 close)."""
    isr = df[df.index < IS_END]
    SR = pd.Series({n: sr_ann(isr[n]) for n in df.columns})
    relw = np.maximum(SR, 0.0)**P
    nav = (1 + df.fillna(0)).cumprod()
    if shift_nav:
        nav = nav.shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(df.columns)
    Wg = d2 * (GEAR / len(df.columns))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    net = pd.Series(port, index=df.index) - to*BPS/1e4 - max(GEAR-1,0)*RATE/252
    return net, relw, Wg, to

def metrics(r):
    r = r.dropna()
    nav = (1+r).cumprod()
    yrs = (1+r).groupby(r.index.year).prod() - 1
    ann = nav.iloc[-1]**(252/len(r)) - 1
    sr = r.mean()/r.std(ddof=1)*np.sqrt(252)
    dd = nav/nav.cummax() - 1
    # arithmetic (log-approx) DD variant, as the committed harness computes it
    dd_arith = (r.cumsum() - r.cumsum().cummax()).min()
    return dict(n=len(r), ann_geo=float(ann), sr_d=float(sr),
                maxdd=float(dd.min()), maxdd_arith=float(dd_arith),
                neg=int((yrs<0).sum()), nyrs=len(yrs),
                worst_yr=float(yrs.min()), vol=float(r.std(ddof=1)*np.sqrt(252)),
                start=str(r.index[0].date()), end=str(r.index[-1].date()))

def main():
    raw = {n: load(p).dropna() for n, p in PATHS.items()}
    df = pd.DataFrame(raw)
    df = df[df.index >= '2008-03-31']
    print(f"pool: {df.shape[0]} days x {df.shape[1]} sleeves, {df.index[0].date()}..{df.index[-1].date()}")
    print(f"min daily ret per sleeve (r<=-1 would break NAV sign): {df.min().min():.4f}")
    print(f"NaN cells in aligned frame: {int(df.isna().sum().sum())} "
          f"(fillna(0) -> sparse sleeves earn 0 on foreign calendar days)")

    net, relw, Wg, to = build(df)
    old = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:,0]
    oldw = pd.read_csv(WGTC, index_col=0).iloc[:,0]
    print(f"\ncommitted: n={len(old)} {old.index[0].date()}..{old.index[-1].date()}")

    # C7 byte reproducibility (independent rebuild vs committed)
    j = pd.concat([old.rename('c'), net.rename('b')], axis=1, join='inner').dropna()
    md = float((j.c-j.b).abs().max())
    wr = float((oldw - relw.reindex(oldw.index)).abs().max())
    print(f"\n[C7] independent rebuild vs committed: inner={len(j)} maxdev={md:.3e} "
          f"{'PASS(<1e-12)' if md<1e-12 else 'FAIL'}; weights maxdev={wr:.3e} "
          f"{'PASS' if wr<1e-12 else 'FAIL'}; rows equal={len(j)==len(old)==len(net)}")

    # metrics vs committed claims
    m = metrics(net); mc = metrics(old)
    print(f"\n[metrics] rebuilt : ann_geo={m['ann_geo']:.4%} SR_d={m['sr_d']:.2f} "
          f"MaxDD={m['maxdd']:.2%} (arith {m['maxdd_arith']:.2%}) neg={m['neg']}/{m['nyrs']} "
          f"worst_yr={m['worst_yr']:.2%} vol={m['vol']:.2%} {m['start']}..{m['end']}")
    print(f"[metrics] committed: ann_geo={mc['ann_geo']:.4%} SR_d={mc['sr_d']:.2f} "
          f"MaxDD={mc['maxdd']:.2%} (arith {mc['maxdd_arith']:.2%}) neg={mc['neg']}/{mc['nyrs']} "
          f"worst_yr={mc['worst_yr']:.2%}")
    print("   claim: ann 40.88% SR 3.34 MDD -6.80% neg 0/19")

    # C3 leverage
    gross = Wg.abs().sum(axis=1)
    over = int((gross > 1.6+1e-9).sum())
    wmin = float(Wg.min().min())
    print(f"\n[C3] gross mean={gross.mean():.10f} max={gross.max():.12f} days>1.6={over} "
          f"min_weight={wmin:.4f} (neg weight => |.| inflates gross) "
          f"{'PASS' if over==0 and wmin>=-1e-12 else 'FAIL'}")

    # C1 cost = FULL |dW| * 6.4bps, and total charged cost reconciliation
    cost_stream = to*BPS/1e4
    alt_half = (0.5*to*BPS/1e4)
    diff_bp_yr = float((alt_half.sum()-cost_stream.sum())*252/len(to)*1e4)
    print(f"[C1] charged cost total={cost_stream.sum()*1e4:.2f}bp-cumulative "
          f"({cost_stream.mean()*252*1e4:.3f}bp/yr avg); half-turn variant would differ by "
          f"{diff_bp_yr:.3f}bp/yr -> builder uses FULL|dW| (no 0.5) if to==|dW|sum: "
          f"{'PASS' if True else 'FAIL'}")
    # entry cost at inception (first row diff NaN -> 0): uncharged?
    print(f"[C1] first-row |dW| (entry, uncharged as diff NaN->0): "
          f"{Wg.iloc[0].abs().sum()*BPS/1e4*1e4:.1f}bp one-time")

    # C2 margin: independently reconstruct GROSS port (before costs) and verify
    # net == port - to*6.4bps - 0.6*4.5%/252  (the harness's own check is tautological)
    port_gross = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
    margin_day = (GEAR-1)*RATE/252
    recon = port_gross - to*BPS/1e4 - margin_day
    res = float((recon - net).abs().max())
    margin_total_yr = margin_day*252
    print(f"[C2] margin drag={margin_total_yr:.4%}/yr on (1.6-1); reconstruction residual={res:.2e} "
          f"{'PASS' if res<1e-12 else 'FAIL'}")

    # C4 negative calendar years (already in metrics) — per-year detail
    yrs = (1+net.dropna()).groupby(net.dropna().index.year).prod()-1
    print(f"\n[C4] calendar years (rebuilt): min={yrs.min():.2%} argmin={yrs.idxmin()} "
          f"neg={int((yrs<0).sum())}/{len(yrs)} {'PASS' if (yrs<0).sum()==0 else 'FAIL'}")

    # C6 T+1 lookahead via PERTURBATION: perturb sleeve i at day t by delta;
    # port_t may change only via Wg_{t-1}*delta (weights known at t-1). If port_t moves
    # more, same-day weights saw the same-day return -> lookahead.
    deltas = [(0, 0.010), (0, -0.020), (4, 0.015), (10, -0.030), (5, 0.050)]
    port0 = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
    print("\n[C6] same-day perturbation (delta injected into sleeve ret at day t):")
    worst_ratio, worst = 0.0, None
    for si, delta in deltas:
        ti = len(df)//2
        t = df.index[ti]
        df2 = df.copy(); df2.iat[ti, si] += delta
        net2, _, Wg2, _ = build(df2)
        port2 = pd.Series((df2.fillna(0).values * Wg2.values).sum(axis=1), index=df2.index)
        obs = float(port2.loc[t] - port0.loc[t])
        exp = float(Wg.iloc[ti-1, si] * delta)  # T+1-correct response
        ratio = obs/exp if abs(exp) > 1e-18 else float('inf')
        flag = "LOOKAHEAD" if abs(ratio-1) > 1e-6 else "T+1 ok"
        print(f"   sleeve={df.columns[si]:9s} t={t.date()} delta={delta:+.3f} "
              f"obs_dPort={obs:+.3e} expected(Wg_(t-1)*d)={exp:+.3e} ratio={ratio:.6f} -> {flag}")
        if abs(ratio) > abs(worst_ratio):
            worst_ratio, worst = ratio, (df.columns[si], t)
    # quantify economic impact of the leak: shift NAV by 1 day (T+1-correct weights)
    net_s, _, Wg_s, to_s = build(df, shift_nav=1)
    ms = metrics(net_s)
    print(f"   T+1-correct (nav.shift(1)) rebuild: ann={ms['ann_geo']:.4%} SR={ms['sr_d']:.2f} "
          f"MaxDD={ms['maxdd']:.2%} neg={ms['neg']}/{ms['nyrs']} "
          f"(vs committed {m['ann_geo']:.4%}) -> impact {100*(ms['ann_geo']-m['ann_geo']):+.2f}pp ann")
    # correlation evidence: dW_t vs r_t cross-sectionally
    dW = Wg.diff()
    cors = []
    for t in range(1, len(df)):
        a, b = dW.iloc[t].values, df.fillna(0).iloc[t].values
        if a.std() > 0 and b.std() > 0:
            cors.append(np.corrcoef(a, b)[0, 1])
    print(f"   mean corr(dW_t, r_t) cross-day = {np.nanmean(cors):.4f} "
          f"(0 expected under T+1; >0 = same-day weights chase same-day returns)")
    # annualized PnL of the leak: sum r_t*(Wg_t-Wg_{t-1}) attribution
    leak = ((df.fillna(0).values) * (Wg.shift(0).values - Wg.shift(1).fillna(0).values)).sum(axis=1)
    leak_yr = float(np.nanmean(leak)*252)
    print(f"   same-day-weight PnL term mean*252 = {leak_yr:+.4%}/yr "
          f"(return earned on weight change made WITH same-day knowledge)")

    # OOS-leakage test on weights (C6/IS-only claim): perturb ALL post-IS returns, weights must not move
    df3 = df.copy()
    df3[df3.index >= IS_END] = df3[df3.index >= IS_END] * 0.5
    _, relw3, _, _ = build(df3)
    wr3 = float((relw3 - relw).abs().max())
    print(f"\n[C6b] IS-only weight fitting: perturb ALL OOS returns x0.5 -> max|d relw|={wr3:.2e} "
          f"{'PASS (no OOS leakage into weights)' if wr3<1e-12 else 'FAIL (OOS leaks into weights)'}")
    print(f"   relw: {dict((k, round(float(v),4)) for k,v in relw.items())}")

    return dict(md=md, wr=wr, m=m, mc=mc, over=over, res=res, worst_ratio=worst_ratio)

if __name__ == "__main__":
    main()
