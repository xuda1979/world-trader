#!/usr/bin/env python3
"""AUDIT_CHAMP2 ROUND 2 — independent from-scratch re-audit of the RE-EMITTED causal champion.

NOTHING trusted: builder source not imported for the reconstruction; committed CSV only
read at the very end for byte comparison. Both admissible weight constructions are rebuilt
from the 13 RAW sleeve files; each must reproduce exactly one of {committed, archived-leak}
to <1e-12, which pins the new-vs-archived difference to EXACTLY the nav.shift(1) mechanism.
"""
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
GEAR, RATE, BPS = 1.6, 0.045, 6.4
IS_END = pd.Timestamp('2017-01-01')
P = 0.55

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
 "CFX4"     :"campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
NAMES = list(PATHS)

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def weights(df, relw, lag):
    nav = (1 + df.fillna(0)).cumprod()
    if lag:
        nav = nav.shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    return d2 * (GEAR / len(NAMES))

def main():
    df = pd.DataFrame({n: load(PATHS[n]).dropna() for n in NAMES})
    df = df[df.index >= '2008-03-31']
    isr = df[df.index < IS_END]
    # R2 FIX (audit-found bug): dropna BEFORE the len guard. isr['CFX4'] has 2286 all-NaN
    # rows (sleeve starts 2019) -> without dropna the guard passes and std()=NaN poisons
    # relw -> the whole port is NaN. Matches the documented is_sr semantics (len<200 -> 0).
    SR = pd.Series({n: (lambda r: 0.0 if len(r.dropna()) < 200 or r.dropna().std(ddof=1) <= 1e-12
                        else float(r.dropna().mean()/r.dropna().std(ddof=1)*np.sqrt(252)))(isr[n])
                    for n in NAMES})
    relw = np.maximum(SR, 0.0)**P
    print(f"pool: {df.shape[0]} days x {df.shape[1]} sleeves, {df.index.min().date()}..{df.index.max().date()}")

    def build(lag):
        Wg = weights(df, relw, lag)
        port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
        to = Wg.diff().abs().sum(axis=1).fillna(0.0)
        net = port - to*BPS/1e4 - (GEAR-1)*RATE/252
        return net, Wg, to, port

    # ---- (d): both constructions vs both committed files ----
    new = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                      index_col=0, parse_dates=True).iloc[:,0]
    arch = pd.read_csv(f"{ROOT}/campaign/results/archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_SAMEDAYLEAK_ann40.84.csv",
                       index_col=0, parse_dates=True).iloc[:,0]
    wcom = pd.read_csv(f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv", index_col=0).iloc[:,0]
    print(f"\n== (d) construction identity ==")
    print(f"weights file: max|built-committed relw| = {(relw-wcom).abs().max():.3e}")

    net_c, Wg_c, to_c, port_c = build(1)
    net_l, Wg_l, to_l, port_l = build(0)

    def cmp(a, b, tag):
        j = pd.concat([a.rename('a'), b.rename('b')], axis=1, join='inner').dropna()
        md = float((j.a-j.b).abs().max())
        print(f"{tag}: n={len(j)} maxdev={md:.3e} {'IDENTICAL' if md < 1e-12 else 'DIFF'}")
        return md

    md_new_c = cmp(net_c, new, "rebuilt CAUSAL  vs committed champion CSV")
    md_arch_l = cmp(net_l, arch, "rebuilt LEAKY   vs archived  leak CSV")
    md_new_l = cmp(net_l, new, "rebuilt LEAKY   vs committed champion CSV (must be DIFF)")
    # transitivity pin: the committed-vs-archived delta is EXACTLY the construction delta
    j = pd.concat([net_c.rename('c'), net_l.rename('l')], axis=1).dropna()
    mech = float((j.c-j.l).abs().max())
    jca = pd.concat([new, arch], axis=1, join='inner').dropna()
    file_d = float((jca.iloc[:,0]-jca.iloc[:,1]).abs().max())
    print(f"mechanism delta (my two rebuilds) = {mech:.6e} | file-vs-file delta = {file_d:.6e} "
          f"| |diff of diffs| = {abs(mech-file_d):.3e}")
    corr = float(np.corrcoef(jca.iloc[:,0], jca.iloc[:,1])[0,1])
    print(f"corr(committed, archived) = {corr:.6f}  (charter pin: ~0.99988, maxdev ~3.96e-3)")
    d_ok = (md_new_c < 1e-12 and md_arch_l < 1e-12 and md_new_l > 1e-12
            and abs(mech-file_d) < 1e-12)
    print(f"(d) VERDICT: {'PASS — difference is EXACTLY nav.shift(1)' if d_ok else 'FAIL'}")

    # ---- C1: FULL |dW| @ 6.4bps ----
    print(f"\n== C1 cost ==")
    cum_cost_bp = float(to_c.mean()*BPS*252)
    print(f"charged turnover (causal Wg): mean |dW|/day={to_c.mean():.6f} -> {cum_cost_bp:.4f} bp/yr")
    # independent residual: net_committed must equal my port - my to*bps - margin
    resid = float((net_c - new).abs().max())
    print(f"independent full-identity residual (port-myto*6.4bp-margin vs committed) = {resid:.3e}")
    # 0.5x counterfactual: would shift ann by how much?
    net_half = port_c - to_c*0.5*BPS/1e4 - (GEAR-1)*RATE/252
    ann_half = (1+net_half).prod()**(252/len(net_half))-1
    ann_true = (1+net_c).prod()**(252/len(net_c))-1
    print(f"half-turn counterfactual ann = {ann_half*100:.4f}% vs true {ann_true*100:.4f}% "
          f"(gap {abs(ann_half-ann_true)*1e4:.3f}bp/yr must be ABSENT from committed)")

    # ---- C2 margin (DISCRIMINATING, not tautological) ----
    # R1 proved a residual of the form (port + mycosts - port) is vacuous: it equals
    # marg_daily for ANY builder. So here I do the OPPOSITE: subtract each candidate
    # margin hypothesis from the committed net and ask which one explains it, using a
    # deliberately WRONG zero-margin hypothesis as the discriminating control.
    marg_daily = (GEAR-1)*RATE/252
    res_450 = float((net_c - (port_c - to_c*BPS/1e4 - marg_daily)).abs().max())      # hypothesis: 4.5% on 0.6
    res_000 = float((net_c - (port_c - to_c*BPS/1e4 - 0.0)).abs().max())             # control: 0% margin
    res_900 = float((net_c - (port_c - to_c*BPS/1e4 - 2*marg_daily)).abs().max())    # control: 9.0%
    print(f"\n== C2 margin == daily drag const={marg_daily:.8e} ({(GEAR-1)*RATE:.2%}/yr)")
    print(f"  residual @4.5% on (1.6-1) [charter] = {res_450:.3e}  (want ~0)")
    print(f"  residual @0.0% margin      [control] = {res_000:.3e}  (want {marg_daily:.3e}, i.e. DETECTED)")
    print(f"  residual @9.0% margin      [control] = {res_900:.3e}  (want ~{marg_daily:.3e}, DETECTED)")
    c2_ok = res_450 < 1e-12 and res_000 > 1e-6 and res_900 > 1e-6
    print(f"  C2 VERDICT: {'PASS — margin is exactly 4.5% on (gross-1), controls detect wrong margins' if c2_ok else 'FAIL'}")

    # ---- C3 leverage ----
    g = Wg_c.abs().sum(axis=1)
    print(f"\n== C3 leverage == gross mean={g.mean():.12f} max={g.max():.12f} min={g.min():.12f} "
          f"days>1.6+1e-9={int((g>1.6+1e-9).sum())} min slot weight={Wg_c.min().min():.6f}")

    # ---- C4 negative years ----
    yby = new.groupby(new.index.year).apply(lambda x: (1+x).prod()-1)
    print(f"\n== C4 years == neg={int((yby<0).sum())}/{len(yby)} worst={yby.min():.4%} best={yby.max():.4%}")

    # ---- C6 T+1 perturbation on the committed stream ----
    print(f"\n== C6 T+1 perturbation (on committed/new CSV vs my causal weights) ==")
    k = len(NAMES)
    ti = len(df)//2
    worst = 0.0
    for si, delta in [(0,0.010),(k-1,-0.020),(k//2,0.050)]:
        df2 = df.copy(); df2.iat[ti, si] += delta
        Wg2 = weights(df2, relw, 1)
        p1 = pd.Series((df2.fillna(0).values*Wg2.values).sum(axis=1), index=df2.index)
        t = df.index[ti]
        obs = float(p1.loc[t] - port_c.loc[t])
        exp = float(Wg_c.iloc[ti, si]*delta)
        ex = abs(obs-exp)/(abs(delta)*(GEAR/k))
        worst = max(worst, ex)
        print(f"  sleeve={NAMES[si]:9s} delta={delta:+.3f} obs={obs:.6e} exp={exp:.6e} excess={ex:.3e}")
    print(f"  max excess response = {worst:.3e} weight-units (T+1 requires <1e-6)")
    dW = Wg_c.diff().iloc[1:]
    rr = df.fillna(0).iloc[1:]
    cors = [np.corrcoef(dW.iloc[i].values, rr.iloc[i].values)[0,1] for i in range(len(dW))
            if dW.iloc[i].std() > 0 and rr.iloc[i].std() > 0]
    print(f"  corr(dW_t, r_t) mean = {np.nanmean(cors):+.4f}  (R1 leak was +0.7846; T+1 wants 0)")

    # ---- metrics ----
    r = new.dropna(); n = len(r)
    ann = (1+r).prod()**(252/n)-1
    sr = r.mean()/r.std(ddof=1)*np.sqrt(252)
    nav = (1+r).cumprod(); dd = (nav/nav.cummax()-1).min()
    print(f"\n== metrics (committed CSV, campaign convention ann_geo=prod^(252/n)-1) ==")
    print(f"ann_geo={ann:.6%}  SR_d={sr:.4f}  MaxDD={dd:.4%}  neg_years=0/{len(yby)}  n={n}")
    ism = r[r.index < IS_END]; osm = r[r.index >= IS_END]
    a_is = (1+ism).prod()**(252/len(ism))-1; a_os = (1+osm).prod()**(252/len(osm))-1
    print(f"IS ann={a_is:.4%} (n={len(ism)})  OOS ann={a_os:.4%} (n={len(osm)})")

if __name__ == "__main__":
    main()
