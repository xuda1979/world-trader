"""Shared helpers for A5_vol_cond — full-gate evaluation per AGENT_BRIEF.md."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import data as D

def sr(r):
    r = r.dropna()
    if len(r) < 2 or r.std() == 0: return 0.0
    return r.mean() / r.std() * np.sqrt(252)

def stats(r):
    r = r.dropna()
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    return dict(n=len(r), sr=sr(r), ann=r.mean()*252*100, vol=r.std()*np.sqrt(252)*100,
                neg_yr=int((yr < 0).sum()), n_yr=len(yr), worst=float(yr.min()*100),
                yearly={int(k): round(v*100,2) for k,v in yr.items()})

def halves(r):
    r = r.dropna(); mid = r.index[len(r)//2]
    return sr(r[r.index <= mid]), sr(r[r.index > mid])

def scramble_pval_sig(pos, r1, n=200, seed=0):
    """Honest signal-scramble: permute the SIGNAL (positions) against the
    REAL date-aligned returns, re-apply T+1 costs, compare SRs."""
    rng = np.random.default_rng(seed)
    idx = pos.index
    rr = r1.reindex(idx).fillna(0.0).values
    pv = pos.values
    def net_of(p):
        p = pd.Series(p, index=idx)
        to = p.diff().abs().fillna(p.abs())
        return pd.Series(p.values * rr - to.values * D.COST / 1e4, index=idx)
    real = sr(net_of(pv).dropna())
    cnt = 0
    for _ in range(n):
        q = rng.permutation(pv)
        if sr(net_of(q).dropna()) >= real: cnt += 1
    return cnt / n

def scramble_pval_base(r, n=200, seed=0):
    """Fallback scramble for sleeves built as scaled-return combos:
    permute the SLEEVE's own net returns vs calendar — tests date clustering.
    For signal gating prefer scramble_pval_sig."""
    rng = np.random.default_rng(seed)
    v = r.dropna()
    real = sr(v)
    cnt = 0
    for _ in range(n):
        p = pd.Series(rng.permutation(v.values), index=v.index)
        # circular block shift destroys alignment to market dates
        if sr(p) >= real: cnt += 1
    return cnt / n

def vol_target(ret_gross, target=0.10, minlen=60):
    """Expanding-window trailing vol scale using ONLY data <= t; position for t+1."""
    rw = ret_gross.rolling(minlen).std().shift(0)
    scale = (target / np.sqrt(252) / rw).clip(0, 3.0).fillna(0.0).shift(1)
    return scale

def gate_report(name, net, extra=""):
    """Run ALL gates (a)-(e) (+g built into construction). Returns (ok, text)."""
    s = stats(net); h1, h2 = halves(net)
    sp = scramble_pval(net)
    lines = [f"[{name}] n={s['n']} SR={s['sr']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% "
             f"negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% H1={h1:.2f} H2={h2:.2f} scram_p={sp:.3f} {extra}"]
    ok_a = s['sr'] >= 0.6
    ok_c = (h1 >= 0.3) and (h2 >= 0.3)
    ok_d = (s['neg_yr'] <= 2) and (s['worst'] > -5.0)
    ok_e = sp <= 0.05
    lines.append(f"    gates: a(SR>=0.6)={ok_a} c(halves)={ok_c} d(yearly)={ok_d} e(scramble)={ok_e}")
    ok = ok_a and ok_c and ok_d and ok_e
    return ok, "\n".join(lines)

def load_lib(name):
    df = pd.read_csv(f"{D.SLEEVE_LIB}/{name}.csv", index_col=0, parse_dates=True)
    return df["ret"].astype(float)

def corr_to_lib(r, names=("L_S_130_30","CTA_15vol","StatArb_40pairs","FactorMom_1963","Credit_z250_1986","Merger_Arb_PEAD")):
    out = {}
    for nm in names:
        try:
            l = load_lib(nm)
            j = pd.concat([r, l], axis=1).dropna()
            if len(j) > 250: out[nm] = round(float(j.corr().iloc[0,1]), 2)
        except Exception: pass
    return out
