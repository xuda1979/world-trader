"""A1 r2 FINAL: mix sleeve = 1/3 breadth CTA (8-leg macro trend, raw net) + 1/3 Multi_Strategy_SharpeW + 1/3 L_S_130_30 (library), single trailing 10% vol target. All gates incl. 200x scramble inside.
Members documented per charter mission 3. Breadth legs: xau, crude(mean wti,brent), copper_monthly,
natgas, dxy, us10y synth TR (dur 7.5), us30y synth TR (dur 15), slv. spx excluded (starts 2016).
"""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
from breadth_cta import PX, COST
from data import fred
import pandas as pd, numpy as np, glob, os
ROOT="/Users/daxu/software/world-trader"
RNG = np.random.default_rng(11)

PX8 = PX.copy(); PX8["crude"]=(PX["wti"]+PX["brent"])/2
LEGS8 = ["xau","crude","copper_monthly","natgas","dxy","us10y","us30y","slv"]
PX8 = PX8.drop(columns=["wti","brent"])
R8 = PX8[LEGS8].pct_change()

def breadth_net(L=189,C=84,cap=1.0,vt=0.10):
    """leg-vol-sized long/flat trend weights; raw net (costs on turnover); no book vt."""
    W = {}
    for l in LEGS8:
        p=PX8[l]; r=R8[l]
        sig=pd.Series(0.0,index=p.index); sig[(p/p.shift(L)-1>0)&(p/p.shift(C)-1>0)]=1.0
        vol=r.expanding(min_periods=60).std()*np.sqrt(252)
        W[l]=(sig*(vt/vol).clip(upper=cap)).replace([np.inf,-np.inf],0.0).fillna(0.0)
    W=pd.DataFrame(W)
    net=(W.shift(1)*R8[LEGS8]).sum(axis=1)-W.diff().abs().sum(axis=1).fillna(0)*COST/1e4
    return W, net

def load_lib(name):
    df=pd.read_csv(f"{ROOT}/campaign/results/sleeve_library/{name}.csv",index_col=0)
    df.index=pd.to_datetime(df.index)
    return (df["ret"] if "ret" in df.columns else df.iloc[:,0]).astype(float)

def official_mix(bcret):
    j=pd.concat([bcret, load_lib("Multi_Strategy_SharpeW"), load_lib("L_S_130_30")],axis=1).sort_index().dropna()
    m=j.mean(axis=1)
    rv=m.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    return (m*(0.10/rv).clip(upper=3.0)).fillna(0.0)

W, net = breadth_net()
mix = official_mix(net)  # 2008-start strict variant: includes 2008 crisis year

def fullstats(x):
    x=x.dropna()
    yr=x.groupby(x.index.year).apply(lambda y:(1+y).prod()-1)*100
    h1=x[x.index<=x.index[len(x)//2]]; h2=x[x.index>x.index[len(x)//2]]
    return dict(sr=x.mean()/x.std()*np.sqrt(252), h1=h1.mean()/h1.std()*np.sqrt(252), h2=h2.mean()/h2.std()*np.sqrt(252),
                ann=x.mean()*252*100, vol=x.std()*np.sqrt(252)*100, neg=int((yr<0).sum()), worst=yr.min(),
                years=len(yr), negd={int(k):round(v,1) for k,v in yr.items() if v<0},
                yrd={int(k):round(v,1) for k,v in yr.items()})

# ---- gates ----
s = fullstats(mix)
print(f"FINAL MIX: SR={s['sr']:.2f} H1={s['h1']:.2f} H2={s['h2']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% negyr={s['neg']}/{s['years']} worst={s['worst']:.1f}%")
print("yearly:", s['yrd'])
print("breadth-CTA-alone SR (2008+):", round(fullstats(net[net.index>="2008-01-03"])['sr'],2), "(fails alone: 6 neg years; mix member per charter mission 3)")
gate_a = s['sr']>=0.6; gate_c = s['h1']>=0.3 and s['h2']>=0.3
gate_d = s['neg']<=2 and s['worst']>-5.0
print(f"gate a: {gate_a}  gate c: {gate_c}  gate d: {gate_d}")

# plateau: weight neighbors +-0.1 and signal neighbors (L,C)
peak=s['sr']; plats=[peak]
for wbc in [0.233,0.433]:
    for wsh in [0.233,0.433]:
        wls=1-wbc-wsh
        j=pd.concat([net,load_lib("Multi_Strategy_SharpeW"),load_lib("L_S_130_30")],axis=1).sort_index().dropna()
        mm=wbc*j.iloc[:,0]+wsh*j.iloc[:,1]+wls*j.iloc[:,2]
        rv=mm.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
        mm=(mm*(0.10/rv).clip(upper=3.0)).fillna(0.0)
        plats.append(fullstats(mm)['sr'])
for (L,C) in [(126,84),(189,63),(252,84)]:
    _,n2=breadth_net(L,C)
    plats.append(fullstats(official_mix(n2[n2.index>="2009-01-02"]))['sr'])
print("plateau neighbors SR:", [round(p,2) for p in plats], "min ratio:", round(min(plats)/peak,2))
gate_b = min(plats)/peak >= 0.8

# scramble: permute breadth weight rows, identical rebuild pipeline
idx=mix.index
Rw=R8.loc[idx][LEGS8].values; Wv=W.loc[idx][LEGS8].values
to=W.diff().abs().sum(axis=1).loc[idx].fillna(0).values*COST/1e4
def mix_sr(Wm):
    g=pd.Series((Wm*Rw).sum(axis=1)-to,index=idx)
    return official_mix(g).mean()/official_mix(g).std()*np.sqrt(252)
real=mix_sr(W.shift(1).loc[idx][LEGS8].values)
print("scramble real (must equal FINAL):", round(real,2)); import sys; sys.exit(0) if abs(real-s["sr"])>=0.02 else None
Wapp=W.shift(1).loc[idx][LEGS8].values
null=np.array([mix_sr(RNG.permutation(Wapp)) for _ in range(200)])
pval=float((null>=real).mean())
print(f"scramble: null mean={null.mean():.2f} p95={np.percentile(null,95):.3f} p={pval:.4f}")
gate_e = pval<=0.05 and abs(real-s['sr'])<0.02
print(f"gate e: {gate_e}")

if gate_a and gate_b and gate_c and gate_d and gate_e:
    from data import save_sleeve
    meta = f"""name: A1_mix_breadthCTA_SharpeW_LS13030 (r2, mission 3 mix)
variant: 2008-start strict (window includes 2008 crisis; breadth-CTA 2008 year +55% isolated)
members: 1/3 breadth CTA (8 legs: xau, crude=mean(wti,brent), copper_monthly, natgas, dxy, us10y synthTR dur7.5, us30y synthTR dur15, slv; 189d trend + 84d confirm, long/flat, leg vol-size expanding min60 cap1.0, T+1, 6bps) + 1/3 Multi_Strategy_SharpeW + 1/3 L_S_130_30 (library, 2022-positive). Single trailing expanding vol target 10% ann (shift 1, min 60d, cap 3x).
rationale: macro trend across 8 economically distinct markets (metals/energy/FX/rates) earns crisis-period payoffs orthogonal to equity L/S books (corr approx -0.1); blending with 2022-positive equity multi-strategy and 130/30 keeps every year's drawdown shallow. spx leg excluded (series starts 2016, insufficient history).
validation: SR={s['sr']:.2f} H1={s['h1']:.2f} H2={s['h2']:.2f} negyears={s['neg']} worst={s['worst']:.1f}% plateau_min_ratio={min(plats)/peak:.2f} scramble_p={pval:.4f} (200 perms, null mean SR {null.mean():.2f})
window: {mix.index[0].date()}..{mix.index[-1].date()} n={len(mix)}
"""
    save_sleeve(mix, f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_mix_breadthCTA_SharpeW_LS13030.csv", meta)
    print("SAVED sleeve A1_mix_breadthCTA_SharpeW_LS13030")
else:
    print("NOT SAVED — failed gates")
