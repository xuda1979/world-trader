import pandas as pd, numpy as np, os, glob, sys
sys.path.insert(0, ".")
import risk_gate as rg
files = sorted(glob.glob("../tools/quant/data/twelve_big/*.csv"))
all_m = []
for f in files:
    sym = os.path.basename(f).replace(".csv","")
    try:
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        c = "close" if "close" in df.columns else df.columns[0]
        m = df[c].astype(float).resample("ME").last().dropna(); m.name=sym
        all_m.append(m)
    except: continue
px = pd.concat(all_m, axis=1).sort_index().ffill()
fwd = px.pct_change(1).shift(-1)
comp = (px.pct_change(3)+px.pct_change(6)+px.pct_change(12))/3
rev = -px.pct_change(2)
spy = rg.load_daily("SPY").resample("ME").last()
vix = rg.load_daily("vix").resample("ME").last()
oos = [d for d in px.index if d.strftime("%Y-%m") >= "2008-01"]
def LM(dt,sig):
    fr=fwd.loc[dt]; s=sig.loc[dt].dropna(); c=s.index.intersection(fr.dropna().index)
    if len(c)<20: return 0.0
    s=s.loc[c]; fr2=fr.loc[c]; G=max(1,len(c)//4); r2=s.sort_values(ascending=False)
    return fr2.loc[r2.index[:G]].mean()
def SP(dt,sig):
    fr=fwd.loc[dt]; s=sig.loc[dt].dropna(); c=s.index.intersection(fr.dropna().index)
    if len(c)<20: return 0.0
    s=s.loc[c]; fr2=fr.loc[c]; G=max(1,len(c)//4); r2=s.sort_values(ascending=False)
    return fr2.loc[r2.index[:G]].mean()-fr2.loc[r2.index[-G:]].mean()
v = lambda dt: float(vix.asof(dt)) if pd.notna(vix.asof(dt)) else 20
sp10 = lambda dt: 1.0 if float(spy.asof(dt)) >= spy[spy.index<=dt].tail(10).mean() else 0.0
vg = lambda dt: 0.3 if v(dt)>30 else (0.5 if v(dt)>25 else (0.75 if v(dt)>20 else 1.0))
mrets = [LM(d, comp) for d in oos]
# Triple-confirmation crash filter: only de-risk when ALL three signal
# 1. Momentum sleeve lost >6% last month
# 2. VIX > 25 (elevated)
# 3. SPY below 10-month MA (downtrend)
def crash_filter(i, dt):
    if i == 0: return 1.0
    mom_crash = mrets[i-1] < -0.06
    vix_high = v(dt) > 25
    spy_down = sp10(dt) < 0.5
    if mom_crash and vix_high and spy_down:
        return 0.2  # aggressive de-risk only on triple confirmation
    return 1.0
# Test with vol target + DD reducer
for rev_w, label in [(0.3, "rev30"), (0.4, "rev40"), (0.5, "rev50")]:
    raw = []
    for i, dt in enumerate(oos):
        cf = crash_filter(i, dt)
        momp = 1.0 * sp10(dt) * cf * LM(dt, comp)
        revp = rev_w * SP(dt, rev)
        raw.append((momp + revp) * vg(dt))
    raw = np.array(raw)
    # vol target 15% + DD reducer
    sc = np.zeros(len(raw)); eq = 1.0; peak = 1.0
    for i in range(len(raw)):
        s = 1.0
        if i >= 6:
            rv = np.std(raw[max(0,i-6):i]) * np.sqrt(12) + 1e-6
            s = min(0.15 / rv, 1.5)
            cur_dd = eq / peak - 1
            if cur_dd < -0.12: s *= 0.25
            elif cur_dd < -0.08: s *= 0.5
        sc[i] = raw[i] * s
        eq *= (1 + sc[i]); peak = max(peak, eq)
    r = sc
    sr = r.mean() / r.std() * np.sqrt(12) if r.std() > 0 else 0
    eq2 = np.cumprod(1 + r)
    dd = min((eq2[i] / max(eq2[:i+1]) - 1) for i in range(len(eq2))) * 100
    print(f"triple + {label}: SR={sr:.2f} ret={r.mean()*12*100:.1f}% DD={dd:.1f}%")
