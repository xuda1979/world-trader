#!/usr/bin/env python3
"""AUDIT_LEVFRONTIER — capital-real <=1.6x frontier engine with honest financing.
Gates: G1 byte-repro (committed recipes), G2 cap<=1.6 all days, G3 margin reduces ann,
G4 cost identity, G5 POOL11-FIX byte-repro. GREEN implementation.
"""
import sys
sys.path.insert(0, 'campaign/scripts')
import numpy as np, pandas as pd
from honest13_build import make as make13, NEW3, NEW2, POOL, ROOT
import honest11_build as h11

CAP = 1.6
SF = {'dualmom':0.5,'QAxasts':0.4,'carryv2':0.3,'C5ng':0.5,'C5ngsum':0.5,
      'brwt15':0.5,'brwt10':0.5,'brwt7':0.5,'brwt5':0.5,'A5r2':0,'a6r7':0}

def vt_local(r, tgt, min_win=60, cap=8.0):
    vol = r.rolling(min_win).std().shift(1) * np.sqrt(252)
    s = (tgt / vol).clip(upper=cap)
    s[vol.isna()] = 0
    return r * s.fillna(0), s

def components13(NEW, TGT, THR):
    """Exact reconstruction of honest13_build.build() internals."""
    Sd, capW, blend, tw, wts = make13(NEW)
    b, gb = vt_local(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod()
    rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1) / rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index)
    full = capW.mul(gb, axis=0).mul(sc, axis=0)
    reb = full.diff().abs().sum(axis=1)
    terms = [capW[n]*sc*SF[n]*(0.005 + (0.006 if n == 'dualmom' else 0.0)) for n in POOL if SF[n] > 0]
    htb = pd.concat(terms, axis=1).sum(axis=1)
    gross = full.abs().sum(axis=1)
    return dict(b=b, gb=gb, sc=sc, full=full, tw=tw, reb=reb, htb=htb, gross=gross)

def components11(TGT, THR):
    """Exact reconstruction of honest11_build.build(PERSLEEVE=0.08, REBAL=True, KEEP=True)."""
    SnP = pd.DataFrame({n: h11.vt(h11.sn(p), 0.08)[1] for n, p in h11.POOL.items()}).dropna(how='all')
    N = len(h11.POOL); capW = SnP / N
    V = {}
    for n in h11.POOL:
        r = h11.sn(h11.POOL[n])
        v, s = h11.vt(r, 0.08)
        V[n] = v - capW[n].diff().abs().fillna(0) * ((h11.EXEC[n]-6.0)/1e4)
    blend = pd.DataFrame(V).mean(axis=1); blend = blend[blend.index >= '2006-10-01']
    W = SnP.div(SnP.sum(axis=1), axis=0).fillna(0)
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, gb = h11.vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc
    dsc = sc.diff().abs()*0.5
    Sd = pd.DataFrame({n: h11.vt(h11.sn(p), 0.08)[1] for n, p in h11.POOL.items()}).dropna(how='all')
    reb = Sd.diff().abs().sum(axis=1)/N + gb.diff().abs().fillna(0)
    terms = [capW[n]*sc*SF[n]*(0.005 + (0.006 if n == 'dualmom' else 0.0)) for n in h11.POOL if SF[n] > 0]
    htb = pd.concat(terms, axis=1).sum(axis=1)   # KEEP semantics: skipna row-sum
    gross = (gb.abs()*sc*Sd.sum(axis=1).fillna(0)/N)
    return dict(b=b, gb=gb, sc=sc, tw=tw, dsc=dsc, reb=reb, htb=htb, gross=gross, capW=capW, Sd=Sd)

def committed_replica13(NEW, TGT, THR):
    c = components13(NEW, TGT, THR); idx = c['b'].index
    dsc = (c['sc'].diff().abs()*0.5).reindex(idx).fillna(0)
    return (c['b']*c['sc'] - (c['tw'].reindex(idx).fillna(0)+dsc)*6e-4
            - c['reb'].reindex(idx).fillna(0)*6e-4
            - c['htb'].reindex(idx).fillna(0)/252).dropna(how='all')

def committed_replica11(TGT, THR):
    c = components11(TGT, THR)
    r = c['b'] - (c['tw'].reindex(c['b'].index).fillna(0) + c['dsc'].reindex(c['b'].index).fillna(0))*6e-4
    r = r - c['reb'].reindex(r.index).fillna(0)*6e-4
    return (r - c['htb'].reindex(r.index).fillna(0)/252).dropna(how='all')

def cap_factor(gross):
    return (CAP / gross).clip(upper=1.0)

def capped_book(NEW, TGT, THR, rate=0.045, cost_bps=6.4, cap=CAP):
    """Cap positions kappa=min(1,cap/gross); return scaled by kappa; margin charged on
    (capped gross - 1)+; 6.4bps/side on tw (kappa-scaled), dsc (kappa-scaled), and the
    EXACT capped position-path turnover reb_c."""
    c = components13(NEW, TGT, THR)
    idx = c['b'].index
    kappa = cap_factor(c['gross']).reindex(idx).fillna(1.0).clip(upper=1.0)
    tw_c  = c['tw'].reindex(idx).fillna(0) * kappa
    dsc_c = (c['sc'].diff().abs()*0.5).reindex(idx).fillna(0) * kappa
    full_c = c['full'].mul(kappa, axis=0)
    reb_c = full_c.diff().abs().sum(axis=1).reindex(idx).fillna(0)
    htb_c = c['htb'].reindex(idx).fillna(0) * kappa / 252
    gross_c = c['gross'].reindex(idx).fillna(0) * kappa
    margin = np.clip(gross_c - 1.0, 0, None) * rate / 252
    r = (c['b']*c['sc']*kappa - (tw_c + dsc_c + reb_c)*cost_bps/1e4 - htb_c - margin)
    return r.dropna(how='all'), gross_c.reindex(r.index), (tw_c+dsc_c+reb_c).reindex(r.index)

def capped_book11(TGT, THR, rate=0.045, cost_bps=6.4, cap=CAP):
    c = components11(TGT, THR)
    idx = c['b'].index
    kappa = cap_factor(c['gross']).reindex(idx).fillna(1.0).clip(upper=1.0)
    tw_c  = c['tw'].reindex(idx).fillna(0) * kappa
    dsc_c = c['dsc'].reindex(idx).fillna(0) * kappa
    reb_c = (c['reb'].reindex(idx).fillna(0) * kappa)
    htb_c = c['htb'].reindex(idx).fillna(0) * kappa / 252
    gross_c = c['gross'].reindex(idx).fillna(0) * kappa
    margin = np.clip(gross_c - 1.0, 0, None) * rate / 252
    r = (c['b']*kappa - (tw_c + dsc_c + reb_c)*cost_bps/1e4 - htb_c - margin)
    return r.dropna(how='all'), gross_c.reindex(r.index), (tw_c+dsc_c+reb_c).reindex(r.index)

def stats(r, start='2008-03-31'):
    rr = r[r.index >= start]
    m = (1 + rr).resample('ME').prod() - 1
    yr = rr.groupby(rr.index.year).apply(lambda x: (1 + x).prod() - 1)
    eq = (1 + rr).cumprod()
    return dict(n=len(rr), ann_geo=((1+rr).prod()**(252/len(rr))-1)*100,
                ann_arith=rr.mean()*252*100,
                sr_d=rr.mean()/rr.std()*np.sqrt(252), sr_m=m.mean()/m.std()*np.sqrt(12),
                mdd=((eq/eq.cummax())-1).min()*100, vol=rr.std()*np.sqrt(252)*100,
                neg=int((yr < 0).sum()), worst=yr.min()*100)
