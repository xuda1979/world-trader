"""CAMP_COST R3 (c') — RE-EMIT CANDIDATE champions into work_r3 (NOT results/, NOT committed).

Two candidates for the coordinator's re-emit wave:
  CANDIDATE 13SLOT : 13 sleeves, brwt10/7/5 swapped for the corrected FULL|dW|@6.4bps CSVs.
  CANDIDATE 10SLOT : brwt10/7/5 DROPPED (10 sleeves) — coordinator's "drop or fix" option.

Both built by the SAME independent recipe verified byte-exact vs the committed champion
(work_r3/reverify_champ.py, maxdev 9.996e-17): IS-SR^0.55 relw (IS_END<2017-01-01) recomputed
from the CURRENT pool streams, nav-drift row-normalized, nav.shift(1) causal, gross 1.6x,
FULL |dW| @ 6.4bps one-side, day-1 entry uncharged, borrow (1.6-1)*4.5%/252.

Per-slot cost at champion level: turnover attribution (see turnover_attribution.py).
READ-ONLY outside CAMP_COST/work_r3/.
"""
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
SL = f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves"
OUT = f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/work_r3"

GEAR, RATE, BPS = 1.6, 0.045, 6.4
IS_END = pd.Timestamp("2017-01-01")
P = 0.55

POOL = {
    "brwt15": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "brwt10": f"{SL}/brwt10_2000__costfix.csv",
    "brwt7": f"{SL}/brwt7__costfix.csv",
    "brwt5": f"{SL}/brwt5__costfix.csv",
    "C5ng": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2": f"{ROOT}/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "a6r7": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "carryv2": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom": f"{ROOT}/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack": f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4": f"{ROOT}/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
DROP = {"brwt10", "brwt7", "brwt5"}  # 10-slot variant drops the unrecoverable-vintage family


def load(p):
    df = pd.read_csv(p, index_col=0)
    df.index = pd.to_datetime(df.index)
    col = "ret" if "ret" in df.columns else df.columns[0]
    s = pd.to_numeric(df[col], errors="coerce").astype(float)
    return s[s.notna()]


def build(pool_names):
    data = {n: load(POOL[n]) for n in pool_names}
    df = pd.DataFrame({n: s[s.index >= "2008-03-31"] for n, s in data.items()})
    ris = df[df.index < IS_END]
    SR = pd.Series({n: (ris[n].mean() / ris[n].std(ddof=1) * np.sqrt(252)
                        if ris[n].notna().sum() > 200 and ris[n].std(ddof=1) > 1e-12 else 0.0)
                    for n in df.columns})
    relw = np.maximum(SR, 0.0) ** P
    nav = (1 + df.fillna(0)).cumprod().shift(1)
    nav.iloc[0] = 1.0
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(df.columns)
    Wg = d2 * (GEAR / len(df.columns))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = Wg.diff().abs().sum(axis=1)
    to.iloc[0] = 0.0
    net = pd.Series(port, index=df.index) - to * BPS / 1e4 - (GEAR - 1) * RATE / 252
    return net, relw, Wg, df


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    dd = nav / nav.cummax() - 1
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return dict(n=len(r), ann=float(nav.iloc[-1] ** (252 / len(r)) - 1),
                sr=float(r.mean() / r.std(ddof=1) * np.sqrt(252)), mdd=float(dd.min()),
                neg_years=int((yr < 0).sum()), worst_year=float(yr.min()))


def gate_table(r):
    """FULL-gate table per GATES_CONTRACT for the composite (informational; composite-level)."""
    r = r.dropna()
    mid = r.index[len(r) // 2]
    h1 = r[r.index <= mid]
    h2 = r[r.index > mid]
    sr = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(252)
    oos = r[r.index >= "2017-01-01"]
    oos_ann = (1 + oos).prod() ** (252 / len(oos)) - 1
    return dict(SR_full=sr(r), SR_H1=sr(h1), SR_H2=sr(h2),
                SR_OOS17=sr(oos), ann_OOS17=oos_ann)


def main():
    committed = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                            index_col=0, parse_dates=True).iloc[:, 0]
    st_c = stats(committed)

    net13, relw13, Wg13, _ = build(list(POOL.keys()))
    ten = [n for n in POOL if n not in DROP]
    net10, relw10, Wg10, _ = build(ten)

    for tag, net in [("candidate13slot", net13), ("candidate10slot", net10)]:
        out = pd.DataFrame({"ret": net.values}, index=net.index).rename_axis("date")
        out.to_csv(f"{OUT}/{tag}.csv")
        st = stats(net)
        g = gate_table(net)
        j = pd.concat([committed.rename("c"), net.rename("n")], axis=1, join="inner").dropna()
        print(f"== {tag}: n={st['n']} ann={st['ann']*100:.2f}% SR={st['sr']:.3f} "
              f"MDD={st['mdd']*100:.2f}% neg={st['neg_years']} worst_yr={st['worst_year']*100:.2f}%")
        print(f"   gates: SR_H1={g['SR_H1']:.2f} SR_H2={g['SR_H2']:.2f} "
              f"OOS17 ann={g['ann_OOS17']*100:.2f}% SR={g['SR_OOS17']:.2f}")
        print(f"   vs committed: ann {st_c['ann']*100:+.2f} -> {st['ann']*100:.2f} "
              f"({(st['ann']-st_c['ann'])*100:+.3f}pp), SR {st_c['sr']:.3f} -> {st['sr']:.3f}, "
              f"MDD {st_c['mdd']*100:.2f} -> {st['mdd']*100:.2f}, "
              f"max|cand-committed|={float((j.c-j.n).abs().max()):.3e}")
    print(f"\nrelw13 brwt slots: " + ", ".join(f"{k}={relw13[k]:.3f}" for k in ("brwt10", "brwt7", "brwt5")))
    print(f"relw10 (family dropped): " + ", ".join(f"{k}={relw10[k]:.3f}" for k in list(relw10.index)[:4]) + " ...")
    print("wrote candidate13slot.csv / candidate10slot.csv to work_r3/ (NOT results/)")


if __name__ == "__main__":
    main()
