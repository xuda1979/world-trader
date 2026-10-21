"""CAMP_COST R2 — costfix emission: full |dW| @ 6.4bps for the 4 byte-exact-verified offenders.
For each: (1) byte-recon committed CSV with ORIGINAL convention (proof of exactness),
(2) flip ONLY the cost line, (3) emit in place, (4) report before/after stats.
brwt10/7/5 NOT touched (no byte-level generator; flagged to coordinator).
Run: python3 costfix_emit.py            (recon-check + emit costfix)
     python3 costfix_emit.py --check    (recon-check only, no writes)
"""
import sys, warnings, hashlib
warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_BASIS2/scratch")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
import lib as L                                    # HUNT_BASIS2 (diescrack)
from campaign.harness import data as D             # closes/ff_factors/month_ends via engine
from campaign.agents.B2_highfreq.gates import vol_target
from engine import month_ends, strategy_ret        # A3_xs_quality engine (dualmom)

ROOT = "/Users/daxu/software/world-trader"
BPS_NEW = 6.4
SH = f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def stats(r):
    r = r.dropna()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    eq = (1 + r).cumprod()
    return dict(n=len(r), ann=((eq.iloc[-1]) ** (252 / len(r)) - 1) * 100,
                sr=r.mean() / r.std() * np.sqrt(252),
                mdd=(eq / eq.cummax() - 1).min() * 100, negy=int((yr < 0).sum()),
                worst=yr.min() * 100)


def rep(tag, s):
    print(f"    {tag}: n={s['n']} ann={s['ann']:.3f}% SR={s['sr']:.4f} "
          f"mdd={s['mdd']:.2f}% negy={s['negy']} worst={s['worst']:.2f}%")


def compare(r, cpath):
    C = pd.read_csv(cpath, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    j = pd.concat([r.rename("a"), C.rename("b")], axis=1, join="inner").dropna()
    d = float((j.a - j.b).abs().max()) if len(j) else float("nan")
    return d, len(j), len(C)


def emit(r, path):
    pd.DataFrame({"ret": r.astype(float).values}, index=r.index).to_csv(path)


# ---------------------------------------------------------------- diescrack
def diescrack(full_dw, bps):
    dj = L.fred("DJFUELUSGULF", src=f"{ROOT}/tools/quant/data/newdata")
    wt = L.fred("wti_full")
    sp = (np.log(dj * 42.0) - np.log(wt)).dropna()
    sp = sp[sp.index >= "2008-01-01"]
    m = sp.rolling(40, min_periods=40).mean()
    sd = sp.rolling(40, min_periods=40).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -2.0] = 1.0
    pos[z > 2.0] = -1.0
    ret = sp.diff().shift(-1)
    gr = (pos * ret).dropna()
    factor = 1.0 if full_dw else 0.5
    tup = (pos.diff().abs() * factor).reindex(gr.index).fillna(0.0)
    base = gr - tup * bps / 1e4
    pi = pos.reindex(base.index).fillna(0.0)
    # committed borrow convention (byte-verified): flat 0.005/252 on any day the book is
    # nonzero OR was nonzero yesterday (exit day still pays one day of borrow)
    bmask = ((pi != 0) | (pi.shift(1).fillna(0) != 0)).astype(float)
    sc = (0.08 / (base.expanding(60).std() * np.sqrt(252))).clip(upper=3.0)
    out = (base * sc).fillna(0.0) - bmask * 0.005 / 252
    return out.dropna()


# ---------------------------------------------------------------- dualmom
def dualmom(full_dw, bps):
    WIN, BAND, FRAC = 200, 0.03, 1 / 3
    px = D.closes()
    rets = px.pct_change()
    MES = [d for d in month_ends(rets) if d in px.index]
    sig = px.shift(21) / px.shift(252) - 1.0
    ff = D.ff_factors()
    mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
    ma = mkt.rolling(WIN, min_periods=WIN).mean()
    g = pd.Series(np.where(mkt > ma * (1 + BAND), 1.0,
                  np.where(mkt < ma * (1 - BAND), 0.0, np.nan)), index=mkt.index)
    g = g.reindex(px.index).ffill().fillna(0.0)
    W = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
    for t in MES:
        if t not in sig.index or g.loc[t] <= 0:
            continue
        row = sig.loc[t].dropna()
        if len(row) < 10:
            continue
        row = row.sort_values()
        nl = max(int(np.floor(len(row) * FRAC)), 1)
        for s in row.index[-nl:]:
            W.loc[t, s] = 1.0 / nl
    idx = rets.index
    w = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    prev = pd.Series(0.0, index=rets.columns)
    turn = pd.Series(0.0, index=idx)
    pos_of = {d: idx.get_loc(d) for d in MES}
    factor = 1.0 if full_dw else 0.5
    for i, t in enumerate(MES):
        neww = W.loc[t]
        p = pos_of[t]
        if p + 1 < len(idx):
            turn.iloc[p + 1] = factor * (neww - prev).abs().sum()
            nxt_p = pos_of[MES[i + 1]] + 1 if i + 1 < len(MES) else len(idx)
            w.iloc[p + 1: nxt_p] = neww.values
            prev = neww
    net = (w * rets.fillna(0.0)).sum(axis=1) - turn * bps / 1e4
    nz = w.abs().sum(axis=1)
    return strategy_ret(net, nz[nz > 0].index[0])


# ---------------------------------------------------------------- brwt15
def brwt15(full_dw, bps):
    BR = D.fred("brent").dropna()
    WT = D.fred("wti_full").dropna()
    sp = (np.log(BR) - np.log(WT)).dropna()
    z = (sp - sp.rolling(15, min_periods=15).mean()) / \
        sp.rolling(15, min_periods=15).std().replace(0, np.nan)
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -1.5] = 1.0
    pos[z > 1.5] = -1.0
    factor = 1.0 if full_dw else 0.5
    net = (pos * sp.diff().shift(-1) - (pos.diff().abs() * factor) * bps / 1e4).dropna()
    sc, _ = vol_target(net)
    return sc.dropna()


# ---------------------------------------------------------------- QAxasts
def qaxasts(full_dw, bps):
    from r7_idea5_breadth import panel, RET_PAN
    from r6lib import wback_rb_core
    from r7lib import wed_rbd
    MAW = 189
    R5 = RET_PAN.drop(columns=["CASH"])
    s = np.sign(panel - panel.rolling(MAW, min_periods=MAW // 2).mean()).fillna(0) * 0.2
    net, _ = wback_rb_core(s, R5, wed_rbd(panel.index), full_dw=full_dw, bps=bps)
    sc, _ = vol_target(net.dropna(), 0.10)
    return sc.dropna()


TARGETS = {
    "diescrack": ("campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv", diescrack),
    "dualmom":   ("campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv", dualmom),
    "brwt15":    ("campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv", brwt15),
    "QAxasts":   ("campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv", qaxasts),
}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "emit"
    force = "--force" in sys.argv
    ok = True
    for name, (rel, fn) in TARGETS.items():
        path = f"{ROOT}/{rel}"
        arch = f"{SH}/{name}__prefix.csv"
        # CANONICAL emission index = the committed (pre-fix) file's index. Data vintages
        # move; the costfix must change ONLY the cost stream, never the date range.
        arch_idx = pd.read_csv(arch, index_col=0, parse_dates=True).index
        print(f"== {name} ({rel})")
        r_new = fn(full_dw=True, bps=BPS_NEW).reindex(arch_idx)
        dn, ni, nc = compare(r_new, path)
        if dn < 1e-12 and not force:
            print(f"  already costfix (new-conv recon maxdev={dn:.1e}, n={ni}) -> nothing to do")
            continue
        r_old = fn(full_dw=False, bps=6.0)
        d, ni, nc = compare(r_old, arch)
        exact = d < 1e-12 and ni == len(arch_idx)
        print(f"  recon(orig conv): n_inner={ni}/{len(arch_idx)} maxdev={d:.3e} "
              f"{'BYTE-EXACT' if exact else 'MISMATCH -> SKIP'}")
        if not exact:
            ok = False
            continue
        so, sn = stats(r_old.reindex(arch_idx)), stats(r_new)
        rep("before", so)
        rep("after ", sn)
        if mode == "emit":
            emit(r_new, path)
            d2, _, _ = compare(r_new, path)
            print(f"  EMITTED n={len(r_new)} -> sha {sha(path)}  (emit-vs-candidate maxdev {d2:.1e})")
    print("DONE" if ok else "PARTIAL (mismatched sleeves skipped, nothing written for them)")


if __name__ == "__main__":
    main()
