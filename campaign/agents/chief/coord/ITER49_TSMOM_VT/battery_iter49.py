import sys, hashlib, json
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER49_TSMOM_VT"
sys.path.insert(0, ROOT + "/campaign/bt")
import verify_champion as V

names12 = ["brwt10", "brwt7", "brwt5", "C5ng", "C5ngsum", "A5r2", "a6r7", "QAxasts", "carryv2", "dualmom", "diescrack", "CFX4"]
sleeve_paths = {
    "brwt10": ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7": ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5": ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "C5ng": ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2": ROOT + "/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock__vt024.csv",
    "a6r7": ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts": OUT + "/arm_vt015_stream_tsm.csv",
    "carryv2": ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom": ROOT + "/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack": ROOT + "/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4": ROOT + "/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
sleeves = dict()
missing = []
errs = []
for n in names12:
    r = V._load_ret(sleeve_paths[n], n, errs)
    if r is None:
        missing.append(n)
    else:
        sleeves[n] = r
assert not missing, missing
df = V._build_frame(sleeves, names12, "2008-03-31")
relw_canon = V._relw_from(df, "2017-01-01", 0.55, rule="minsharpe", shrink=0.70, brwt_cap=0.30)
W = V._weights_gear(df, relw_canon, 1.0)
net, to = V._net_from(df, W, 6.4, 0.045, 1.0)
drv_relw = pd.read_csv(OUT + "/arm_vt015_weights.csv", index_col=0).iloc[:, 0]
d_w = float((relw_canon - drv_relw.reindex(relw_canon.index)).abs().max())
print("canonical-vs-driver relw maxdev = %.3e" % d_w)
relw_canon.to_frame("relw").to_csv(OUT + "/canonical_tsm015_weights.csv")
pd.DataFrame(dict(ret=net.values), index=net.index).to_csv(OUT + "/canonical_tsm015_daily.csv")

def sr(x): return float(x.mean() / x.std(ddof=1) * np.sqrt(252))
def mdd(x):
    nav = (1 + x).cumprod(); return float((nav / nav.cummax() - 1).min())
def ann_cagr(x): return float((1 + x).prod() ** (252 / len(x)) - 1)
def ann_arith(x): return float(x.mean() * 252)
def neg_years(x):
    yr = x.groupby(x.index.year).apply(lambda v: (1 + v).prod() - 1)
    return yr[yr < 0]

champ = pd.read_csv(ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv", index_col=0, parse_dates=True).iloc[:, 0]
f_sr, f_mdd = sr(net), mdd(net)
f_ann_a, f_ann_c = ann_arith(net) * 100, ann_cagr(net) * 100
nyf = neg_years(net)
gmax = float(W.abs().sum(axis=1).max())
wmax_sf = float(relw_canon.max()) * 11
cfx = float(relw_canon["CFX4"])
bins = (("2017-18", "2017", "2018"), ("2019-20", "2019", "2020"), ("2021-22", "2021", "2022"), ("2023-24", "2023", "2024"), ("2025-26", "2025", "2026"))
dsrc = []
for lbl, a, b in bins:
    m_c = net[(net.index >= a + "-01-01") & (net.index <= b + "-12-31")]
    m_i = champ[(champ.index >= a + "-01-01") & (champ.index <= b + "-12-31")]
    dsrc.append(sr(m_c) - sr(m_i))
pos = sum(1 for d in dsrc if d > 0)
g = {
    "G1": (f_ann_c >= 20.0) or (f_ann_a >= 20.0),
    "G2": gmax <= 1.6 + 1e-9,
    "G3": f_mdd >= -0.07,
    "G4": len(nyf) == 0,
    "G5": cfx == 0.0,
    "G6": wmax_sf <= 2.0 + 1e-9,
    "G7": (pos >= 4) and (min(dsrc) >= -0.10) and (f_sr > 3.784099),
}
print("CANONICAL: FS SR=%.6f cagr=%.4f arith=%.4f MDD=%.4f negyrs=%d grossmax=%.9f Wmax_sf=%.4fx" % (f_sr, f_ann_c, f_ann_a, f_mdd * 100, len(nyf), gmax, wmax_sf))
print("G7 bins:", ["%+.4f" % d for d in dsrc], "pos=%d/5 min=%+.4f" % (pos, min(dsrc)))
print("GATES:", g)
print("ALL-GATES:", all(g.values()))
yr = net.groupby(net.index.year).apply(lambda v: (1 + v).prod() - 1) * 100
print("worst yr cand=%.4f%%" % yr.min())
relw_prior = pd.read_csv(ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv", index_col=0).iloc[:, 0]
print("QAxasts book share: prior %.4f pct -> tsm-vt015 %.4f pct" % (relw_prior["QAxasts"] * 100, relw_canon["QAxasts"] * 100))
h = len(net) // 2
h1 = sr(net.iloc[:h]) - sr(champ[champ.index.isin(net.index[:h])])
h2 = sr(net.iloc[h:]) - sr(champ[champ.index.isin(net.index[h:])])
print("H1 dSR %+.4f  H2 dSR %+.4f" % (h1, h2))
yrc = net.groupby(net.index.year).apply(lambda v: (1 + v).prod() - 1) * 100
yri = champ.groupby(champ.index.year).apply(lambda v: (1 + v).prod() - 1) * 100
d = (yrc - yri).dropna()
print("yr deltas positive %d/%d, worst delta %+.3f pp" % ((d > 0).sum(), len(d), d.min()))
s10 = pd.read_csv(ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv", index_col=0, parse_dates=True).iloc[:, 0]
s15 = pd.read_csv(OUT + "/arm_vt015_stream_tsm.csv", index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([s10.rename("a"), s15.rename("b")], axis=1, join="inner").dropna()
print("tsmom standalone SR vt010 %.4f vt015 %.4f (std ratio %.4fx = 1.50 expected for pure scale)" % (sr(j.a), sr(j.b), j.b.std() / j.a.std()))
corr = float(pd.concat([net.rename("a"), champ.rename("b")], axis=1, join="inner").dropna().corr().iloc[0, 1])
print("corr(canonical candidate, incumbent champion) = %.10f" % corr)
print("turnover bp/yr = %.4f" % (float(to.mean()) * 252 * 6.4))
