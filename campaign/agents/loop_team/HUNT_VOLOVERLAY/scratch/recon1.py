"""Recon 1: build trailing state signals, measure predictive content for champion ret_{t+1}."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VOLOVERLAY/scratch')
import lib, numpy as np, pandas as pd

r = lib.champion()
F = lib.fred  # loader

def prep(s):
    s = s.dropna(); s.index = pd.to_datetime(s.index)
    return s.sort_index()

S = {}
# 1. champion own trailing rv (z vs expanding ref, as FF2 style)
rv63 = r.rolling(63).std()*np.sqrt(252)
S['champ_rv63_z'] = lib.exz(rv63, minp=252)
S['champ_rv63'] = rv63
# 2. VIX
vix = prep(lib.fred('VIXCLS'))
S['vix_z252'] = lib.exz(vix.rolling(252).mean(), minp=252)   # trend z
S['vix_zexp'] = lib.exz(vix, minp=504)                        # level z expanding
S['dvix5'] = vix.diff(5)
S['dvix21'] = vix.diff(21)
# 3. credit
hy = prep(lib.fred('hy_oas')); S['hy_oas_z'] = lib.exz(hy, minp=504)
baa = prep(lib.fred('baa')); aaa = prep(lib.fred('aaa'))
spr = (baa-aaa).dropna(); S['baa_aaa_z'] = lib.exz(spr, minp=504)
# 4. curve / rates
t2 = prep(lib.fred('us2y')); t10 = prep(lib.fred('us10y'))
S['slope'] = (t10-t2).dropna()
S['slope_z'] = lib.exz((t10-t2).dropna(), minp=504)
dgs2 = prep(lib.fred('DGS2')); S['dgs2_chg21'] = dgs2.diff(21)
S['dgs10_chg21'] = prep(lib.fred('DGS10')).diff(21)
# 5. breakeven inflation
be = prep(lib.fred('T10YIE')); S['be_z'] = lib.exz(be, minp=504)
# 6. dollar / EM FX
dxy = prep(lib.fred('dxy')); S['dxy_mom63'] = dxy.pct_change(63)
dexbz = prep(lib.fred('DEXBZUS')); S['bz_mom21'] = dexbz.pct_change(21)
dexmx = prep(lib.fred('DEXMXUS')); S['mx_mom21'] = dexmx.pct_change(21)
dtw = prep(lib.fred('DTWEXBGS')); S['dtw_mom63'] = dtw.pct_change(63)
# 7. FF factors
ff = lib.ff_factors(); mkt = ff['Mkt-RF']; mom = lib.ff_mom()['Mom']
S['mkt_rv63_z'] = lib.exz(mkt.rolling(63).std()*np.sqrt(252), minp=252)
S['mom_rv63_z'] = lib.exz(mom.rolling(63).std()*np.sqrt(252), minp=252)
S['mkt_mom126'] = mkt.rolling(126).sum()
# 8. SPX trend
spx = prep(lib.fred('spx')); S['spx_ma_gap'] = spx/spx.rolling(252).mean()-1

# predictive content: corr(r_t, s_{t-1}); quintile conditional means
rows = []
for name, s in S.items():
    x = s.shift(1).reindex(r.index).fillna(np.nan)  # T+1: known at t-1 close
    j = pd.concat([r.rename('r'), x.rename('x')], axis=1).dropna()
    if len(j) < 1500: rows.append((name, len(j), np.nan, np.nan, np.nan, np.nan)); continue
    c = j.r.corr(j.x)
    q = pd.qcut(j.x, 5, labels=False, duplicates='drop')
    qm = j.groupby(q).r.mean()*1e4
    srq = j.groupby(q).r.apply(lambda z: z.mean()/z.std()*np.sqrt(252) if z.std()>0 else np.nan)
    rows.append((name, len(j), round(c,4), round(qm.iloc[0],1), round(qm.iloc[-1],1),
                 round(srq.iloc[-1]-srq.iloc[0],2)))
out = pd.DataFrame(rows, columns=['signal','n','corr','q1_bp','q5_bp','srQ5-srQ1'])
print(out.sort_values('corr', key=abs, ascending=False).to_string(index=False))
