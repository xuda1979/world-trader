"""E3_volregime shared lib: vol-event engines. T+1 execution, 6bps/side, vt10 trailing-only."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader")
from campaign.harness import data as D
from campaign.agents.B2_highfreq.gates import full_stats, halves_sr

COST = 6.0 / 1e4

def spx_ret():
    px = D.closes()["SPY"].sort_index()
    return px.pct_change()

def fred_s(name):
    s = D.fred(name).sort_index()
    return s[~s.index.duplicated(keep="last")]

def blend_rets():
    out = {}
    for nm, p in [("COORD", f"{D.ROOT}/campaign/results/COORD_FINAL_daily.csv"),
                  ("CHAMP20Y", f"{D.ROOT}/campaign/results/GOAL100_CHAMPION20Y_BALANCED_daily.csv")]:
        df = pd.read_csv(p, index_col=0, parse_dates=True)
        out[nm] = df.iloc[:, 0].astype(float)
    return out

def exec_net(pos, asset_ret, cost=COST):
    """pos decided at close t using data<=t -> PnL on t+1 (shift 1). T+1 honest."""
    p = pos.shift(1).fillna(0.0)
    r = asset_ret.reindex(p.index).fillna(0.0)
    to = p.diff().abs().fillna(p.abs())
    return p * r - to * cost

def vt_scale(net, target=0.10, minlen=60, clip=3.0):
    """Expanding trailing vol scale, shift(1) so only data<=t used."""
    rv = net.expanding(minlen).std() * np.sqrt(252)
    sc = (target / rv).clip(upper=clip).fillna(0.0).shift(1)
    return sc

def sr(r):
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(252)) if len(r) > 2 and r.std() > 0 else 0.0

def scramble_pval_pos(pos, asset_ret, n=200, seed=0):
    """Honest: permute POSITIONS vs real date-aligned asset returns, costs reapplied."""
    rng = np.random.default_rng(seed)
    p0 = pos.shift(1).fillna(0.0)
    idx = p0.index
    rr = asset_ret.reindex(idx).fillna(0.0).values
    pv = p0.values
    def net_of(v):
        p = pd.Series(v, index=idx)
        to = p.diff().abs().fillna(p.abs())
        return p.values * rr - to.values * COST
    real = sr(pd.Series(net_of(pv), index=idx).dropna())
    cnt = 0
    for _ in range(n):
        if sr(pd.Series(net_of(rng.permutation(pv)), index=idx).dropna()) >= real:
            cnt += 1
    return cnt / n

def corr_to_blends(net):
    out = {}
    for nm, b in blend_rets().items():
        j = pd.concat([net, b], axis=1).dropna()
        if len(j) > 250:
            out[nm] = float(j.corr().iloc[0, 1])
    return out

def full_gate(name, net, pos=None, asset_ret=None, peak_sr=None, chosen_sr=None,
              min_sr=1.0, verbose=True):
    net = net.dropna()
    s = full_stats(net)
    h1, h2 = halves_sr(net)
    pv = (scramble_pval_pos(pos, asset_ret) if pos is not None
          else np.nan)
    cor = corr_to_blends(net)
    maxc = max(abs(v) for v in cor.values()) if cor else 9.9
    g = {
      "a_SR>=1.0": s["sr"] >= min_sr,
      "b_plateau": True if peak_sr is None else (chosen_sr >= 0.8 * peak_sr),
      "c_halves>=0.5": (h1 >= 0.5) and (h2 >= 0.5),
      "d_yearly": (s["negy"] <= 2) and (s["worst"] > -5.0),
      "e_scramble_p<=.05": (pv <= 0.05) if pos is not None else False,
      "f_corr<0.15": maxc < 0.15,
      "f2_corr<0.35": maxc < 0.35,
    }
    ok = g["a_SR>=1.0"] and g["b_plateau"] and g["c_halves>=0.5"] and g["d_yearly"] and g["e_scramble_p<=.05"] and g["f2_corr<0.35"]
    if verbose:
        print(f"[{name}] n={s['years']}y SR={s['sr']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% "
              f"mdd={s['mdd']:.1f}% negy={s['negy']}/{s['years']} worst={s['worst']:.1f}% "
              f"H1={h1:.2f} H2={h2:.2f} scram_p={pv:.3f} corr={ {k: round(v,3) for k,v in cor.items()} }")
        print(f"   yearly: {s['yearly']}")
        print(f"   gates: { {k: bool(v) for k,v in g.items()} } ALL={ok}")
    return dict(name=name, s=s, H1=h1, H2=h2, scram_p=pv, corr=cor, gates=g, all_pass=ok)
