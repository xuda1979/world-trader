"""HUNT_VOL2 ROUND 2 scan: champion-integrated conditional vol gates.

Families (charter round 2, standup 2026-09-07 01:3x):
  A  VVIX-spike de-risk, CONDITIONAL: VVIX expanding-z > thr AND champ trail-W ret < 0
  B  SKEW 5d-change tail gate: while in expanding-q tail of 5d SKEW jump, hold 10d,
     scale gross 1.6 -> 1.0 (multiplier 0.625)
  C  VIX9D > VIX3M inversion sustained k days -> de-risk (VIX9D starts 2011, honest note)

pos = 1.6 * gate, T+1 on gate; costs incremental 6.4bps one-side on FULL |dW| with
p_{-1}=1 (champion built flat 1.6 day 0) — champion-identical convention, test-enforced.
Bar: dAnn_geo > +0.3pp net of costs; report dMDD, dWorstYr, trigger stats, null_trim_p.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_VOL2/scratch")
import numpy as np, pandas as pd
import vol2_lib2 as L2

rows = []


def expanding_z(d, minp=252):
    mu = d.expanding(min_periods=minp).mean()
    sd = d.expanding(min_periods=minp).std(ddof=1)
    return (d - mu) / sd.replace(0.0, np.nan)


def run(name, gate, ch, r_note=""):
    gate = gate.reindex(ch.index).fillna(1.0)
    net = L2.overlay_net(gate, ch)
    d = L2.deltas(net, ch)
    st = L2.gate_stats(gate, ch)
    p = L2.null_trim_p(gate, ch, n=200, seed=7) if st["trigger_frac"] > 0 else float("nan")
    line = L2.fmt(name, st, d, extra=f"nullTrimP={p:.3f} {r_note}")
    rows.append(dict(name=name, **st, **d, null_p=p))
    print(line, flush=True)
    return net


def main():
    ch = L2.champion()
    vvix, skew = L2.vol("VVIX"), L2.vol("SKEW")
    v9, v3m = L2.vol("VIX9D"), L2.vol("VIX3M")

    print(f"CHAMPION base: geoAnn={L2.geo_ann(ch)*100:.2f}% MDD={L2.mdd(ch)*100:.2f}% "
          f"worstYr={L2.worst_year(ch)*100:.2f}% n={len(ch)}", flush=True)
    print("=" * 110, flush=True)

    # ---------------- (a) VVIX spike x champ-drawdown conditional de-risk ----------
    vv = vvix.reindex(ch.index).ffill()
    zexp = expanding_z(vv, minp=252)
    for w in (10, 20, 60):
        tr = L2.trail_ret(ch, w)
        for thr in (1.5, 2.0, 2.5):
            cond = (zexp > thr) & (tr.fillna(1.0) < 0)
            for lvl in (0.0, 0.5):
                g = pd.Series(1.0, index=ch.index)
                g[cond.fillna(False)] = lvl
                run(f"A|vvixZexp>{thr}|trail{w}ret<0|to{lvl}", g, ch)

    # ---------------- (b) SKEW 5d-change tail gate, hold H days, 1.6->1.0 ---------
    sk = skew.reindex(ch.index).ffill()
    chg5 = sk.diff(5)
    for q in (0.95, 0.98, 0.99):
        thrq = L2.expanding_q(chg5, q=q, minp=252)
        for hold in (5, 10, 15):
            trig = (chg5 > thrq).fillna(False)
            h = L2.hold_after(trig, hold)
            g = pd.Series(np.where(h, 1.0 / 1.6, 1.0), index=ch.index)
            run(f"B|skewchg5>expq{q}|hold{hold}|gross1.6->1.0", g, ch)
    # positive-only vs abs-tail control: abs tail
    for q in (0.98,):
        thrq = L2.expanding_q(chg5.abs(), q=q, minp=252)
        for hold in (10,):
            trig = (chg5.abs() > thrq).fillna(False)
            h = L2.hold_after(trig, hold)
            g = pd.Series(np.where(h, 1.0 / 1.6, 1.0), index=ch.index)
            run(f"B|skew|chg5|>expq{q}|hold{hold}|gross1.6->1.0", g, ch)

    # ---------------- (c) VIX9D > VIX3M inversion sustained k -> de-risk ----------
    i9 = v9.reindex(ch.index).ffill()
    i3 = v3m.reindex(ch.index).ffill()
    inv = (i9 > i3).fillna(False)
    # usable window only where BOTH series live (VIX9D starts 2011-01-04)
    live = i9.notna() & i3.notna()
    for k in (1, 3, 5):
        s = L2.sustained(inv, k)
        for lvl in (0.0, 0.5):
            g = pd.Series(np.where(s & live, lvl, 1.0), index=ch.index)
            run(f"C|9d>3m_sust{k}|to{lvl}", g, ch, r_note="(VIX9D era 2011+)")

    print("=" * 110, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv("/tmp/vol2_round2_scan.csv", index=False)
    ok = df[df.d_ann_geo_pp > 0.3]
    print(f"TOTAL {len(df)} variants; dAnn_geo>+0.3pp: {len(ok)}", flush=True)
    if len(ok):
        print(ok.sort_values("d_ann_geo_pp", ascending=False).to_string(), flush=True)
    print("BEST by dAnn:", df.loc[df.d_ann_geo_pp.idxmax()].to_dict(), flush=True)


if __name__ == "__main__":
    main()
