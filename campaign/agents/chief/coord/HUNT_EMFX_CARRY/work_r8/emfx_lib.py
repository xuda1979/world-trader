"""HUNT_EMFX_CARRY R8 — EM FX carry / momentum / cross-section on tools/quant/data/em_rates/.

PRE-REGISTERED candidate set (declared before any performance number):
  C1 BRL_CARRY_L      long BRL vs USD when carry>0, VT10 trailing, gross<=1
  C2 BRL_CARRY_MED    C1 gated on carry level > expanding median (regime filter)
  C3 TSMOM_252       12m TS momentum, 4 USD pairs, long/short, EW, VT10
  C4 TSMOM_126       6m variant
  C5 BRL_MOM_252     BRL-only 12m momentum (isolates single-ccy question)
  C6 XS_252          cross-sectional long strongest / short weakest, 4 ccy (pre-reg as under-powered)
  C7 COMBO           signal = C1 carry sign + C3 momentum sign, EW

Data honesty: carry differential vs USD is expressible for BRL ONLY (selic vs DFF).
No CZK/PLN/PEN policy rate exists on disk (verified by exhaustive sweep + em_rates_dl SERIES).
C3-C7 therefore book SPOT-ONLY (no accrual) for CZK/PLN/PEN -> disclosed, not hidden.

Costs: 6.4e-4 on FULL |dW| one-side + 0.5%/yr borrow on short notional + 4.5%/yr margin on max(gross-1,0).
T+1: effective weight at t = signal_{t-1} * volscale_{t-1} (vol through t-2). Strictly causal.
"""
import os, sys, json, hashlib
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
CAMP = os.path.join(ROOT, "campaign")
if CAMP not in sys.path:
    sys.path.insert(0, CAMP)
from bt import gates as G
from bt.engine import vol_target_scale, cap_leverage
from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years
from bt.leakcheck import leak_probe, gates_flag

WORK = os.path.dirname(os.path.abspath(__file__))
EM   = os.path.join(ROOT, "tools/quant/data/em_rates")
FR   = os.path.join(ROOT, "tools/quant/data/more_fred")
CHAMP_CSV = os.path.join(ROOT, "campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
CHAMP_SHA = "8d7e711e6d05a2b1"
COST = 6.4e-4
BORROW = 0.005
MARGIN = 0.045
ANN = 252.0

CCY = ["BRL", "CZK", "PEN", "PLN"]
PAIR = {"BRL": "brazil_usdbrl", "CZK": "czech_usdczk",
        "PEN": "peru_usdpen", "PLN": "poland_usdpln"}


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()[:16]


def load_series(path):
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    return pd.to_numeric(df["value"], errors="coerce")


def champion():
    sha = sha16(CHAMP_CSV)
    if not sha.startswith(CHAMP_SHA):
        raise RuntimeError("champion sha drift %s != %s" % (sha, CHAMP_SHA))
    return pd.read_csv(CHAMP_CSV, parse_dates=["date"]).set_index("date")["ret"]


def panel(mask_stale=True):
    """USDXXX prices on the champion calendar.

    ffill carries the last close across LOCAL holidays (correct: no new price, 0 spot
    return that day). It must NOT carry a DEAD series forward: poland_usdpln.csv stops
    2025-12-31, and a naive ffill silently freezes PLN at 3.6016 for all of 2026-01..
    2026-08 (8 months of fake 0%-vol flat prices, which then blows the vol-target scale
    to its cap). mask_stale=True sets every date after a series' LAST REAL OBSERVATION
    back to NaN so the position is forced flat there."""
    ch = champion()
    px = {}
    for c in CCY:
        s = load_series(os.path.join(EM, PAIR[c] + ".csv")).dropna()
        last = s.index.max()
        f = s.reindex(ch.index.union(s.index)).ffill().reindex(ch.index)
        if mask_stale:
            f[f.index > last] = np.nan
        px[c] = f
    return pd.DataFrame(px, index=ch.index)


def carry_brl(idx):
    """Daily carry of long BRL funded in USD.
    selic = BCB SGS-11 daily effective rate in PERCENT PER DAY (unit-verified against
    published anchors: 2016-01 -> (1+v/100)^252-1 = 14.15%/yr vs effective ~14.15%).
    dff = FRED DFF annualized percent -> daily = val/100/252."""
    sel = load_series(os.path.join(EM, "brazil_selic.csv"))
    dff = load_series(os.path.join(FR, "DFF.csv"))
    sel = sel.reindex(idx.union(sel.index)).ffill().reindex(idx)
    dff = dff.reindex(idx.union(dff.index)).ffill().reindex(idx)
    return sel / 100.0 - (dff / 100.0) / ANN


def total_perunit(px, carry):
    """Per-unit long-EM-currency return: spot (long EM = -dlog USDXXX) + carry accrual."""
    lr = -np.log(px).diff()
    lr["BRL"] = lr["BRL"] + carry
    return lr


def effective_weights(sig, per_unit, target=0.10, cap=3.0, gross_max=1.0):
    """sig_t uses info <= t. Returns EFFECTIVE weights indexed t (used for r_t).
    effective_t = sig_{t-1} * scale_t ; scale_t from vol through t-1 (engine already shifts).
    Gross capped (peg regimes drive vol -> 0 -> scale to the cap)."""
    sig = sig.fillna(0.0)
    g = sig.abs().sum(axis=1).replace(0.0, np.nan)
    unit = sig.div(g, axis=0).fillna(0.0)
    port = (unit.shift(1) * per_unit).sum(axis=1)
    sc = vol_target_scale(port.to_frame("r"), target=target, window=60, cap=cap)["r"]
    w = sig.mul(sc, axis=0).shift(1).fillna(0.0)
    return cap_leverage(w, gross_max)


def net_book(w, per_unit):
    """Fully-costed net book on the same index. w are EFFECTIVE weights."""
    gross_ret = (w * per_unit).sum(axis=1)
    to = w.fillna(0.0).diff().abs().sum(axis=1)
    if len(w):
        to.iloc[0] = w.fillna(0.0).iloc[0].abs().sum()
    cost = to * COST
    shorts = (-w.clip(upper=0.0)).sum(axis=1)
    borrow = shorts * BORROW / ANN
    g = w.abs().sum(axis=1)
    margin = (g - 1.0).clip(lower=0.0) * MARGIN / ANN
    return gross_ret - cost - borrow - margin, cost, to, g


def stats(x):
    x = x.dropna()
    if len(x) == 0:
        return {}
    neg, worst = neg_years(x)
    k = len(x) // 2
    return dict(n=int(len(x)), sr=round(float(sharpe_d(x)), 4),
                ann=round(float(ann_geo(x)), 4), mdd=round(float(max_dd(x)), 4),
                vol=round(float(x.std(ddof=1) * np.sqrt(ANN)), 4),
                neg_years=int(neg), worst_year=round(float(worst), 4),
                h1=round(float(sharpe_d(x.iloc[:k])), 4),
                h2=round(float(sharpe_d(x.iloc[k:])), 4))
