"""HUNT_TIMESFM ROUND 4 sleeve evaluation.
 (a) forecast-direction L/S per asset (and equal-weight 6-asset book):
     pos_t = sign(f - last) decided at close T, held at T+1 (the target day).
 (b) forecast-magnitude champion overlay: |m| percentile -> 0.7x mask on champion,
     WITH mandatory content-free controls:
       (b1) champion's own trailing 252d realized-vol percentile mask (zero TF content)
       (b2) CONSTANT scale = candidate's mean exposure (scale-invariance isolate).
Gates: GATES_CONTRACT.md — SR>=1.0, halves>=0.5, <=2 negyr none<-5%, scramble p<0.05,
|corr|<0.15 vs champion. Costs 6.4bps full |dW| + borrow 0.5%/yr + margin 4.5%/yr.
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r4")
import tfm_engine_r4 as eng
from bt import metrics

ROOT = "/Users/daxu/software/world-trader"
ETFDIR = f"{ROOT}/tools/quant/data/more_etf"
OUT = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r4"
ASSETS = ["QQQ", "XLE", "XLF", "TLT", "GLD", "EEM"]
COST, BORROW, MARGIN, ANN = eng.COST, eng.BORROW, eng.MARGIN, eng.ANN


def close(t):
    df = pd.read_csv(f"{ETFDIR}/{t}.csv", index_col=0, parse_dates=True)
    s = pd.to_numeric(df["close"], errors="coerce"); s = s[s > 0]
    return s[~s.index.duplicated(keep="last")].sort_index()


def champion():
    return pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                       index_col=0, parse_dates=True).iloc[:, 0].astype(float)


def net_of_positions(pos: pd.Series, r: pd.Series, vt: str = "on") -> pd.Series:
    """pos decided at close t, held t+1. Full cost stack on held weight."""
    p = pos.shift(1).fillna(0.0)
    r = r.reindex(p.index)
    if vt == "on":
        p = p * eng.vt_scale(r.fillna(0.0))
    act = p.abs() > 0
    if (act & r.isna()).any():
        raise ValueError("silent zero-fill in sleeve book")
    r = r.fillna(0.0)
    to = p.diff().abs(); to.iloc[0] = abs(p.iloc[0])
    return (p * r - to * COST
            - (-p.clip(upper=0.0)) * BORROW / ANN
            - (p.abs() - 1.0).clip(lower=0.0) * MARGIN / ANN)


def overlay_net(scale: pd.Series, champ: pd.Series, gross_champ: float = 1.6) -> pd.Series:
    """Scale champion (capital-real gross=1.6) by scale_t (decided at close t, held t+1).
    Extra turnover from the mask charged at 6.4bps on |d(scale*1.6)|."""
    s = scale.shift(1).fillna(0.0)
    w = (s * gross_champ).rename("w").to_frame()
    r = champ.reindex(w.index).fillna(0.0)
    to = w["w"].diff().abs(); to.iloc[0] = abs(w["w"].iloc[0])
    to_base = pd.Series(gross_champ, index=w.index).diff().abs().fillna(0.0)
    extra_to = (to - to_base).clip(lower=0.0)
    return (w["w"] * r - extra_to * COST - (w["w"].abs() - 1.0).clip(lower=0.0) * MARGIN / ANN)


def gate_report(net: pd.Series, champ: pd.Series) -> dict:
    net = net.dropna()
    sr = metrics.sharpe_d(net)
    h1, h2 = metrics.half_split(net)
    neg, worst = metrics.neg_years(net)
    j = pd.concat([net.rename("a"), champ.rename("c")], axis=1, join="inner").dropna()
    corr = float(j.corr().iloc[0, 1])
    return dict(n=len(net), sr=round(sr, 3), h1=round(h1, 3), h2=round(h2, 3),
                neg=int(neg), worst=round(worst, 4), corr=round(corr, 3),
                ann=round(metrics.ann_geo(net), 4))


def scramble(net: pd.Series, pos: pd.Series, ret: pd.Series, n=200) -> float:
    """Position-scramble on the raw per-unit book (positions vs returns, T+1 applied)."""
    p = pos.shift(1).fillna(0.0).reindex(net.index).fillna(0.0).values
    r = ret.reindex(net.index).fillna(0.0).values
    p_v, f = btgates.scramble_positions(p, r) if False else (None, None)
    from bt import gates as G
    pv, real = G.scramble_positions(p, r, n=n)
    return pv


def run_a():
    champ = champion()
    print("=== (a) forecast-direction L/S per asset + equal-weight book ===")
    books = {}
    for a in ASSETS:
        f = pd.read_csv(f"{OUT}/fcst_{a}.csv", parse_dates=["date"]).set_index("date")
        m = f["f"] - f["last"]                       # predicted log move for target day
        px = close(a)
        r = px.pct_change().reindex(m.index)
        pos = pd.Series(np.sign(m.values), index=m.index)
        net = net_of_positions(pos, r, vt="on")
        g = gate_report(net, champ)
        sp = scramble(net, pos, r)
        books[a] = net
        print(f"  {a}: SR={g['sr']} h1={g['h1']} h2={g['h2']} neg={g['neg']} "
              f"worst={g['worst']} corr={g['corr']} ann={g['ann']} scr_p={sp} n={g['n']}")
    book = pd.concat(books, axis=1).dropna().mean(axis=1)
    g = gate_report(book, champ)
    print(f"  EW6: SR={g['sr']} h1={g['h1']} h2={g['h2']} neg={g['neg']} "
          f"worst={g['worst']} corr={g['corr']} ann={g['ann']} n={g['n']}")

    print("  -- DEAD-family control: naive 1d momentum (sign of last 1d ret) --")
    agree_tab = {}
    for a in ASSETS:
        f = pd.read_csv(f"{OUT}/fcst_{a}.csv", parse_dates=["date"]).set_index("date")
        m = f["f"] - f["last"]
        px = close(a)
        r = px.pct_change().reindex(f.index)
        lastret = px.diff().reindex(f.index)  # day-T realized move (decision-day info)
        pos_n = pd.Series(np.sign(lastret.fillna(0.0).values), index=f.index)
        net_n = net_of_positions(pos_n, r, vt="on")
        gn = gate_report(net_n, champ)
        tfmd = np.sign(m.values)
        naived = pos_n.values
        both = ~((tfmd == 0) | (naived == 0))
        agree = float((tfmd[both] == naived[both]).mean())
        agree_tab[a] = agree
        print(f"  {a} naive: SR={gn['sr']} corr={gn['corr']} ann={gn['ann']} | dir-agree={agree:.3f}")
    return books, agree_tab
