#!/usr/bin/env python3
"""AUDIT_V2 check 2: new sleeves from RAW data.
diescrack: rebuild from FRED DJFUELUSGULF + wti_full with my own code (meta discloses recipe).
CFX4: rebuild from twelvedata closes with my own code."""
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
DIE = f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv"
CFX = f"{ROOT}/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv"
FRED = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
FXD = f"{ROOT}/tools/quant/data/fx"
COST = 6.0/1e4

def fred(name):
    import os
    p1 = f"{FRED}/{name}.csv"
    if not os.path.exists(p1):
        p1 = f"{ROOT}/tools/quant/data/newdata/{name}.csv"
    df = pd.read_csv(p1, index_col=0, parse_dates=True)
    s = df['value'] if 'value' in df.columns else df.iloc[:,0]
    return pd.to_numeric(s, errors='coerce')[~s.index.duplicated(keep='last')].sort_index()

def rebuild_diescrack(lb=40, gate=2.0, vt_ann=0.08, min_days=60, cap=3.0):
    dj = fred('DJFUELUSGULF')*42.0
    wti = fred('wti_full')
    sp = (np.log(dj) - np.log(wti)).dropna()
    sp = sp[sp.index >= '2008-01-01']
    m = sp.rolling(lb, min_periods=lb).mean()
    sd = sp.rolling(lb, min_periods=lb).std().replace(0, np.nan)
    z = (sp-m)/sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -gate] = 1.0
    pos[z > gate] = -1.0
    ret = sp.diff().shift(-1)
    gr = pos*ret
    tup = (pos.diff().abs()/2.0).reindex(gr.index).fillna(0.0)
    net = gr - tup*COST
    # borrow 0.5%/yr on 1-unit short leg charged on all nonzero rows (incl cost-only) => net already;
    # meta says borrow charged on ALL nonzero rows. Implement: rows where gr!=0 or tup>0 (active)
    borrow = pd.Series(0.0, index=net.index)
    active = (pos != 0.0).reindex(net.index).fillna(False)
    # cost-only rows are those with tup>0; meta: "222 cost-only entry/exit rows also charged"
    borrow[active | (tup > 0)] = 0.005/252
    net = net - borrow
    # expanding vol target 0.08 min60 cap3
    rv = net.expanding(min_days).std()*np.sqrt(252)
    scale = (vt_ann/rv).clip(upper=cap)
    out = (net*scale).dropna()
    return out, pos, net

def rebuild_cfx4():
    pairs = ["GBP_USD","NZD_USD","AUD_USD","EUR_USD"]
    def loadf(p):
        df = pd.read_csv(f"{FXD}/{p}.csv", index_col=0, parse_dates=True)
        df = df[df.index.dayofweek < 5]
        df = df[~df.index.duplicated(keep='last')].sort_index()
        return df
    cl = {p: loadf(p).close for p in pairs}
    C = pd.DataFrame(cl).dropna()
    R = C.pct_change()
    books = [("GBP_USD","NZD_USD"), ("AUD_USD","GBP_USD"), ("AUD_USD","EUR_USD"), ("EUR_USD","NZD_USD")]
    nets = []
    for a, b in books:
        spl = np.log(C[a]) - np.log(C[b])
        zs = []
        for lb in (21, 63):
            z = (spl - spl.rolling(lb).mean())/spl.rolling(lb).std()
            zs.append(z)
        z = sum(zs)/len(zs)
        w = (2.0*(-z)).clip(-2.0, 2.0)/2.0
        sig = w.shift(1)
        net = sig*(R[a]-R[b]) - 2*sig.diff().abs()*COST - 0.005/252*sig.abs()
        nets.append(net.dropna(how='all'))
    return pd.concat(nets, axis=1).mean(axis=1).dropna()

if __name__ == "__main__":
    out, pos, net = rebuild_diescrack()
    ref = pd.read_csv(DIE, index_col=0, parse_dates=True).iloc[:,0]
    j = pd.concat([ref.rename('ref'), out.rename('mine')], axis=1, join='inner').dropna()
    print(f"diescrack: ref n={len(ref)} span {ref.index[0].date()}..{ref.index[-1].date()}; mine n={len(out)} span {out.index[0].date()}..{out.index[-1].date()}")
    print(f"  overlap {len(j)}; max|diff| {float((j.ref-j.mine).abs().max()):.3e}")
    only_ref = ref.index.difference(out.index); only_mine = out.index.difference(ref.index)
    print(f"  only-ref {len(only_ref)}, only-mine {len(only_mine)}")
    out2 = rebuild_cfx4()
    refc = pd.read_csv(CFX, index_col=0, parse_dates=True).iloc[:,0]
    jc = pd.concat([refc.rename('ref'), out2.rename('mine')], axis=1, join='inner').dropna()
    print(f"CFX4: ref n={len(refc)} span {refc.index[0].date()}..{refc.index[-1].date()}; mine n={len(out2)} span {out2.index[0].date()}..{out2.index[-1].date()}")
    print(f"  overlap {len(jc)}; max|diff| {float((jc.ref-jc.mine).abs().max()):.3e}")
    print(f"  only-ref {len(refc.index.difference(out2.index))}, only-mine {len(out2.index.difference(refc.index))}")
