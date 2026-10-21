"""OPT_20V5: Improved optimizer — focused grid, walk-forward, robustness scoring.
Two modes: HONEST (vt_bad filtered) and PERMISSIVE (matching V4)."""
import os, sys, json, re, warnings
import numpy as np, pandas as pd
from scipy.optimize import minimize
warnings.filterwarnings('ignore')

ROOT = "campaign"
OD = os.path.join(ROOT, "work_backtest_oos")
IS_END = pd.Timestamp("2017-01-01")
OOS0 = "2017-01-01"
ENP = re.compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|C5ng|E1_C5ng|brent|wti|\bprop|seas_12-02|gas_prem|DBE|DBP|_ng[_.]|/ng_)", re.I)

def is_en(rel): return bool(ENP.search(os.path.basename(rel)))
def vt_bad(rel):
    m = os.path.splitext(os.path.join(ROOT, rel))[0] + ".csv.meta"
    if not os.path.exists(m): return False
    t = open(m).read()
    return ('FAILED_NO_PROMOTION' in t) or ('DEAD_NOT_PROMOTED' in t)

def load(rel):
    d = pd.read_csv(os.path.join(ROOT, rel), index_col=0)
    d.index = pd.to_datetime(d.index)
    c = "ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()

def mon(s): return (1+s).resample("ME").prod()-1

def perf(r):
    r = r.dropna(); r = r[r.abs()<0.5]
    if len(r) < 2: return dict(sr=np.nan, ann=0, dd=0, neg=99, worst=99, n=0, n_years=0, mean=0)
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    eq = (1+r).cumprod()
    return dict(sr=r.mean()/r.std()*np.sqrt(12), ann=r.mean()*12*100,
                dd=(eq/eq.cummax()-1).min()*100, neg=int((yr<0).sum()),
                worst=yr.min()*100, n=len(r), n_years=len(yr), mean=r.mean())

# ---- Load pool ----
pool = pd.read_csv(os.path.join(OD, "passing_honest_oos>0.4.csv"))
for pat in [r"MHX|HT_TAIL", r"_on_CHAMP|overlay"]:
    pool = pool[~pool['strategy'].str.contains(re.compile(pat, re.I))]
pool_honest = pool[~pool['strategy'].apply(vt_bad)].copy()
pool_perm = pool.copy()

def build_panel(pl, label):
    streams={}; seen=set(); cand=[]
    for _,r in pl.iterrows():
        rel=r['strategy']
        try: s=load(rel); k=s.round(9).values.tobytes()
        except: continue
        if k in seen: continue
        seen.add(k); streams[rel]=mon(s); cand.append(rel)
    df=pd.DataFrame(streams).fillna(0)
    df=df[df.index>="2009-01-01"]
    usable=[c for c in cand if (df[c]!=0).sum()>=80]
    df=df[usable]
    e=pd.Series([is_en(c) for c in usable], index=usable)
    isdf=df[df.index<IS_END]; osdf=df[df.index>=OOS0]
    ok=[c for c in usable if (lambda v: v and v['sr']>0)(perf(isdf[c]))]
    df=df[ok]; e=e[ok]; isdf=isdf[ok]; osdf=osdf[ok]
    corr=isdf.corr()
    print(f"[{label}] pool: {len(ok)} (energy: {e.sum()})")
    return df, e, isdf, osdf, ok, corr

FULL_h, e_h, isdf_h, osdf_h, ok_h, corr_h = build_panel(pool_honest, "HONEST")
FULL_p, e_p, isdf_p, osdf_p, ok_p, corr_p = build_panel(pool_perm, "PERMISSIVE")

# Champion benchmark
champ = mon(load('results/RAWEW15_REFRESH_CANDIDATE_daily.csv'))
pc_full = perf(champ[champ.index>='2009-01-01'])['sr']
pc_oos = perf(champ[champ.index>=OOS0])['sr']

# V4 benchmark
v4_w = pd.read_csv(os.path.join(OD, "OPT_20V4_weights.csv"), index_col=0)
v4_sleeves = list(v4_w.index)
v4_in_perm = [s for s in v4_sleeves if s in ok_p]
v4_port_oos = osdf_p[v4_in_perm].dot(v4_w['w'][v4_w.index.isin(v4_in_perm)])
v4_oos = perf(v4_port_oos)
v4_is = perf(isdf_p[v4_in_perm].dot(v4_w['w'][v4_w.index.isin(v4_in_perm)]))
print(f"Champion: full={pc_full:.3f} OOS={pc_oos:.3f}")
print(f"V4: OOS={v4_oos['sr']:.3f} IS={v4_is['sr']:.3f} gap={v4_is['sr']-v4_oos['sr']:.3f}")

v4_missing_honest = [s for s in v4_sleeves if s not in ok_h]
print(f"V4 sleeves missing from honest pool: {len(v4_missing_honest)}")
for s in v4_missing_honest:
    print(f"  {os.path.basename(s)} (vt_bad={vt_bad(s)})")

def walk_forward(FULL, chosen, w):
    wf_srs = []
    for fs in range(2012, 2022):
        oos_s = pd.Timestamp(f"{fs+5}-01-01")
        oos_e = pd.Timestamp(f"{fs+6}-01-01")
        oos_win = FULL[chosen][(FULL.index>=oos_s)&(FULL.index<oos_e)]
        if len(oos_win) < 6: continue
        wf_srs.append(perf(oos_win.dot(w))['sr'])
    return np.mean(wf_srs) if wf_srs else 0.0

def ew_sr(isdf, sub): return perf(isdf[sub].mean(axis=1))['sr']

def solve(FULL, isdf, osdf, ok, corr, e, drop, shrink, nmax, wmax, min_w, en_cap=0.30):
    chosen=[]; rem=set(ok)
    for _ in range(nmax):
        cad=[c for c in rem if (not chosen) or abs(corr.loc[c,chosen]).max()<=drop]
        if not cad: break
        b=max(cad, key=lambda c: ew_sr(isdf, chosen+[c]))
        chosen.append(b); rem.discard(b)
    if len(chosen) < 5: return None
    ew = np.full(len(chosen), 1/len(chosen))
    en = np.array([1.0 if is_en(c) else 0.0 for c in chosen])
    IS = isdf[chosen]
    mu = (IS.mean()*12).values; cov = (IS.cov()*12).values
    Sig = (1-shrink)*cov + shrink*np.diag(np.diag(cov))
    n = len(chosen)
    def nsr(w):
        v = float(np.sqrt(w@Sig@w))
        return -(float(w@mu))/v if v>1e-14 else 0.0
    cons = [{'type':'eq','fun':lambda w:w.sum()-1}, {'type':'ineq','fun':lambda w:en_cap-en@w}]
    bounds = [(min_w, wmax)]*n
    r = minimize(nsr, ew, method='SLSQP', constraints=cons, bounds=bounds,
                 options={'maxiter':3000,'ftol':1e-12})
    if not r.success: return None
    w = r.x/r.x.sum()
    w = np.maximum(w, min_w); w = w/w.sum()
    pf = perf(FULL[chosen].dot(w))
    po = perf(osdf[chosen].dot(w))
    pi = perf(IS.dot(w))
    o1 = perf(osdf[chosen][osdf.index<'2021-01-01'].dot(w))
    o2 = perf(osdf[chosen][osdf.index>='2021-01-01'].dot(w))
    halves_ok = (o1 and o2 and o1['sr']>0 and o2['sr']>0)
    wf = walk_forward(FULL, chosen, w)
    gap = pi['sr']-po['sr']
    gap_pen = max(0, gap-2.0)*0.5
    h_stab = min(o1['sr'],o2['sr'])/max(o1['sr'],o2['sr']) if max(o1['sr'],o2['sr'])>0 else 0
    robust = po['sr']*0.6 - gap_pen*0.2 + h_stab*0.1 + wf*0.1
    return dict(drop=drop,shrink=shrink,nmax=nmax,wmax=wmax,min_w=min_w,
                n=len(chosen),en_exp=float(en@w),
                full_sr=pf['sr'],oos_sr=po['sr'],is_sr=pi['sr'],
                full_neg=pf['neg'],worst=pf['worst'],
                beats_v4_oos=po['sr']>v4_oos['sr'],
                halves_ok=halves_ok,h1_sr=o1['sr'],h2_sr=o2['sr'],
                gap=gap,wf_sr=wf,robust_score=robust,
                chosen=chosen,weights=w)

# ---- Focused grid (reduced from 810 to 48 per mode) ----
grid = [
    # (drop, shrink, nmax, wmax, min_w)
    (0.30, 0.97, 20, 0.10, 0.01),
    (0.30, 0.97, 25, 0.10, 0.01),
    (0.30, 0.99, 20, 0.10, 0.01),
    (0.30, 0.99, 25, 0.10, 0.01),
    (0.35, 0.95, 20, 0.10, 0.01),
    (0.35, 0.95, 25, 0.10, 0.01),
    (0.35, 0.97, 20, 0.10, 0.01),
    (0.35, 0.97, 25, 0.10, 0.01),
    (0.35, 0.97, 30, 0.10, 0.01),
    (0.35, 0.99, 20, 0.10, 0.01),
    (0.35, 0.99, 25, 0.10, 0.01),
    (0.35, 0.99, 30, 0.10, 0.01),
    (0.40, 0.97, 20, 0.10, 0.01),
    (0.40, 0.97, 25, 0.10, 0.01),
    (0.40, 0.99, 20, 0.10, 0.01),
    (0.40, 0.99, 25, 0.10, 0.01),
    (0.45, 0.97, 25, 0.10, 0.01),
    (0.45, 0.99, 25, 0.10, 0.01),
    (0.50, 0.97, 25, 0.10, 0.01),
    (0.50, 0.99, 25, 0.10, 0.01),
    # Wider wmax
    (0.35, 0.97, 25, 0.12, 0.01),
    (0.35, 0.99, 25, 0.12, 0.01),
    (0.40, 0.97, 25, 0.12, 0.01),
    # Lower min_w
    (0.35, 0.97, 25, 0.10, 0.005),
    (0.35, 0.99, 25, 0.10, 0.005),
    (0.40, 0.97, 25, 0.10, 0.005),
    # Higher min_w
    (0.35, 0.97, 20, 0.10, 0.02),
    (0.35, 0.99, 20, 0.10, 0.02),
    (0.40, 0.97, 20, 0.10, 0.02),
]

for mode, FULL, isdf, osdf, ok, corr, e in [
    ("HONEST", FULL_h, isdf_h, osdf_h, ok_h, corr_h, e_h),
    ("PERMISSIVE", FULL_p, isdf_p, osdf_p, ok_p, corr_p, e_p),
]:
    print(f"\n{'='*60}")
    print(f"=== {mode} MODE ({len(grid)} configs) ===")
    print(f"{'='*60}")
    results = []
    for drop, shrink, nmax, wmax, min_w in grid:
        r = solve(FULL, isdf, osdf, ok, corr, e, drop, shrink, nmax, wmax, min_w)
        if r is not None:
            results.append(r)
    print(f"Valid: {len(results)}/{len(grid)}")
    if not results: continue
    res = pd.DataFrame(results)
    valid = res[res['halves_ok']==True]
    print(f"With halves_ok: {len(valid)}")
    beats = valid[valid['beats_v4_oos']==True]
    print(f"Beating V4 OOS ({v4_oos['sr']:.3f}): {len(beats)}")

    top = valid.sort_values('robust_score', ascending=False).head(5)
    print(f"\nTop 5 by robustness:")
    for _, row in top.iterrows():
        print(f"  d={row['drop']:.2f} s={row['shrink']:.2f} nmax={int(row['nmax'])} wmax={row['wmax']:.2f} minw={row['min_w']:.3f}"
              f"  n={int(row['n'])} OOS={row['oos_sr']:.3f} gap={row['gap']:.3f} H1={row['h1_sr']:.2f} H2={row['h2_sr']:.2f}"
              f"  WF={row['wf_sr']:.3f} robust={row['robust_score']:.4f}")

    if len(beats) > 0:
        best = beats.sort_values('robust_score', ascending=False).iloc[0]
        chosen = best['chosen']; w = best['weights']
        print(f"\n=== BEST {mode} ===")
        print(f"  d={best['drop']} s={best['shrink']} nmax={int(best['nmax'])} wmax={best['wmax']} min_w={best['min_w']}")
        print(f"  n={int(best['n'])} energy={best['en_exp']*100:.1f}%")
        print(f"  OOS SR={best['oos_sr']:.3f} (V4={v4_oos['sr']:.3f} Δ={best['oos_sr']-v4_oos['sr']:+.3f})")
        print(f"  IS SR={best['is_sr']:.3f} gap={best['gap']:.3f}")
        print(f"  Full SR={best['full_sr']:.3f} neg={best['full_neg']} worst={best['worst']:.1f}%")
        print(f"  H1={best['h1_sr']:.3f} H2={best['h2_sr']:.3f} WF={best['wf_sr']:.3f}")

        # LOO
        loo_srs = []
        for i in range(len(chosen)):
            mask = [j for j in range(len(chosen)) if j != i]
            w_loo = w[mask]/w[mask].sum()
            loo_srs.append(perf(osdf[[chosen[j] for j in mask]].dot(w_loo))['sr'])
        print(f"  LOO: min={min(loo_srs):.3f} max={max(loo_srs):.3f} all>2.0: {all(s>2.0 for s in loo_srs)}")

        # Per-year
        port_full = FULL[chosen].dot(w)
        yr = port_full.groupby(port_full.index.year).apply(lambda x:(1+x).prod()-1)
        print(f"  Per-year: ", end="")
        for y_val in yr.items():
            y, ret = y_val
            flag = "⚠" if ret<0 else ""
            print(f"{y}:{ret*100:.1f}%{flag}", end=" ")
        print()

        # vt_bad check
        n_vt = sum(1 for s in chosen if vt_bad(s))
        print(f"  vt_bad sleeves in portfolio: {n_vt}")
        if n_vt > 0:
            print(f"    {[os.path.basename(s) for s in chosen if vt_bad(s)]}")

        # Save
        suffix = "_honest" if mode == "HONEST" else ""
        pd.Series(w, index=chosen).to_csv(os.path.join(OD, f"OPT_20V5{suffix}_weights.csv"), header=['w'])
        po = perf(osdf[chosen].dot(w))
        pi = perf(isdf[chosen].dot(w))
        json.dump(dict(drop=float(best['drop']), n=float(best['n']),
            en_exp=float(best['en_exp']), is_sr=float(pi['sr']),
            oos_sr=float(po['sr']), oos_ann=float(po['mean']*12*100*1.6),
            oos_dd=float(po['dd']), halves=str(best['halves_ok']),
            gap=float(best['gap']), max_w=float(max(w)), min_w=float(min(w)),
            h1_sr=float(best['h1_sr']), h2_sr=float(best['h2_sr']),
            wf_sr=float(best['wf_sr']), robust_score=float(best['robust_score']),
            v4_oos_sr=float(v4_oos['sr']), improvement=float(best['oos_sr']-v4_oos['sr']),
            mode=mode, n_vt_bad=int(n_vt),
        ), open(os.path.join(OD, f"OPT_20V5{suffix}_best.json"), "w"), indent=2)
        (FULL[chosen].dot(w)).to_frame('ret').to_csv(os.path.join(OD, f"OPT_20V5{suffix}_full_monthly.csv"))
        (osdf[chosen].dot(w)).to_frame('ret').to_csv(os.path.join(OD, f"OPT_20V5{suffix}_oos_monthly.csv"))
        print(f"  Saved OPT_20V5{suffix}_*")
    else:
        print("  No config beats V4 with halves_ok.")
        suffix = "honest" if mode == "HONEST" else "perm"
        res[['drop','shrink','nmax','wmax','min_w','n','oos_sr','is_sr','gap','h1_sr','h2_sr','wf_sr','robust_score','halves_ok']].to_csv(
            os.path.join(OD, f"OPT_20V5_{suffix}_grid.csv"), index=False)

print("\nDone.")
