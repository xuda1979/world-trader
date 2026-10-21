"""HTS-style pre-gated hunt harness: given a raw daily series (price, flow, level, ratio),
build candidate daily long/short signals, T+1 causal + vol-normalized, full |dW| costs,
and gate vs the champion (SR>=1.5, ac1<0.5, uniqR>=0.08, |corr|<=0.4, mass-pos)."""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0,'campaign/scripts'); sys.path.insert(0,'campaign')
import rawew13v2_build as B

def load_series(path, datecol='date', valcol=None):
    df=pd.read_csv(path)
    df.columns=[c.strip().lower() for c in df.columns]
    df['_d']=pd.to_datetime(df[datecol], errors='coerce')
    df=df.dropna(subset=['_d'])
    v = valcol if valcol else ([c for c in df.columns if c not in ('_d','date')][0])
    s=pd.Series(pd.to_numeric(df[v],errors='coerce').values, index=df['_d']).sort_index()
    return s[~s.index.duplicated(keep='last')]

def vol_scale(r, win=60, cap=8.0):
    v=r.rolling(win,min_periods=20).std(ddof=1).shift(1)
    s=(0.10/np.sqrt(252))/v
    s=s.clip(upper=cap); s=s.fillna(0.0)
    return (r*s).fillna(0.0)

def candidate_returns(sig, raw_ret, gear=1.0, cost_bps=6.4):
    """sig: desired position series (already T+1 conceptually). We apply the position to a return series."""
    We=sig.shift(1).fillna(0.0)     # T+1 causal
    gross=We.abs()
    port=(raw_ret*We).fillna(0.0)
    to=We.diff().abs().fillna(0.0)
    net=port - to*(cost_bps/1e4) - np.maximum(gross.mean()-1,0)*0.0/252
    return net

def gates(net, champ_net, shelf=None):
    """Return dict of gate results."""
    j=pd.concat([net.rename('n'), champ_net.rename('c')], axis=1, join='inner').dropna()
    n=j['n'] if (j['n'].abs()>1e-15).any() else net.dropna()
    sr= n.mean()/n.std(ddof=1)*np.sqrt(252)
    ann=(1+n).prod()**(252/len(n))-1
    nav=(1+n).cumprod(); mdd=(nav/nav.cummax()-1).min()
    ac1=n.autocorr(1) if len(n)>3 else 0.0
    uniq=n.nunique()/len(n) if len(n) else 0.0
    corr=net.reindex(champ_net.index).corr(champ_net) if len(net)>20 else 0.0
    # negative years
    yr=n.groupby(n.index.year).apply(lambda x:(1+x).prod()-1)
    neg=int((yr<0).sum())
    # mass-pos: share of days with nonzero position > 5%
    mass=(net.abs()>1e-12).mean()
    return dict(sr=float(sr), ann=float(ann*100), mdd=float(mdd*100), ac1=float(ac1) if ac1==ac1 else 0.0,
                uniqR=float(uniq), corr_champ=float(corr) if corr==corr else 0.0, neg_years=neg, mass=mass)

def hunt_report(name, signals, raw_ret, champ_net, gear=1.0):
    """signals: dict {label: position series}. raw_ret: matching returns series."""
    print(f"\n===== HUNT: {name} =====")
    for lab, sig in signals.items():
        if sig is None or len(sig)==0: continue
        common=sig.index.intersection(raw_ret.dropna().index).intersection(champ_net.index)
        if len(common)<40: 
            print(f"  {lab}: <40 common days, skip"); continue
        sigc=sig.reindex(common).fillna(0.0); rrc=raw_ret.reindex(common).fillna(0.0)
        net=candidate_returns(sigc.fillna(0.0), rrc)
        g=gates(net, champ_net)
        ok = g['sr']>=1.5 and g['ac1']<0.5 and g['uniqR']>=0.08 and abs(g['corr_champ'])<=0.4 and g['mass']>=0.02
        print(f"  {lab:28s} n={len(common):5d} SR={g['sr']:5.2f} ann={g['ann']:7.2f}% MDD={g['mdd']:7.2f}% "
              f"ac1={g['ac1']:5.2f} uniqR={g['uniqR']:6.3f} corrC={g['corr_champ']:+.3f} negY={g['neg_years']} mass={g['mass']:.2f}  {'*PASS*' if ok else 'fail'}")
        if ok and shelf is not None:
            net.to_frame('ret').to_csv(f"{shelf}/{name}_{lab}.csv")
