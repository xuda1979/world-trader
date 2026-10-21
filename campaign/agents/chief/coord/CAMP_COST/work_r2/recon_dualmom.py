"""CAMP_COST R2 — dualmom (QA_dualmom_band121) byte-reconstruction + costfix.

Step 1: rebuild committed sleeve with ORIGINAL convention (0.5*|dW| @ 6.0bps) -> byte-compare.
Step 2: flip ONLY the cost line (FULL |dW| @ 6.4bps), report before/after stats.
Construction mirrors QA_dualmom_band121.py lines 23-71 exactly (no scramble).
"""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from campaign.harness import data as D
from engine import month_ends, strategy_ret

WIN, BAND, FRAC, TARGET = 200, 0.03, 1/3, 0.10
COST_OLD, BPS_NEW = 6.0, 6.4
ROOT = "/Users/daxu/software/world-trader"

C = pd.read_csv(f"{ROOT}/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
                index_col=0, parse_dates=True)["ret"].astype(float)


def build(full_dw=False, bps=None):
    px = D.closes()
    rets = px.pct_change()
    MES = [d for d in month_ends(rets) if d in px.index]
    sig = px.shift(21) / px.shift(252) - 1.0
    ff = D.ff_factors()
    mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
    ma = mkt.rolling(WIN, min_periods=WIN).mean()
    g = pd.Series(np.where(mkt > ma * (1 + BAND), 1.0,
                  np.where(mkt < ma * (1 - BAND), 0.0, np.nan)), index=mkt.index)
    g = g.reindex(px.index).ffill().fillna(0.0)
    W = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
    for t in MES:
        if t not in sig.index or g.loc[t] <= 0:
            continue
        row = sig.loc[t].dropna()
        if len(row) < 10:
            continue
        row = row.sort_values()
        nl = max(int(np.floor(len(row) * FRAC)), 1)
        for s in row.index[-nl:]:
            W.loc[t, s] = 1.0 / nl
    idx = rets.index
    mes = list(MES)
    w = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    prev = pd.Series(0.0, index=rets.columns)
    turn = pd.Series(0.0, index=idx)
    pos_of = {d: idx.get_loc(d) for d in mes}
    bps = (BPS_NEW if bps is None else bps)
    factor = (1.0 if full_dw else 0.5)
    for i, t in enumerate(mes):
        neww = W.loc[t]
        p = pos_of[t]
        if p + 1 < len(idx):
            turn.iloc[p + 1] = factor * (neww - prev).abs().sum()
            nxt_p = pos_of[mes[i + 1]] + 1 if i + 1 < len(mes) else len(idx)
            w.iloc[p + 1: nxt_p] = neww.values
            prev = neww
    net = (w * rets.fillna(0.0)).sum(axis=1) - turn * bps / 1e4
    nz = w.abs().sum(axis=1)
    start = nz[nz > 0].index[0]
    r = strategy_ret(net, start)
    return r


def stats(r):
    r = r.dropna()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    sr = r.mean() / r.std() * np.sqrt(252)
    eq = (1 + r).cumprod()
    return dict(n=len(r), ann=(eq.iloc[-1]) ** (252 / len(r)) - 1, sr=sr,
                mdd=(eq / eq.cummax() - 1).min(), negy=int((yr < 0).sum()),
                first=str(r.index[0].date()), last=str(r.index[-1].date()))


if __name__ == "__main__":
    r_old = build(full_dw=False, bps=COST_OLD)
    j = pd.concat([r_old.rename("a"), C.rename("b")], axis=1, join="inner").dropna()
    d = float((j.a - j.b).abs().max())
    print(f"STEP1 recon-vs-committed: n_inner={len(j)}/{len(C)} maxdev={d:.3e} "
          f"{'BYTE-EXACT' if d < 1e-12 else 'MISMATCH'}")
    if d < 1e-12:
        r_new = build(full_dw=True, bps=BPS_NEW)
        so, sn = stats(r_old), stats(r_new)
        print(f"STEP2 before: ann={so['ann']*100:.3f}% SR={so['sr']:.4f} mdd={so['mdd']*100:.2f}% "
              f"negy={so['negy']} n={so['n']}")
        print(f"      after : ann={sn['ann']*100:.3f}% SR={sn['sr']:.4f} mdd={sn['mdd']*100:.2f}% "
              f"negy={sn['negy']} n={sn['n']}")
        jj = pd.concat([r_old.rename("o"), r_new.rename("n")], axis=1, join="inner").dropna()
        viol = jj[jj.n > jj.o + 1e-15]
        print(f"      cost-grows-only: {'PASS' if len(viol)==0 else f'FAIL {len(viol)} days'} "
              f"(n_days_inner={len(jj)})")
        pd.DataFrame({"ret": r_new.values}, index=r_new.index).to_csv(
            f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/work_r2/dualmom_costfix_candidate.csv")
        print("      candidate written")
