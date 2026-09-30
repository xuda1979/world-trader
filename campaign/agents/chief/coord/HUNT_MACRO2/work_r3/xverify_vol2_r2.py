#!/usr/bin/env python3
"""HUNT_MACRO2 round 3, charter 3(c): independent cross-verification of HUNT_VOL2's
round-2 negatives (34 champion-overlay variants, claimed 0/34 pass dAnn>+0.3pp).

Independent = re-derive the gate construction + arithmetic from the SPEC in their
docstrings (round2_scan.py + vol2_lib2.py), do NOT import their lib. Inputs are the
same on-disk data (champion CSV, more_vol CBOE closes). Compare vs their saved
vol2_round2_scan.csv; a variant 'CONFIRMS' if |dAnn_mine - dAnn_theirs| < 0.05pp and
both sides of the acceptance bar agree (both < +0.3pp = their negative stands).

Acceptance bar is THEIR charter bar (dAnn_geo > +0.3pp net) — I check the sign/bar
verdict, not my own charter (this is an overlay family, not a standalone sleeve).
"""
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
THEIRS = f"{ROOT}/campaign/agents/chief/coord/HUNT_VOL2/sleeves/vol2_round2_scan.csv"

GEAR, COST = 1.6, 6.4e-4

CH = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                 index_col=0, parse_dates=True).iloc[:, 0].astype(float)


def vol(name):
    df = pd.read_csv(f"{ROOT}/tools/quant/data/more_vol/{name}.csv", parse_dates=["date"])
    s = df.set_index("date")["close"].astype(float)
    s = s[s > 0]
    if name == "VVIX":
        s = s[s.index >= "2007-01-01"]
    return s[~s.index.duplicated(keep="last")].sort_index()


# ---- arithmetic re-derived from their docstrings (NOT imported) ---------------
def overlay_net(g, r):
    """Overlay on the champion: champion returns are ALREADY the gross-1.6 book
    return, so scaling is p_t = g_{t-1} (in [0,1]) times r; cost = 6.4bps x
    |dW| = 6.4bps x 1.6 x |dp|, day-0 vs the flat-1.6 champion seed (p_{-1}=1).
    (First draft multiplied p by GEAR too — double-scaling; caught by the
    cross-check itself: gates matched exactly, pnl could not.)"""
    g = g.reindex(r.index)
    p = g.shift(1).fillna(1.0)
    to = p.diff().abs()
    if len(p):
        to.iloc[0] = abs(p.iloc[0] - 1.0)
    return p * r.reindex(p.index).fillna(0.0) - to * COST * GEAR


def geo_ann(r):
    r = r.dropna()
    return float((1 + r).prod() ** (252 / len(r)) - 1.0) if len(r) else 0.0


def mdd(r):
    nav = (1 + r.dropna()).cumprod()
    return float((nav / nav.cummax() - 1).min())


def gate_stats(g, r):
    g = g.reindex(r.index).fillna(1.0)
    trig = g < 1.0 - 1e-12
    eps = int((trig & ~trig.shift(1, fill_value=False)).sum())
    return dict(trigger_frac=float(trig.mean()), n_trig=eps)


def expanding_q(d, q, minp):
    return d.expanding(min_periods=minp).quantile(q)


def sustained(c, k):
    return c.rolling(k).apply(lambda x: int(x.all()), raw=True).fillna(0).astype(bool)


def hold_after(trig, hold):
    return trig.rolling(hold + 1, min_periods=1).max().fillna(0).astype(bool)


def expanding_z(d, minp=252):
    mu = d.expanding(min_periods=minp).mean()
    sd = d.expanding(min_periods=minp).std(ddof=1)
    return (d - mu) / sd.replace(0.0, np.nan)


# ---- rebuild all 34 gates exactly per their spec ------------------------------
def build_variants():
    ch = CH
    vvix, skew = vol("VVIX"), vol("SKEW")
    v9, v3m = vol("VIX9D"), vol("VIX3M")
    out = []

    # (a) VVIX expanding-z spike x champion trailing-return drawdown conditional
    vv = vvix.reindex(ch.index).ffill()
    zexp = expanding_z(vv, minp=252)
    for w in (10, 20, 60):
        tr = (1 + ch).rolling(w).apply(np.prod, raw=True) - 1.0
        for thr in (1.5, 2.0, 2.5):
            cond = (zexp > thr) & (tr.fillna(1.0) < 0)
            for lvl in (0.0, 0.5):
                g = pd.Series(1.0, index=ch.index)
                g[cond.fillna(False)] = lvl
                out.append((f"A|vvixZexp>{thr}|trail{w}ret<0|to{lvl}", g))

    # (b) SKEW 5d-change tail gate, hold H days, gross 1.6 -> 1.0
    sk = skew.reindex(ch.index).ffill()
    chg5 = sk.diff(5)
    for q in (0.95, 0.98, 0.99):
        thrq = expanding_q(chg5, q=q, minp=252)
        for hold in (5, 10, 15):
            trig = (chg5 > thrq).fillna(False)
            h = hold_after(trig, hold)
            g = pd.Series(np.where(h, 1.0 / 1.6, 1.0), index=ch.index)
            out.append((f"B|skewchg5>expq{q}|hold{hold}|gross1.6->1.0", g))
    # abs-tail control
    thrq = expanding_q(chg5.abs(), q=0.98, minp=252)
    trig = (chg5.abs() > thrq).fillna(False)
    h = hold_after(trig, 10)
    g = pd.Series(np.where(h, 1.0 / 1.6, 1.0), index=ch.index)
    out.append(("B|skew|chg5|>expq0.98|hold10|gross1.6->1.0", g))

    # (c) VIX9D > VIX3M inversion sustained k days
    i9, i3 = v9.reindex(ch.index).ffill(), v3m.reindex(ch.index).ffill()
    inv = (i9 > i3).fillna(False)
    live = i9.notna() & i3.notna()
    for k in (1, 3, 5):
        s = sustained(inv, k)
        for lvl in (0.0, 0.5):
            g = pd.Series(np.where(s & live, lvl, 1.0), index=ch.index)
            out.append((f"C|9d>3m_sust{k}|to{lvl}", g))
    return out


def main():
    theirs = pd.read_csv(THEIRS).set_index("name")
    # their CSV quotes the name field -> literal "'" chars in the index; strip both sides
    theirs.index = theirs.index.str.strip("'")
    mine = {}
    for name, g in build_variants():
        net = overlay_net(g, CH)
        j = pd.concat([net.rename("a"), CH.rename("b")], axis=1, join="inner").dropna()
        d = (geo_ann(j.a) - geo_ann(j.b)) * 100
        dm = (mdd(j.a) - mdd(j.b)) * 100
        mine[name] = dict(d_ann_mine=d, d_mdd_mine=dm, **gate_stats(g, CH))
    df = pd.DataFrame(mine).T
    th = theirs.rename(columns={"trigger_frac": "trigger_frac_theirs",
                                "n_trig": "n_trig_theirs"})
    j = th.join(df, how="outer")

    assert len(j) == 34 and j["d_ann_mine"].notna().all(), "name alignment failed"
    j["absdiff"] = (j["d_ann_geo_pp"] - j["d_ann_mine"]).abs()
    j["verdict_agree"] = (j["d_ann_geo_pp"] < 0.3) == (j["d_ann_mine"] < 0.3)
    ok = j["absdiff"] < 0.05

    print(f"variants compared: {len(j)} (theirs {len(theirs)}, mine {len(df)})")
    print(f"  |dAnn diff| < 0.05pp: {int(ok.sum())}/{len(j)}")
    print(f"  verdict-agree (same side of +0.3pp bar): {int(j.verdict_agree.sum())}/{len(j)}")
    print(f"  max |dAnn diff|:  {j.absdiff.max():.6f}pp")
    print(f"  max |dMDD diff|:  {(j['d_mdd_pp'] - j['d_mdd_mine']).abs().max():.6f}pp")
    print(f"  max |trig_frac diff|: {(j['trigger_frac_theirs'] - j['trigger_frac']).abs().max():.2e}")
    bad = j[~(ok & j.verdict_agree)]
    if len(bad):
        print("\nDISAGREEMENTS:")
        print(bad[["d_ann_geo_pp", "d_ann_mine", "absdiff", "d_mdd_pp", "d_mdd_mine",
                   "trigger_frac_theirs", "trigger_frac"]].to_string())
    print(f"\nTHEIR headline: best dAnn = {theirs.d_ann_geo_pp.max():+.3f}pp "
          f"(< +0.3pp bar on all {len(theirs)}), {int((theirs.d_ann_geo_pp > 0.3).sum())} pass")
    print(f"MY recompute : best dAnn = {df.d_ann_mine.max():+.3f}pp, "
          f"{int((df.d_ann_mine > 0.3).sum())} pass -> their NEGATIVE "
          f"({'CONFIRMED' if (df.d_ann_mine > 0.3).sum() == 0 else 'REFUTED'})")

    df.to_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r3/"
              f"xverify_vol2_r2_mine.csv")


if __name__ == "__main__":
    main()
