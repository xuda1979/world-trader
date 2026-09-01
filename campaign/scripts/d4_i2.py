import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/D4_microstruct')
import d4_lib as L
import numpy as np, pandas as pd

ho = L.newdata('DHOILNYH'); wti = L.newdata('DCOILWTICO')
rl_ho, rl_wti = L.logret(ho), L.logret(wti)
idx = rl_ho.index.intersection(rl_wti.index)
print("HO-WTI common:", idx[0].date(), idx[-1].date(), len(idx))
rh, rw = rl_ho.reindex(idx).fillna(0), rl_wti.reindex(idx).fillna(0)

def season_pos(idx, months_on, legs='ls'):
    m = idx.month
    on = pd.Series(np.isin(m, months_on), index=idx)
    p_ho = on.astype(float); p_wti = -on.astype(float) if legs=='ls' else pd.Series(0.0, index=idx)
    if legs=='lo': p_ho = on.astype(float); p_wti = on*0
    return p_ho, p_wti

def run(p_ho, p_wti, rh, rw, tag):
    gross = L.t1_pnl(p_ho, rh) + L.t1_pnl(p_wti, rw)
    to = p_ho.shift(1).fillna(0).diff().abs().fillna(0) + p_wti.shift(1).fillna(0).diff().abs().fillna(0)
    net = L.vt10(gross - to*L.COST)
    s = L.full_stats(net); h1,h2 = L.halves_sr(net)
    cb,cc,n = L.corr_blend(net)
    print(f"{tag}: SR {s['sr']:.2f} ann {s['ann']:.1f}% vol {s['vol']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']} worst {s['worst']:.1f}% H1 {h1:.2f} H2 {h2:.2f} corrB {cb:.3f} corrC {cc:.3f}")
    return net, s

# a-priori convention: EIA heating season Oct 1 - Mar 31 (in-season Oct..Mar)
for legs in ['ls','lo']:
    ph, pw = season_pos(idx, [10,11,12,1,2,3], legs)
    run(ph, pw, rh, rw, f"HO season Oct-Mar {legs}")
# alt: Sep 30 - Feb 28
ph, pw = season_pos(idx, [10,11,12,1,2], 'ls')
run(ph, pw, rh, rw, "HO season Oct-Feb ls")
# monthly heat map of HO L/S by month to see structure
print("\nHO long-only by month (raw t):")
rlm = pd.DataFrame({'ho': rh})
for mo in range(1,13):
    p = pd.Series(1.0 if mo==0 else 0.0, index=idx); p[idx.month==mo]=1.0
    g = L.t1_pnl(p, rh); t = g.mean()/g.std()*np.sqrt(len(g)) if g.std()>0 else 0
    print(f"  m{mo:02d}: ann {g.mean()*252*1e4:.0f}bp t {t:.2f}", end='')
print()
# spread-level z reversion baseline for reference (HO-WTI crack)
crack = np.log(ho*42) - np.log(wti)
for lb in [63,126,252]:
    z = (crack - crack.rolling(lb).mean())/crack.rolling(lb).std()
    for sgn in [-1,1]:
        pos = sgn*(-z).shift(1).clip(-1,1).reindex(idx).fillna(0)
        net = L.vt10(L.net_turnover(pos, rh))
        s = L.full_stats(net)
        print(f"crack z-rev lb{lb} sgn{sgn}: SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}%")
