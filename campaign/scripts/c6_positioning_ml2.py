"""C6 Idea 3 (cont): Positioning-ML per-market GBM -> 5d sign book."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr, scramble_pval
from sklearn.ensemble import GradientBoostingRegressor
import warnings; warnings.filterwarnings('ignore')

px = pd.read_pickle('/tmp/c6_px.pkl')
COT='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_cot'
cot = pd.read_csv(f'{COT}/cot_tidy.csv', parse_dates=['date'])
tff = pd.read_csv(f'{COT}/tff_tidy.csv', parse_dates=['date'])
cot['mkt']=cot.market.str.replace(r'\s+',' ',regex=True).str.strip()
tff['mkt']=tff.market.str.replace(r'\s+',' ',regex=True).str.strip()

MAP = {
 'wti':'CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE',
 'brent':'BRENT LAST DAY - NEW YORK MERCANTILE EXCHANGE',
 'natgas':'NATURAL GAS - NEW YORK MERCANTILE EXCHANGE',
 'gold':'GOLD - COMMODITY EXCHANGE INC.',
 'silver':'SILVER - COMMODITY EXCHANGE INC.',
 'copper':'COPPER-GRADE #1 - COMMODITY EXCHANGE INC.',
 'spx':'E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE',
 'us10y':'10-YEAR U.S. TREASURY NOTES - CHICAGO BOARD OF TRADE',
 'eur':'EURO FX - CHICAGO MERCANTILE EXCHANGE',
 'jpy':'JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE',
 'gbp':'BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE',
 'chf':'SWISS FRANC - CHICAGO MERCANTILE EXCHANGE',
 'aud':'AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE',
 'cad':'CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE',
}
def build_features(mkt, src, df, p):
    d = df[df.mkt==mkt].set_index('date').sort_index()
    if src=='cot': pos = d['m_money_long']-d['m_money_short']
    else:          pos = d['lf_net']
    if pos.isna().mean()>0.3 or len(pos)<150: return None
    pos_d = pos.reindex(p.index.union(pos.index)).ffill(limit=5)   # weekly -> daily-ish
    pz = (pos_d - pos_d.rolling(52).mean())/pos_d.rolling(52).std()
    pct = pos_d/(pos_d.rolling(52).max())                            # not ideal; use pct-of-oi
    pnl = p.pct_change()
    r21 = p.pct_change(21); r63 = p.pct_change(63)
    v21 = pnl.rolling(21).std()
    F = pd.DataFrame({'posz':pz, 'r21':r21, 'r63':r63, 'v21':v21})
    F['target'] = pnl.shift(-5)     # 5d fwd return
    return F.dropna()

def run_market(key, mkt, src, df):
    p = px[key]; F = build_features(mkt, src, df, p)
    if F is None: return None, 'no-data'
    F = F.loc['2008-01-01':]
    if len(F)<300: return None, 'short'
    dates = F.index
    mends = pd.date_range('2009-07-01', dates.max(), freq='ME')
    sig = pd.Series(np.nan, index=dates)
    for me in mends:
        te = (dates>me)&(dates<=me+pd.offsets.MonthEnd(1))
        tr = dates<=me-pd.Timedelta(days=7)
        if tr.sum()<260 or te.sum()==0: continue
        m = GradientBoostingRegressor(n_estimators=60, max_depth=2, learning_rate=0.05,
                                      subsample=0.8, random_state=0)
        m.fit(F.loc[tr, ['posz','r21','r63','v21']], F.loc[tr,'target'])
        pr = m.predict(F.loc[te, ['posz','r21','r63','v21']])
        sig.loc[dates[te]] = np.sign(pr)
    if sig.notna().sum()<300: return None, 'few-sig'
    return sig, 'ok'

books = {}
for key, mkt in MAP.items():
    src_df = cot if key not in ('spx','us10y','eur','jpy','gbp','chf','aud','cad') else tff
    if mkt not in src_df.mkt.unique():
        print(f'{key}: market missing'); continue
    sig, status = run_market(key, mkt, 'tff' if src_df is tff else 'cot', src_df)
    if sig is None: print(f'{key}: {status}'); continue
    p = px[key]; pnl = p.pct_change()
    pos = sig.shift(1).fillna(0)                       # T+1
    turn = pos.diff().abs().fillna(0)
    net = pos*pnl - 6e-4*turn
    net = net[net.index>='2008-06-01']
    ns,_ = vol_target(net, 0.10)
    st = full_stats(ns)
    print(f"{key:7s} SR {st['sr']:5.2f} ann {st['ann']:6.1f} negy {st['negy']} n {len(ns)}")
    books[key]=ns
if books:
    R = pd.DataFrame(books).dropna(how='all')
    R['mean'] = R.mean(axis=1)
    ms,_ = vol_target(R['mean'],0.10)
    st=full_stats(ms); h1,h2=halves_sr(ms); pv,rsr=scramble_pval(ms)
    print('BOOK mean-of-5 FULL',{k:(round(v,2) if isinstance(v,float) else v) for k,v in st.items() if k!='yearly'})
    print('halves',round(h1,2),round(h2,2),'scramble p',pv)
    oos=ms[ms.index>='2017-01-01']; print('OOS',{k:(round(v,2) if isinstance(v,float) else v) for k,v in full_stats(oos).items() if k!='yearly'})
    b=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv',index_col=0,parse_dates=True)['ret']
    j=pd.concat([ms,b],axis=1,join='inner').dropna(); print('corr blend',round(j.corr().iloc[0,1],3),'n',len(j))
    ms.to_frame('ret').to_csv('/tmp/c6_cot_ml.csv')
    print('yearly',st['yearly'])
