import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/D4_microstruct')
import d4_lib as L
import numpy as np, pandas as pd

jet = L.newdata('DJFUELUSGULF'); ho = L.newdata('DHOILNYH'); wti = L.newdata('DCOILWTICO')
rl_j, rl_h, rl_w = L.logret(jet), L.logret(ho), L.logret(wti)

# ---- Idea 3: jet fuel. 2020+ only (disclose short window); jet vs HO spread momentum/reversion
idx3 = rl_j.index.intersection(rl_h.index)
idx3 = idx3[idx3 >= '2020-01-01']
print("Idea3 jet window:", idx3[0].date(), idx3[-1].date(), len(idx3))
rj, rh = rl_j.reindex(idx3).fillna(0), rl_h.reindex(idx3).fillna(0)
for lb in [21, 63, 126]:
    mom = (np.log(jet).diff(lb) - np.log(ho).diff(lb)).reindex(idx3)
    for sgn in [1, -1]:
        pos = (sgn*np.sign(mom)).shift(1).reindex(idx3).fillna(0)
        gross = L.t1_pnl(pos, rj) + L.t1_pnl(-pos, rh)
        to = pos.shift(1).fillna(0).diff().abs().fillna(0)*2
        net = L.vt10(gross - to*L.COST)
        s = L.full_stats(net); h1,h2 = L.halves_sr(net)
        print(f"  jet-HO mom lb{lb} sgn{sgn}: SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']} H1 {h1:.2f} H2 {h2:.2f}")

# ---- Idea 4: copper-gold ratio (copx/xau)
copx, xau = L.price('copx'), L.price('xau')
idx = copx.index.intersection(xau.index)
print("\nIdea4 Cu/Au window:", idx[0].date(), idx[-1].date(), len(idx))
ratio = (copx/xau).reindex(idx).dropna()
r_sp = L.logret(ratio)
rl_spx = L.logret(L.price('spx')).reindex(idx).fillna(0)
rl_co = L.logret(copx).reindex(ratio.index).fillna(0)
rl_au = L.logret(xau).reindex(ratio.index).fillna(0)

# 4a: ratio 63d momentum -> SPX gate
for lb in [63, 126, 252]:
    mom = np.log(ratio).diff(lb)
    z = mom/mom.rolling(252).std()
    pos = z.shift(1).clip(-3,3).fillna(0)   # scaled momentum on SPX
    net = L.vt10(L.net_turnover(pos, rl_spx))
    s = L.full_stats(net); h1,h2 = L.halves_sr(net)
    cb,cc,n = L.corr_blend(net)
    print(f"  4a CuAu mom{lb}->SPX: SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']} H1 {h1:.2f} H2 {h2:.2f} corrB {cb:.3f}")
# binary version
pos = np.sign(np.log(ratio).diff(63)).shift(1).fillna(0)
net = L.vt10(L.net_turnover(pos, rl_spx)); s = L.full_stats(net); h1,h2=L.halves_sr(net)
print(f"  4a binary mom63->SPX: SR {s['sr']:.2f} H1 {h1:.2f} H2 {h2:.2f}")

# 4b: ratio 21d reversion (long COPX / short XAU or reverse)
for lb in [21, 63]:
    z = (np.log(ratio) - np.log(ratio).rolling(lb).mean())/np.log(ratio).rolling(lb).std()
    for sgn in [1, -1]:
        pos = (sgn*(-z)).shift(1).clip(-1,1).fillna(0)
        gross = L.t1_pnl(pos, rl_co) + L.t1_pnl(-pos, rl_au)
        to = pos.shift(1).fillna(0).diff().abs().fillna(0)*2
        net = L.vt10(gross - to*L.COST)
        s = L.full_stats(net); h1,h2 = L.halves_sr(net)
        cb,cc,n = L.corr_blend(net)
        print(f"  4b CuAu z-rev lb{lb} sgn{sgn}: SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']} worst {s['worst']:.1f}% H1 {h1:.2f} H2 {h2:.2f} corrB {cb:.3f} corrC {cc:.3f}")

# 4c: raw t-stats of ratio daily changes by nothing special; check ratio momentum on gold side quick
mom63 = np.log(ratio).diff(63)
raw = rl_spx[mom63.shift(1)>0].mean()/rl_spx[mom63.shift(1)>0].std()*np.sqrt(252)
raw2 = rl_spx[mom63.shift(1)<0].mean()/rl_spx[mom63.shift(1)<0].std()*np.sqrt(252)
print(f"  SPX ann SR: high-ratio-mom {raw:.2f} vs low {raw2:.2f}")
