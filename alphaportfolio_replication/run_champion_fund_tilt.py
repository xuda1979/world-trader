#!/usr/bin/env python3
"""FUNDAMENTAL TILT variant of the champion composite.

Tests the last untested lever (fundamental tilts): blend cross-sectional
rank-z VALUE/QUALITY signals into the momentum ranking.

Data: SEC EDGAR companyfacts (fundamentals_annual.parquet, 501 S&P 500
names, annual FY2009-2025, 6-month reporting lag). Overlap with the
twelve_big panel: 257/291 names.

Tilts (all cross-sectional rank-z per month):
  value   = book/price          (equity / (shares * price))
  quality = ROE rank-z          (net_income/equity)
  gm      = gross margin rank-z ((revenue-cogs)/revenue)
Signal = (1-TILT_W) * rank-z(momentum) + TILT_W * rank-z(tilt composite)

Baselines: champion SR 0.933/14.43%/-15.95%; +gold20 SR 1.053/15.10%/-15.00%.
Env: TILT_W, TILT_MODE in {value, quality, gm, vq (value+quality), all}
     GOLD_W (0 default, 0.2 to stack on top)
"""
from __future__ import annotations
import os, sys, glob
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import risk_gate as rg
BIG_DIR = os.path.join(HERE, "..", "tools", "quant", "data", "twelve_big")
FUND_PQ = os.path.join(HERE, "data", "fundamentals_annual.parquet")
GLD_CSV = os.path.join(HERE, "..", "tools", "quant", "data", "twelvedata", "GLD.csv")
START_YM = os.environ.get("START_YM", "2008-01")
COST_BPS = float(os.environ.get("COST_BPS", 6.0))
VOL_WIN = int(os.environ.get("VOL_WIN", 6))
GATE_LB = int(os.environ.get("GATE_LB", 10))
VOL_TARGET = float(os.environ.get("VOL_TARGET", 0.15))
REV_SLEEVE = float(os.environ.get("REV_SLEEVE", 0.3))
TILT_W = float(os.environ.get("TILT_W", 0.0))
TILT_MODE = os.environ.get("TILT_MODE", "all")
GOLD_W = float(os.environ.get("GOLD_W", 0.0))
TILT_LAG = int(os.environ.get("TILT_LAG", 6))  # months after fy-end before data usable
VIX_L1 = float(os.environ.get("VIX_L1", 20))
VIX_L2 = float(os.environ.get("VIX_L2", 25))
VIX_L3 = float(os.environ.get("VIX_L3", 30))
VIX_F1 = float(os.environ.get("VIX_F1", 0.75))
VIX_F2 = float(os.environ.get("VIX_F2", 0.5))
VIX_F3 = float(os.environ.get("VIX_F3", 0.3))
MOM_LB = [int(x) for x in os.environ.get("MOM_LB", "3 6 12").split()]
G_DIV = int(os.environ.get("G_DIV", 4))  # top 1/G_DIV of names held
VOL_CAP = float(os.environ.get("VOL_CAP", 1.5))  # max vol-target scale
DD_L1 = float(os.environ.get("DD_L1", -0.08))
DD_L2 = float(os.environ.get("DD_L2", -0.12))
DD_F1 = float(os.environ.get("DD_F1", 0.5))
DD_F2 = float(os.environ.get("DD_F2", 0.25))  # DD reducer thresholds/factors
REBAL_FREQ = int(os.environ.get("REBAL_FREQ", 1))  # months between rebalances (1=m, 3=q)
SOFT_GATE = int(os.environ.get("SOFT_GATE", 0))  # 1 = proportional SPY-MA gate
V_W = float(os.environ.get("V_W", 1.0))
Q_W = float(os.environ.get("Q_W", 1.0))  # value/quality balance in vq mode
def build_panel():
    files = sorted(glob.glob(os.path.join(BIG_DIR, "*.csv")))
    all_m=[]
    for f in files:
        sym=os.path.basename(f).replace(".csv","")
        try:
            df=pd.read_csv(f, index_col=0, parse_dates=True)
            c="close" if "close" in df.columns else df.columns[0]
            m=df[c].astype(float).resample("ME").last().dropna(); m.name=sym
            all_m.append(m)
        except: continue
    return pd.concat(all_m,axis=1).sort_index().ffill()
def build_fund_tilts(px):
    """Monthly cross-sectional rank-z tilt signals, mapped to panel index."""
    f = pd.read_parquet(FUND_PQ)
    f = f[f.symbol.isin(px.columns)]
    f = f[f.shares > 0]
    # book value, ROE, gross margin per fy
    f = f.assign(book=f.equity, roe=f.net_income / f.equity.replace(0, np.nan),
                 gm=(f.revenue - f.cogs) / f.revenue.replace(0, np.nan),
                 prof=f.op_income / f.total_assets.replace(0, np.nan),
                 ag=(f.total_assets - f.groupby('symbol').total_assets.shift(1)) / f.groupby('symbol').total_assets.shift(1).replace(0, np.nan))
    out = {}
    for mode in ["value", "quality", "gm", "prof", "ag"]:
        col = {"value": "book", "quality": "roe", "gm": "gm", "prof": "prof", "ag": "ag"}[mode]
        s = f[["symbol", "fy", col]].dropna()
        s = s[s[col] != 0]
        # map to month index: fy Y available LAG months after year-end
        m = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
        for fy in sorted(s.fy.unique()):
            if int(fy) + 1 > 2027: continue
            sub = s[s.fy == fy]
            if sub.empty: continue
            vals = dict(zip(sub.symbol, sub[col]))
            months = sorted(set(px.index[px.index >= pd.Timestamp(f"{int(fy)+1}-{TILT_LAG:02d}-01")]))
            for month in months:
                m.loc[month] = vals
        out[mode] = m
    return out
def rank_z(s: pd.Series) -> pd.Series:
    r = s.rank(pct=True)
    return (r - r.mean()) / (r.std() + 1e-9)
def LM(dt,sig,fwd):
    if isinstance(sig, pd.Series):
        s=sig.dropna()
    else:
        s=sig.loc[dt].dropna()
    fr=fwd.loc[dt]; c=s.index.intersection(fr.dropna().index)
    if len(c)<20: return 0.0
    s=s.loc[c]; fr2=fr.loc[c]; G=max(1,len(c)//G_DIV); r2=s.sort_values(ascending=False)
    return fr2.loc[r2.index[:G]].mean()
def SP(dt,sig,fwd):
    fr=fwd.loc[dt]; s=sig.loc[dt].dropna(); c=s.index.intersection(fr.dropna().index)
    if len(c)<20: return 0.0
    s=s.loc[c]; fr2=fr.loc[c]; G=max(1,len(c)//G_DIV); r2=s.sort_values(ascending=False)
    return fr2.loc[r2.index[:G]].mean()-fr2.loc[r2.index[-G:]].mean()
def main():
    print("Building panel...", flush=True)
    px=build_panel()
    print(f"Panel: {px.shape[0]}mo x {px.shape[1]} stocks", flush=True)
    fwd=px.pct_change(1).shift(-1)
    comp=sum(px.pct_change(n) for n in MOM_LB)/len(MOM_LB)
    rev=-px.pct_change(2)
    spy=rg.load_daily("SPY").resample("ME").last()
    vix=rg.load_daily("vix").resample("ME").last()
    gld=pd.read_csv(GLD_CSV, index_col=0, parse_dates=True)
    c="close" if "close" in gld.columns else gld.columns[0]
    gld_r=gld[c].astype(float).resample("ME").last().pct_change().reindex(px.index).fillna(0.0)
    tilts = build_fund_tilts(px)
    if TILT_MODE in ("value","quality","gm","prof","ag"):
        tilt = tilts[TILT_MODE]
    elif TILT_MODE == "vq":
        tilt = tilts["value"].mul(V_W).add(tilts["quality"].mul(Q_W)).div(V_W+Q_W)
    elif TILT_MODE == "vqp":
        tilt = tilts["value"].add(tilts["quality"]).add(tilts["prof"]).div(3)
    elif TILT_MODE == "vqpa":
        tilt = tilts["value"].add(tilts["quality"]).add(tilts["prof"]).add(tilts["ag"].mul(-1)).div(4)
    else:
        tilt = tilts["value"].add(tilts["quality"]).add(tilts["gm"]).div(3)
    oos=[d for d in px.index if d.strftime("%Y-%m")>=START_YM]
    v=lambda dt: float(vix.asof(dt)) if pd.notna(vix.asof(dt)) else 20
    def sp10(dt):
        x = float(spy.asof(dt)); m = float(spy[spy.index<=dt].tail(GATE_LB).mean())
        if SOFT_GATE:
            # proportional: 1 at >=MA, linear 0..1 for -10%..0 below MA
            return 1.0 if x>=m else max(0.0, 1 + (x/m - 1)*10)
        return 1.0 if x>=m else 0.0
    vg=lambda dt: VIX_F3 if v(dt)>VIX_L3 else (VIX_F2 if v(dt)>VIX_L2 else (VIX_F1 if v(dt)>VIX_L1 else 1.0))
    raw=[]; cost_arr=[]; prev_mom=None; prev_rev=None
    rebal_months = {d for d in oos if (d.year*12 + d.month - 1) % REBAL_FREQ == 0}
    held_mom = None; held_rev = None  # name sets frozen between rebalances
    held_mom_n = 0; held_rev_n = 0
    for dt in oos:
        if dt in rebal_months:
            mom_sig = comp.loc[dt].dropna()
            t = tilt.loc[dt] if dt in tilt.index else None
            if TILT_W > 0 and t is not None and t.dropna().shape[0] > 30:
                mz = rank_z(mom_sig.reindex(t.dropna().index).dropna())
                tz = rank_z(t.dropna().reindex(mz.index).dropna())
                c_ = mz.index.intersection(tz.index)
                if len(c_) > 30:
                    mom_sig = (1-TILT_W)*mz.loc[c_] + TILT_W*tz.loc[c_]
            fr0 = fwd.loc[dt].dropna()
            s = mom_sig.dropna(); c = s.index.intersection(fr0.index)
            held_mom_n = len(c)
            G = max(1, len(c)//G_DIV)
            r2 = s.loc[c].sort_values(ascending=False)
            held_mom = set(r2.index[:G].tolist())
            r = rev.loc[dt].dropna(); c2 = r.index.intersection(fr0.index)
            held_rev_n = len(c2)
            r3 = r.loc[c2].sort_values(ascending=False)
            held_rev = (set(r3.index[:G].tolist()), set(r3.index[-G:].tolist()))
            cur_mom, cur_rev = held_mom, held_rev
            if prev_mom is None:
                cost_arr.append(0.0)
            else:
                mo = 1 - len(prev_mom & cur_mom)/max(1,len(cur_mom))
                rp, rs = prev_rev; cp, cs = cur_rev
                ro = (1-len(rp&cp)/max(1,len(cp)) + 1-len(rs&cs)/max(1,len(cs)))/2
                cost_arr.append(COST_BPS/1e4 * (mo + REV_SLEEVE*2*ro))
            prev_mom, prev_rev = cur_mom, cur_rev
        else:
            cost_arr.append(0.0)
        # realized return of the held book this month (fwd.loc[dt] = next-month rets)
        fr = fwd.loc[dt].dropna(); fri = set(fr.index)
        if held_mom and held_mom_n >= 20:
            have = [x for x in held_mom if x in fri]
            momp = 1.0*sp10(dt)*fr.loc[have].mean() if have else 0.0
        else:
            momp = 0.0
        if held_rev and held_rev_n >= 20:
            long_ = [x for x in held_rev[0] if x in fri]
            short_ = [x for x in held_rev[1] if x in fri]
            revp = REV_SLEEVE*(fr.loc[long_].mean() - fr.loc[short_].mean()) if long_ and short_ else 0.0
        else:
            revp = 0.0
        book = (momp + revp)*vg(dt)
        gr = float(gld_r.loc[dt]) if dt in gld_r.index else 0.0
        raw.append((1-GOLD_W)*book + GOLD_W*gr)
    raw=np.array(raw); cost_arr=np.array(cost_arr)
    net=raw-cost_arr
    print(f"COST: drag={cost_arr.mean()*12*100:.2f}%/yr one-way_turn={cost_arr.mean()/(COST_BPS/1e4):.1%}/mo")
    scaled=np.zeros(len(net)); eq=1.0; peak=1.0
    for i in range(len(net)):
        s=1.0
        if i>=6:
            rv=np.std(net[max(0,i-VOL_WIN):i])*np.sqrt(12)+1e-6
            s=min(VOL_TARGET/rv, VOL_CAP)
            cur_dd=eq/peak-1
            if cur_dd<DD_L2: s*=DD_F2
            elif cur_dd<DD_L1: s*=DD_F1
        scaled[i]=net[i]*s
        eq*=(1+scaled[i]); peak=max(peak,eq)
    r=scaled
    sr=r.mean()/r.std()*np.sqrt(12) if r.std()>0 else 0
    ann=r.mean()*12*100; vol=r.std()*np.sqrt(12)*100
    eq2=np.cumprod(1+r); dd=min((eq2[i]/max(eq2[:i+1])-1) for i in range(len(eq2)))*100
    half=len(r)//2
    print(f"TILT mode={TILT_MODE} w={TILT_W:.2f} gold={GOLD_W:.0%}: SR={sr:.3f} ret={ann:+.2f}% "
          f"vol={vol:.2f}% MaxDD={dd:.2f}% half={r[:half].mean()/r[:half].std()*np.sqrt(12):.3f}/"
          f"{r[half:].mean()/r[half:].std()*np.sqrt(12):.3f} n={len(r)} NET6bps")
    pd.DataFrame({"ym":[d.strftime("%Y-%m") for d in oos[:len(r)]], "net":r}).to_csv(
        os.path.join(HERE,"data",os.environ.get("OUT_CSV","wf_champion_final.csv")), index=False)
if __name__=="__main__": main()
