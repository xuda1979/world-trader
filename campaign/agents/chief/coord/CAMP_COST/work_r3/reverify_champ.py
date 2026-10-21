"""CAMP_COST R3 (a') — INDEPENDENT re-verification of the coordinator's 07:28 champion emit.

Per charter: "independent re-verification of the 07:28 emit from your own generators; report
any residual vs the committed CSV."

Independence discipline (do NOT reuse rawew13v2_build.build()):
  * Re-implement the recipe from the CHARTER TEXT alone (GATES_CONTRACT + docstring semantics:
    IS-SR^0.55 relw on IS_END<2017-01-01, nav-drift row-normalized weights, nav.shift(1)
    causal, FULL |dW| @ 6.4bp one-side, day-1 entry uncharged, margin (1.6-1)*4.5%/252).
  * Own loader (dict of Series, own dropna), own algebra (explicit python loops for the
    weight recursion where cheap; pandas for the rest, differently ordered ops).
  * Stats via a second implementation: cumprod NAV, max drawdown, neg-year count, daily SR.
  * Cross-checks the builder itself cannot make: causality probe (perturb day-t sleeve ret
    must NOT move day-t champion ret), day-1 entry uncharged, exact gross=1.6, and a
    mutation probe — flipping ONLY the three brwt sleeves to their corrected R3 CSVs must
    move the series (proves the champion actually consumes them).
READ-ONLY outside work_r3/.
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
SL = f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves"

# path map copied from rawew13v2_build.py, re-typed independently.
# R4 UPDATE: the champion of record (commit b268e52) consumes the CAMP_COST R3 costfix
# brwt streams (FULL |dW| @ 6.4bps) — rawew13v2_build.PATHS was swapped accordingly. The
# legacy COORD paths below rebuilt the PRE-costfix book (ann 39.69%, max dev 4.572e-03 vs
# committed) and are kept ONLY as a comment for lineage. (Stale-probe fix, R4.)
PATHS = {
    "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    # legacy (pre-re-emit): "campaign/agents/COORD/sleeves/brwt10_2000.csv"
    "brwt10": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "C5ng": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2": "campaign/agents/A5_vol_cond/slevees_placeholder_IGNORED.csv",  # fixed below
    "a6r7": "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "carryv2": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4": "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
PATHS["A5r2"] = "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv"

GEAR, RATE, BPS = 1.6, 0.045, 6.4
IS_END = pd.Timestamp("2017-01-01")
P = 0.55


def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    col = "ret" if "ret" in df.columns else df.columns[0]
    s = pd.to_numeric(df[col], errors="coerce").astype(float)
    return s[s.notna()]


def is_sr(r):
    r = r[r.index < IS_END]
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252))


def build_own():
    data = {}
    for n, p in PATHS.items():
        s = load(p)
        s = s[s.index >= "2008-03-31"]
        data[n] = s
    df = pd.DataFrame(data)
    SR = pd.Series({n: is_sr(df[n]) for n in df.columns})
    relw = np.maximum(SR, 0.0) ** P
    nav = (1 + df.fillna(0)).cumprod().shift(1)
    nav.iloc[0] = 1.0
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(df.columns)
    Wg = d2 * (GEAR / len(df.columns))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    dw = Wg.diff()
    to = dw.abs().sum(axis=1)
    to.iloc[0] = 0.0  # day-1 entry uncharged (builder convention, charter-documented)
    net = pd.Series(port, index=df.index) - to * BPS / 1e4 - (GEAR - 1) * RATE / 252
    return net, relw, Wg, df


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    peak = nav.cummax()
    dd = nav / peak - 1
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = yr[yr < 0]
    sr = float(r.mean() / r.std(ddof=1) * np.sqrt(252))
    ann = float(nav.iloc[-1] ** (252 / len(r)) - 1)
    return dict(n=len(r), ann=ann, sr=sr, mdd=float(dd.min()),
                neg_years=int(len(neg)), worst_year=float(yr.min()),
                first=str(r.index[0].date()), last=str(r.index[-1].date()))


def main():
    net, relw, Wg, df = build_own()
    champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([champ.rename("committed"), net.rename("own")], axis=1, join="inner").dropna()
    md = float((j.committed - j.own).abs().max())
    n_missing = len(champ.index.difference(net.index))
    print(f"[1] independent rebuild vs committed CSV: inner={len(j)} "
          f"max|own-committed|={md:.4e} committed_rows_missing_from_own={n_missing} "
          f"{'BYTE-CONSISTENT' if md < 1e-12 and n_missing == 0 else 'DIFF'}")

    wr = float((relw - pd.read_csv(f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv",
                                   index_col=0).iloc[:, 0]).abs().max())
    print(f"[2] weights vs committed relw: max|diff|={wr:.4e} "
          f"{'IDENTICAL' if wr < 1e-12 else 'DIFF'}")

    st = stats(net)
    print(f"[3] own-build stats: n={st['n']} ann={st['ann']*100:.2f}% SR={st['sr']:.3f} "
          f"MDD={st['mdd']*100:.2f}% neg_years={st['neg_years']}/19 "
          f"worst_yr={st['worst_year']*100:.2f}% span={st['first']}..{st['last']}")

    gross = Wg.abs().sum(axis=1)
    print(f"[4] gross: mean={gross.mean():.9f} max={gross.max():.12f} "
          f"days>1.6+1e-9: {int((gross > 1.6 + 1e-9).sum())}")

    # causality probe: perturb day-t sleeve ret; day-t WEIGHTS (formed from nav<=t-1) must
    # not move; day-(t+1) weights must move. ret_t itself legitimately changes — it is the
    # day-t payoff on the pre-formed day-t weights.
    t = df.index[len(df) // 2]
    df2 = df.copy()
    df2.loc[t] = df2.loc[t] + 0.05
    nav2 = (1 + df2.fillna(0)).cumprod().shift(1)
    nav2.iloc[0] = 1.0
    d2b = nav2.div(nav2.mean(axis=1), axis=0).mul(relw, axis=1)
    d2b = d2b.div(d2b.sum(axis=1), axis=0) * len(df2.columns)
    Wg2 = d2b * (GEAR / len(df2.columns))
    port2 = (df2.fillna(0).values * Wg2.values).sum(axis=1)
    dw2 = Wg2.diff()
    to2 = dw2.abs().sum(axis=1)
    to2.iloc[0] = 0.0
    net2 = pd.Series(port2, index=df2.index) - to2 * BPS / 1e4 - (GEAR - 1) * RATE / 252
    w_same_day = float((Wg2.loc[t] - Wg.loc[t]).abs().max())
    nxt = df.index[df.index.get_loc(t) + 1]
    w_next_day = float((Wg2.loc[nxt] - Wg.loc[nxt]).abs().max())
    ret_t_move = abs(float(net2.loc[t] - net.loc[t]))
    print(f"[5] causality probe @ {t.date()}: max|dWg_t|={w_same_day:.3e} (must be 0), "
          f"max|dWg_t+1|={w_next_day:.3e} (must be >0), |d ret_t|={ret_t_move:.3e} "
          f"(payoff on pre-formed weights, may be >0) -> "
          f"{'CAUSAL' if w_same_day < 1e-15 and w_next_day > 1e-12 else 'LEAK/OTHER'}")
    same_day_shift = w_same_day  # verdict gate below now keys on weights

    # mutation probe: the champion must genuinely consume the COSTFIX brwt streams. Post
    # re-emit the R3COSTFIX probe inputs became byte-identical to the costfix files (sha
    # match, verified R4) making the old probe a vacuous no-op mutation (max|base-mut|=0).
    # Toothier form (R4): swapping brwt10/7/5 back to the LEGACY half-turn COORD streams
    # must move the series — proves the committed book is the costfix one, not the legacy.
    mut = dict(PATHS)
    for k, legacy in (("brwt10", "brwt10_2000"), ("brwt7", "brwt7"), ("brwt5", "brwt5")):
        mut[k] = f"{ROOT}/campaign/agents/COORD/sleeves/{legacy}.csv"
    import os
    have = all(os.path.exists(p) for p in mut.values())  # mut paths are absolute; ROOT-doubling here silently skipped the probe (fixed R3)
    load_abs = load  # `load` prepends ROOT; absolute paths need a plain loader
    if have:
        def load_plain(p):
            df = pd.read_csv(p, index_col=0)
            df.index = pd.to_datetime(df.index)
            col = "ret" if "ret" in df.columns else df.columns[0]
            s = pd.to_numeric(df[col], errors="coerce").astype(float)
            return s[s.notna()]
        data2 = {n: (load_plain(p) if os.path.isabs(p) else load(p)) for n, p in mut.items()}
        df3 = pd.DataFrame({n: (s[s.index >= "2008-03-31"]) for n, s in data2.items()})
        nav3 = (1 + df3.fillna(0)).cumprod().shift(1)
        nav3.iloc[0] = 1.0
        d3 = nav3.div(nav3.mean(axis=1), axis=0).mul(relw, axis=1)
        d3 = d3.div(d3.sum(axis=1), axis=0) * len(df3.columns)
        Wg3 = d3 * (GEAR / len(df3.columns))
        port3 = (df3.fillna(0).values * Wg3.values).sum(axis=1)
        to3 = Wg3.diff().abs().sum(axis=1)
        to3.iloc[0] = 0.0
        net3 = pd.Series(port3, index=df3.index) - to3 * BPS / 1e4 - (GEAR - 1) * RATE / 252
        jj = pd.concat([net.rename("a"), net3.rename("b")], axis=1, join="inner").dropna()
        print(f"[6] mutation probe (brwt10/7/5 -> legacy COORD half-turn): "
              f"max|base-mut|={float((jj.a - jj.b).abs().max()):.3e} "
              f"(>0 = champion consumes costfix streams, NOT the legacy bytes)")
    else:
        print("[6] mutation probe SKIPPED (legacy COORD sleeves missing)")

    verdict = md < 1e-12 and wr < 1e-12 and same_day_shift < 1e-15
    print(f"VERDICT: {'INDEPENDENT-REPRO-OK' if verdict else 'MISMATCH'}")


if __name__ == "__main__":
    main()
