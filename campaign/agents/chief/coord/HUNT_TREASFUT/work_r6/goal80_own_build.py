"""HUNT_TREASFUT R6 — MY OWN independent GOAL80 COORD_FINAL builder.

Written from the documented recipe (AUDIT_CHAMP2 R5c FINDINGS + the test docstring
in test_audit_champ2_round5b.py) — NOT an import of coord_goal100_v2.py and NOT a
copy of AUDIT_CHAMP2 code. Structure mirrors the audited construction so a GREEN
byte-repro means the CONSTRUCTION is confirmed, not that code was copied.

Recipe (as documented):
  14 sleeves, min_hist>=750. RAW-FIRST per-sleeve vt: v_i = r_i * (0.10/vol_i).clip(<=8),
  vol_i = rolling60 std shift(1) * sqrt(252), computed on each sleeve's OWN index
  (no NaN alignment), scale 0 where vol NaN. Weights W_i = scale_i / sum_j scale_j
  (sum-1). raw = mean_i v_i (EW). raw = raw[index >= 2008-09-01].
  Global vt @ TGT=0.08: b = raw * (0.08 / vol_raw).clip(<=8).
  Turnover tw_t = sum_i |W_i,t - W_i,t-1| * 0.5 (HALF-turn).
  DD-throttle: sc_t = 0.5 if tdd_t < -0.04 else 1.0, tdd = eq.shift(1)/rollmax126.shift(1)-1
  on (1+b.fillna(0)).cumprod(). b *= sc. Throttle turnover dsc = |diff(sc)| * 0.5.
  net_t = b_t - (tw + dsc) * 6bps/1e4. Start 2008-09-01, dropna.
  dualmom pinned to the b268e52~1 pre-costfix blob (byte-identical to AUDIT_CHAMP2's
  dualmom_pre_costfix.csv, sha256 7132a167f70f3a6c...).
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", ".."))

POOL = {
    "H21_f5": "tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv",
    "H21_br": "tools/quant/reports/xgb_horizons/h21_breadth_gate_daily.csv",
    "A5r7": "campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
    "a6r7": "campaign/agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv",
    "A1inf": "campaign/agents/A1_trend_cta/sleeves/A1_infl_breadth_mom.csv",
    "QAxasts": "campaign/agents/A3_xs_quality/sleeves/QA_xasts_tsmom189.csv",
    "A5r2": "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "A1credit": "campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
    "XGB1y": "campaign/results/sleeve_library/XGB1y_deploy.csv",
    "dualmom": os.path.relpath(
        os.path.join(HERE, "dualmom_pre_myblob.csv"), WT),
    "carryv2": "campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv",
    "A5r4": "campaign/agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv",
    "brwt": "campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv",
    "B3momhml": "campaign/agents/B3_antiregime/ref_momhml_composite.csv",
}

COST = 6 / 10000          # 6bps one-side, HALF-turn convention (pre-costfix vintage)
START = "2008-09-01"
TGT_PER = 0.10            # per-sleeve vol target
TGT_GLOB = 0.08           # global vol target (the artifact's documented vt)
VT_CAP = 8.0
DD_THR = 0.04             # drawdown throttle trigger
DD_FR = 0.5               # throttle fraction
DD_WIN = 126


def load(rel):
    df = pd.read_csv(os.path.join(WT, rel), index_col=0)
    df.index = pd.to_datetime(df.index)
    col = "ret" if "ret" in df.columns else df.columns[0]
    return df[col].astype(float)


def vt_series(r, tgt):
    """Raw-first vt on a Series' OWN index (no cross-sleeve NaN alignment)."""
    vol = r.rolling(60).std().shift(1) * np.sqrt(252)
    scale = (tgt / vol).clip(upper=VT_CAP)
    scale[vol.isna()] = 0.0
    return r * scale.fillna(0.0), scale


def build_all(pool_override=None, min_hist=750):
    pool = dict(POOL)
    for k, v in (pool_override or {}).items():
        pool[k] = v
    D = {}
    for n in pool:
        r = load(pool[n])
        if len(r) >= min_hist:
            D[n] = r
    V = pd.DataFrame({n: vt_series(D[n], TGT_PER)[0] for n in D})
    S = pd.DataFrame({n: vt_series(D[n], TGT_PER)[1] for n in D})
    W = S.div(S.sum(axis=1), axis=0).fillna(0)
    raw = V.mean(axis=1)
    raw = raw[raw.index >= START]
    tw = (W - W.shift(1)).abs().sum(axis=1) * 0.5
    b, s_glob = vt_series(raw, TGT_GLOB)
    eq = (1 + b.fillna(0)).cumprod()
    rm = eq.rolling(DD_WIN).max().shift(1)
    tdd = eq.shift(1) / rm - 1
    sc = pd.Series(np.where(tdd < -DD_THR, DD_FR, 1.0), index=b.index)
    b = b * sc
    dsc = sc.diff().abs() * 0.5
    tot = tw.reindex(b.index).fillna(0) + dsc.fillna(0)
    net = (b - tot * COST).dropna()
    # gross multiplier actually carried: global-vt scale x throttle
    gross_vt = (s_glob * sc).reindex(net.index)
    return net, {"gross_vt": gross_vt, "weights": W, "throttle": sc}


if __name__ == "__main__":
    net, aux = build_all()
    s = net.describe()
    print(f"n={len(net)} span {net.index[0].date()}..{net.index[-1].date()}")
    print(net.head(3))
