"""HUNT_COT2 round 3 (a), part 3: rebuild the remaining 3 HUNT_CMDT2 round-2 sleeves.

  CMDT2_CotGatedMom_9m_k2_thr0.2     (their headline round-2 number, SR 0.245)
  CMDT2_CotMom_9m_k2_UNGATED_ablation
  CMDT2_UNGshortdecay_volscaled      (EXT-F: constant short UNG, custom 60d vol scale)

Same my-own-engine conventions as part 2. The COT gate chain: raw report (Tue as-of) ->
+3d availability stamp -> daily ffill -> expanding percentile (min_periods=26) of the
report's own history -> crowded when |pctl| > 0.8 -> weight masked to 0 that day.
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
SLEEVES = f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves"
ANN, COST_BPS, BORROW = 252, 6.4, 0.005

sys.path.insert(0, f"{ROOT}/campaign/scripts")   # ONLY to reuse part-2's net_book; no CMDT2 import
from HUNT_COT2_rebuild_cmdt2 import net_book, load_close  # noqa: E402

COT_MAP = {"crude_wti_nymex": "USO", "nat_gas_nymex": "UNG", "gold": "GLD", "silver": "SLV",
           "copper": "CPER", "corn": "CORN", "soybeans": "SOYB", "wheat_srw": "WEAT",
           "sugar_no11": "CANE"}


def cot_gate(fam, thr=0.2, end=None):
    df = pd.read_csv(f"{ROOT}/tools/quant/data/more_cot/{fam}_cot.csv", parse_dates=["date"])
    s = df.set_index("date")["net_noncomm_pct_oi"].astype(float).sort_index()
    s.index = s.index + pd.Timedelta(days=3)               # Tue as-of -> Fri availability
    if end is not None:
        s = s.loc[:end]
    pctl = s.expanding(min_periods=26).apply(lambda a: (a[-1] >= a).mean(), raw=True)
    gate = (pctl.abs() <= (1.0 - thr)).astype(float)
    gate[pctl.isna()] = np.nan                              # warmup -> unknown -> blocked
    return gate


def run_gated_mom(px, R, months=9, topk=2, hold=3, thr=0.2, gross=2.0):
    mom = px.shift(0) / px.shift(months * 21) - 1.0
    idx = px.index
    n = px.shape[1]
    gdf = pd.DataFrame({COT_MAP[f]: cot_gate(f, thr=thr).reindex(idx).ffill() for f in COT_MAP})
    gdf = gdf[list(px.columns)]
    per = pd.Series(idx, index=idx).groupby(idx.to_period("M")).first()
    ms = sorted(set(idx.searchsorted(per.values)))
    mseq = {p: j for j, p in enumerate(sorted({idx[i].to_period("M") for i in ms}))}
    rebset = {i for i in ms if mseq[idx[i].to_period("M")] % hold == 0}
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    prev = None
    for i in range(len(idx)):
        if i in rebset and i > 0:
            m = mom.iloc[i - 1]
            if m.notna().sum() >= max(2, int(round(0.8 * n))):
                r = m.rank(ascending=False, na_option="keep")
                w = pd.Series(0.0, index=px.columns)
                w[r <= topk] = gross / (2 * topk)
                w[r > n - topk] = -gross / (2 * topk)
                prev = w
        if prev is not None:
            W.iloc[i] = (prev * gdf.iloc[i].reindex(px.columns).fillna(0.0)).values
    return net_book(W, R) + (W,)


def run_ung_shortdecay():
    px = load_close("UNG").to_frame("UNG")
    R = px.pct_change()
    vol = px["UNG"].pct_change().rolling(60, min_periods=40).std() * np.sqrt(ANN)
    scale = (0.10 / vol.replace(0, np.nan)).clip(upper=3.0).shift(1)
    scale = scale.where(vol.shift(1).notna(), 0.0).fillna(0.0)
    W = pd.DataFrame({"UNG": -scale}, index=px.index)
    return net_book(W, R) + (R,)      # their net_of default vt=True also stacks here


def main():
    px = pd.concat({s: load_close(s) for s in sorted(COT_MAP.values())}, axis=1).sort_index()
    R = px.pct_change()
    builds = {
        "CMDT2_CotGatedMom_9m_k2_thr0.2": lambda: run_gated_mom(px, R, months=9, topk=2, thr=0.2),
        "CMDT2_CotMom_9m_k2_UNGATED_ablation": lambda: run_gated_mom(px, R, months=9, topk=2, thr=0.0),
        "CMDT2_UNGshortdecay_volscaled": lambda: run_ung_shortdecay(),
    }
    out_rows = []
    for name, fn in builds.items():
        net, W, _ = fn()
        their = pd.read_csv(f"{SLEEVES}/{name}.csv", index_col=0, parse_dates=True).iloc[:, 0]
        j = pd.concat({"mine": net, "theirs": their}, axis=1, sort=True).dropna()
        d = (j["mine"] - j["theirs"]).abs()
        sr = lambda s: s.mean() / s.std(ddof=1) * np.sqrt(ANN)
        missing = len(their) - len(j)
        ok = (j["mine"].corr(j["theirs"]) > 0.9999 and d.max() < 5e-4 and missing == 0)
        out_rows.append(dict(name=name, n_theirs=len(their), n_overlap=len(j),
                             corr=j["mine"].corr(j["theirs"]), max_abs_diff=d.max(),
                             mean_abs_diff_bp=d.mean() * 1e4,
                             sr_mine=sr(j["mine"]), sr_theirs=sr(j["theirs"])))
        print(f"[{name}] n_theirs={len(their)} overlap={len(j)} mine_only={len(net)-len(j)} "
              f"corr={j['mine'].corr(j['theirs']):.6f} max|d|={d.max():.2e} "
              f"mean|d|={d.mean()*1e4:.3f}bp SR mine={sr(j['mine']):.3f} "
              f"theirs={sr(j['theirs']):.3f} -> {'MATCH' if ok else 'MISMATCH'}")
    df = pd.DataFrame(out_rows)
    out = f"{ROOT}/campaign/agents/chief/coord/HUNT_COT2/rebuild_cmdt2_r3_p2_results.csv"
    df.to_csv(out, index=False)
    n_ok = int(((df["corr"] > 0.9999) & (df["max_abs_diff"] < 5e-4)).sum()) if len(df) else 0
    print(f"\nSUMMARY: {n_ok}/{len(df)} reproduce (corr>0.9999, max|d|<5e-4)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
