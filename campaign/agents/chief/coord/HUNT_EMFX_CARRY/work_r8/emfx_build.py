"""HUNT_EMFX_CARRY R8 — build the pre-registered candidate set + full V2 battery.

Run: python3 emfx_build.py     (from this directory; writes emfx_results.json)
"""
import os, sys, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, os.path.join(ROOT, "campaign"))

import emfx_lib as L
from bt import gates as G
from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years
from bt.leakcheck import leak_probe, gates_flag

ANN = 252.0
CH = L.champion()
PX = L.panel()
CARRY = L.carry_brl(CH.index)
PU = L.total_perunit(PX, CARRY).fillna(0.0)
AVAIL = PX.notna()


def zsign(x):
    return np.sign(x.fillna(0.0))


def m(sig, name, target=0.10):
    sig = sig.where(AVAIL, 0.0).fillna(0.0)
    w = L.effective_weights(sig, PU, target=target)
    net, cost, to, g = L.net_book(w, PU)
    return dict(name=name, sig=sig, w=w, net=net, cost=cost, to=to, gross=g)


# ---------------------------------------------------------------- signals (info <= t)
LR = np.log(PX)

S = {}
# C1 long BRL carry (carry differential vs USD, always > 0 in-sample)
S["C1_BRL_CARRY_L"] = pd.DataFrame({"BRL": np.where(CARRY > 0, 1.0, 0.0)}, index=CH.index)
# C2 carry only when the carry LEVEL is above its own expanding median (regime filter)
med = CARRY.expanding(min_periods=252).median()
S["C2_BRL_CARRY_MED"] = pd.DataFrame({"BRL": np.where(CARRY > med, 1.0, 0.0)}, index=CH.index)
# C3/C4 TS momentum 12m / 6m, long/short, EW across available ccy
for nm, lb in [("C3_TSMOM_252", 252), ("C4_TSMOM_126", 126)]:
    mom = LR - LR.shift(lb)
    S[nm] = zsign(mom)
# C5 BRL-only 12m momentum
mom252 = LR - LR.shift(252)
S["C5_BRL_MOM_252"] = pd.DataFrame({"BRL": zsign(mom252["BRL"])}, index=CH.index)
# C6 cross-sectional 12m: long strongest / short weakest (pre-registered as under-powered)
rk = mom252.where(AVAIL).rank(axis=1, ascending=False)
xs = pd.DataFrame(0.0, index=CH.index, columns=L.CCY)
xs = xs.mask(rk.eq(1), 1.0).mask(rk.eq(len(L.CCY)), -1.0)
xs = xs.where(rk.notna().sum(axis=1).ge(3), 0.0)
S["C6_XS_252"] = xs
# C7 combo: carry sign (BRL) + momentum sign (all)
cb = pd.DataFrame({"BRL": np.where(CARRY > 0, 1.0, 0.0)}, index=CH.index).reindex(columns=L.CCY).fillna(0.0)
S["C7_COMBO"] = (cb + zsign(mom252)).fillna(0.0)

CAND = {}
for k, v in S.items():
    CAND[k] = m(v, k)

# ---------------------------------------------------------------- benchmarks (V2 7c)
def load_bench():
    spy = pd.read_csv(os.path.join(ROOT, "tools/quant/data/twelvedata/SPY.csv"),
                      parse_dates=["date"]).set_index("date")["close"].sort_index()
    ief = pd.read_csv(os.path.join(ROOT, "tools/quant/data/more_etf/IEF.csv"),
                      parse_dates=["date"]).set_index("date")["close"].sort_index()
    cta = pd.read_csv(os.path.join(ROOT, "campaign/results/sleeve_library/CTA_15vol.csv"),
                      parse_dates=["date"]).set_index("date")["ret"]
    return spy.pct_change().rename("ret"), ief.pct_change().rename("ret"), cta

SPY, IEF, CTA = load_bench()

# ---------------------------------------------------------------- evaluation
def era(x, lo, hi):
    return x.loc[lo:hi]


def blend_ladder(net_s, w_grid=(0.85, 0.90, 0.925, 0.95, 0.975)):
    out = {}
    cs = L.stats(CH)
    for wc in w_grid:
        b = wc * CH + (1 - wc) * net_s
        st = L.stats(b)
        out["%g" % wc] = dict(w_sleeve=round(1 - wc, 4), **st,
                              dAnn=round(st["ann"] - cs["ann"], 4),
                              dSR=round(st["sr"] - cs["sr"], 4),
                              dMDD=round(st["mdd"] - cs["mdd"], 4),
                              dH1=round(st["h1"] - cs["h1"], 4),
                              dH2=round(st["h2"] - cs["h2"], 4))
    return out


def battery(name, c):
    net, w, sig = c["net"], c["w"], c["sig"]
    gross_units = w.abs().sum(axis=1)
    r_pu = (net / gross_units.replace(0.0, np.nan)).fillna(0.0)
    g = G.run(r_pu, ref=CH, sig=gross_units.values, leak_check=True,
              beats_passive=True, spy=SPY, ief=IEF, cta=CTA)
    signed = w.sum(axis=1)
    lp = leak_probe(signed.values, PU.sum(axis=1).values)
    return g, lp


def truncation_probe(name, c, cut=0.7):
    """Causality: rebuild on data truncated at `cut`; the overlap must be byte-identical."""
    n = len(CH)
    k = int(n * cut)
    idx = CH.index[:k]
    sig = c["sig"].iloc[:k]
    pu = PU.iloc[:k]
    w2 = L.effective_weights(sig, pu, target=0.10)
    net2, _, _, _ = L.net_book(w2, pu)
    a = c["net"].iloc[:k]
    d = float(np.nanmax(np.abs(a.values - net2.values)))
    return d


RESULT = {}
for name, c in CAND.items():
    g, lp = battery(name, c)
    st = L.stats(c["net"])
    st09 = L.stats(c["net"].loc[:"2009-12-31"])
    st10 = L.stats(c["net"].loc["2010-01-01":])
    gross = float(c["gross"].max())
    gross_mean = float(c["gross"].mean())
    frac_cap = float((c["gross"] > 0.999).mean())
    # ANNUAL cost in bp: mean DAILY cost (fraction) * 252 * 1e4
    cost_bp = float(c["cost"].mean() * ANN * 1e4)
    to = float(c["to"].mean())
    corr = G.corr_to(CH, c["net"])
    RESULT[name] = dict(
        stats=st, pre2010=st09, post2010=st10,
        ann_cost_bp_yr=round(cost_bp, 3), turns_per_yr=round(to * ANN, 2),
        gross_max=round(gross, 4), gross_mean=round(gross_mean, 4),
        gross_frac_at_cap=round(frac_cap, 4), corr_champ=round(float(corr), 4),
        gate=dict(pass_=bool(g["pass"]), sr=g["sr"], sr_ok=g["sr_ok"],
                  h1=g["h1"], h2=g["h2"], halves_ok=g["halves_ok"],
                  neg_years=g["neg_years"], worst=g["worst"], neg_ok=g["neg_ok"],
                  corr=g["corr"], corr_ok=g["corr_ok"], scr_p=g["scr_p"], scr_ok=g["scr_ok"],
                  leak_ok=g["leak_ok"], leak_same_period_corr=g["leak"]["same_period_corr"],
                  leak_flag=g["leak"]["leak"],
                  bp_ok=g["beats_passive"]["beats_passive_ok"],
                  bp_best=g["beats_passive"].get("best_passive_sr"),
                  bp_name=g["beats_passive"].get("best_passive_name"),
                  bp_detail=g["beats_passive"].get("detail")),
        leak_probe_signed=dict(leak=lp["leak"], same_period_corr=round(lp["same_period_corr"], 4),
                               same_period_p=round(lp["same_period_p"], 4)),
        truncation_max_abs_dev=truncation_probe(name, c),
        blend=blend_ladder(c["net"]))
    print("== %-18s SR %6.3f ann %7.2f%% MDD %7.2f%% negy %2d corr %+.3f pass=%s  "
          "cost %.1fbp/yr gross %.2f" % (
              name, st["sr"], st["ann"] * 100, st["mdd"] * 100, st["neg_years"],
              corr, g["pass"], cost_bp, gross))

# save net series for reuse
os.makedirs(os.path.join(HERE, "nets"), exist_ok=True)
for name, c in CAND.items():
    c["net"].rename("ret").to_csv(os.path.join(HERE, "nets", name + ".csv"))
json.dump(RESULT, open(os.path.join(HERE, "emfx_results.json"), "w"), indent=1, default=str)
print("\nWROTE emfx_results.json + nets/")
