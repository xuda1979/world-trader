"""
H1_optiontail — Direction 4: cross-sectional tail-pricing STATE ESTIMATION.
Single-date CBOE chain snapshot (2026-09-08). NO backtest (fail-open: only one
date of options data exists -> any backtest is impossible by construction).
Output: risk-neutral 30d return distribution per symbol via Breeden-Litzenberger
on SVI-fitted smiles, total-variance interpolated to T=30/365.
T+1 causal: uses only the 2026-09-08 snapshot (decision T, tradable T+1).
Offline: reads only tools/quant/data/cboe_options/latest/*.csv.
"""
import numpy as np, pandas as pd, glob, os
from scipy.stats import norm
from scipy.optimize import least_squares
from scipy.integrate import cumulative_trapezoid

SNAP   = pd.Timestamp('2026-09-08')
TARG_T = 30.0/365.0
DGRID  = 4000
DATA   = 'tools/quant/data/cboe_options/latest/'
OUT    = 'campaign/agents/H1_optiontail_results/'

def bs_call(S,K,r,q,tau,iv):
    v=iv*np.sqrt(tau); d1=(np.log(S/K)+(r-q+0.5*iv*iv)*tau)/v; d2=d1-v
    return S*np.exp(-q*tau)*norm.cdf(d1)-K*np.exp(-r*tau)*norm.cdf(d2)

def bs_put(S,K,r,q,tau,iv):
    return bs_call(S,K,r,q,tau,iv)-S*np.exp(-q*tau)+K*np.exp(-r*tau)

def fit_parity(df_e, S):
    """put-call parity regression per expiry: C-P = S e^{-q tau} - K e^{-r tau}"""
    p = df_e.pivot_table(index='strike', columns='typ', values='mid', aggfunc='mean').dropna()
    if len(p) < 8: return None
    b, a = np.polyfit(p.index.values.astype(float), (p['C']-p['P']).values, 1)
    tau = df_e['tau'].iloc[0]
    if b >= -1e-6 or a <= 0: return None
    r = -np.log(-b)/tau; q = -np.log(a/S)/tau
    if not (abs(r) < 0.20 and -0.10 < q < 0.30): return None
    return r, q

def svi_raw(p, k):
    a,b,rho,m,s = p
    return a + b*(rho*(k-m) + np.sqrt((k-m)**2 + s*s))

def fit_svi(k, w, tau):
    """total variance w(k)=iv^2*tau; SVI raw fit, butterfly-plausible"""
    k = np.asarray(k,float); w = np.asarray(w,float)
    def res(p): return svi_raw(p,k)-w
    atm = float(np.interp(0.0, k, w))
    best, bc = None, np.inf
    for rho0 in (-0.9,-0.5,0.0):
        p0 = [max(atm*0.5,1e-6), 0.1, rho0, 0.0, 0.1]
        lb = [0.0, 0.0, -0.999, -2.0, 1e-4]
        ub = [atm*4+0.2, 4.0, 0.999, 2.0, 4.0]
        try: r = least_squares(res, p0, bounds=(lb,ub), loss='soft_l1', f_scale=atm*0.05)
        except Exception: continue
        if r.cost < bc: bc, best = r.cost, r.x
    return best, bc

def smile_fit(df_e, F):
    """liquid OTM(+ATM) points -> SVI in total-variance space"""
    d = df_e[((df_e.typ=='P')&(df_e.strike<=F)) | ((df_e.typ=='C')&(df_e.strike>=F))].copy()
    d = d[((d.open_interest>=10)|(d.volume>=10)) & (d.ask>0) & (d.iv>0.01) & (d.iv<3.0)]
    d['k'] = np.log(d.strike/F)
    d = d.groupby('k', as_index=False).iv.mean()
    if len(d) < 6: return None
    k, w = d.k.values, (d.iv.values**2)*df_e.tau.iloc[0]
    p, cost = fit_svi(k, w, df_e.tau.iloc[0])
    # fallback: constrained quadratic in k if SVI degenerate
    if p is None or svi_raw(p,0.0)<=0:
        c2,c1,c0 = np.polyfit(k,w,2)
        if c2 < 0: c2 = 0.0
        p = np.array([c0,0.0,0.0,0.0,0.0]); p = None  # quad handled separately
        qfit = (c0,c1,c2)
        return ('quad', qfit, k.min(), k.max(), len(d))
    return ('svi', p, float(k.min()), float(k.max()), len(d))

def w_of(fit, k):
    kind, par, kmin, kmax, _ = fit
    if kind=='svi': return np.maximum(svi_raw(par, np.asarray(k,float)), 1e-8)
    c0,c1,c2 = par
    return np.maximum(c0 + c1*np.asarray(k,float) + c2*np.asarray(k,float)**2, 1e-8)

def build_symbol(sym):
    df = pd.read_csv(DATA+sym+'.csv', dtype={'exp':str})
    S  = float(df.spot.iloc[0])
    df['tau'] = (pd.to_datetime(df.exp)-SNAP).dt.days/365.0
    df['mid'] = (df.bid+df.ask)/2.0
    df = df[(df.tau>1.0/365)&(df.tau<=2.0)]
    surf, n_parity = [], 0
    for e in sorted(df.exp.unique()):
        de = df[df.exp==e]
        pq = fit_parity(de, S); n_parity += int(pq is not None)
        r, q = pq if pq else (0.045, 0.013)
        F = S*np.exp((r-q)*de.tau.iloc[0])
        ft = smile_fit(de, F)
        if ft is not None: surf.append((de.tau.iloc[0], r, q, ft))
    if len(surf) < 2: raise RuntimeError(f'only {len(surf)} usable expiries')
    # ---- surface: linear interp of total variance w(k,tau) across expiries
    def iv_at(k, tau_t):
        scalar = np.isscalar(k)
        ks = np.atleast_1d(np.asarray(k,float))
        ts = np.array([s[0] for s in surf])
        W  = np.vstack([w_of(s[3], ks) for s in surf])
        w  = np.array([np.interp(tau_t, ts, W[:,i]) for i in range(len(ks))])
        out = np.sqrt(np.maximum(w,1e-10)/tau_t)
        return float(out[0]) if scalar else out
    tau_t = TARG_T
    ts = np.array([s[0] for s in surf])
    r30 = float(np.interp(tau_t, ts, [s[1] for s in surf]))
    q30 = float(np.interp(tau_t, ts, [s[2] for s in surf]))
    F30 = S*np.exp((r30-q30)*tau_t)
    K = np.exp(np.linspace(np.log(0.25*S), np.log(3.0*S), DGRID))
    ivg = iv_at(np.log(K/F30), tau_t)
    C  = bs_call(F30, K, r30, q30, tau_t, ivg)
    f  = np.exp(r30*tau_t)*np.gradient(np.gradient(C, K), K)   # Breeden-Litzenberger
    f  = np.clip(f, 0, None)
    Z  = float(np.trapezoid(f, K)); f = f/Z
    cdf = cumulative_trapezoid(f, K, initial=0.0); cdf = cdf/cdf[-1]
    p20 = float(np.interp(0.8*S, K, cdf))
    R   = K/S - 1.0
    var95 = float(np.interp(0.05, cdf, R)); var99 = float(np.interp(0.01, cdf, R))
    X = np.log(K/S)
    m = [np.trapezoid(f*X**i, K) for i in (1,2,3,4)]
    mu, var = m[0], max(m[1]-m[0]**2, 1e-12)
    skew = (m[2]-3*mu*var-mu**3)/var**1.5
    kurt = (m[3]-4*mu*m[2]+6*mu*mu*var-3*mu**4)/var**2 - 3.0
    # ---- cross-check: model-free digital P(S_T<0.8S)=e^{rT}*dP/dK on same surface
    dk = 1e-4; K0 = 0.8*S
    Pp = float(bs_put(F30,K0*np.exp( dk),r30,q30,tau_t, iv_at(np.log(K0*np.exp( dk)/F30),tau_t)))
    Pm = float(bs_put(F30,K0*np.exp(-dk),r30,q30,tau_t, iv_at(np.log(K0*np.exp(-dk)/F30),tau_t)))
    p20_digital = float(np.exp(r30*tau_t)*(Pp-Pm)/(K0*(np.exp(dk)-np.exp(-dk))))
    near = [s for s in surf if abs(s[0]-tau_t) <= 45/365]
    diag = dict(symbol=sym, spot=S, n_expiries=len(surf), n_parity_ok=n_parity,
                norm_Z=Z, atm_iv_30d=float(iv_at(0.0,tau_t)),
                iv_80pct=float(iv_at(np.log(0.8),tau_t)),
                fit_k_min=min(s[3][2] for s in near), in_data_p20=bool(min(s[3][2] for s in near) <= np.log(0.8)),
                wing_mass_below_data=float(np.interp(F30*np.exp(min(s[3][2] for s in near)), K, cdf)),
                p_beyond_grid=float(np.interp(0.25*S, K, cdf)), p20_digital=p20_digital)
    return dict(symbol=sym, p20_30d=p20, var95=var95, var99=var99,
                skew=float(skew), kurt=float(kurt)), diag

rows, diags, rejects = [], [], []
for fp in sorted(glob.glob(DATA+'*.csv')):
    sym = os.path.basename(fp)[:-4]
    try:
        r, d = build_symbol(sym)
        # ---- FAIL-CLOSED gates: non-emitting on failure
        g1 = np.isfinite(d['norm_Z']) and 0.90 < d['norm_Z'] < 1.10
        g2 = 0 <= r['p20_30d'] < 1 and r['var99'] <= r['var95'] < 0
        g3 = abs(d['p20_digital']-r['p20_30d']) <= max(0.003, 0.35*r['p20_30d'])
        if not (g1 and g2 and g3):
            rejects.append((sym, f'norm_Z={d["norm_Z"]:.3f} p20={r["p20_30d"]:.5f} '
                                 f'digital={d["p20_digital"]:.5f} var95={r["var95"]:.4f} '
                                 f'var99={r["var99"]:.4f} g1={g1} g2={g2} g3={g3}'))
            continue
        rows.append(r); diags.append(d)
    except Exception as ex:
        rejects.append((sym, repr(ex))); print('REJECT', sym, repr(ex))

pd.DataFrame(rows)[['symbol','p20_30d','var95','var99','skew','kurt']].to_csv(OUT+'H1_tailfactor.csv', index=False)
pd.DataFrame(diags).to_csv(OUT+'H1_diagnostics.csv', index=False)
print(pd.DataFrame(rows).round(6).to_string(index=False))
print(pd.DataFrame(diags).round(4).to_string(index=False))
print('EMITTED:', len(rows), 'REJECTED:', len(rejects))
for s in rejects: print('  REJECT', s)
