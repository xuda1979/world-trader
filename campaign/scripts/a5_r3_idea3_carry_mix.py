"""A5 r3 idea3: FX accrual-carry (A2-style, rebuilt) blended with A5 contango champion.
Mix vol-targeted; gates on mix; scramble = block circular-shift of one member (blend-aware)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from a5_r3_lib import gates_a_c_d, vt_scale, sr, halves, stats, lib_corr, corr_summary
import data as D

FRED = D.FRED
def _fred(n):
    s = D.fred(n); s.index = pd.to_datetime(s.index); return s.sort_index()
def _twd(p, invert=False):
    s = pd.read_csv(f"{D.FX}/{p}.csv", parse_dates=["date"], index_col="date")["close"].sort_index()
    return 1.0/s if invert else s

px = pd.DataFrame({"EUR": _fred("eur"), "GBP": _fred("gbp"),
                   "JPY": 1.0/_fred("jpy"), "CAD": 1.0/_fred("cad"),
                   "AUD": _twd("AUD_USD"), "NZD": _twd("NZD_USD"), "CHF": _twd("USD_CHF", invert=True)}).sort_index()
px = px[~px.index.duplicated(keep="last")]
y = pd.DataFrame({"USD": _fred("us10y"), "EUR": _fred("ez10y"), "GBP": _fred("gb10y"),
                  "JPY": _fred("jp10y"), "CAD": _fred("ca10y"), "CHF": _fred("ch10y"),
                  "AUD": _fred("au10y"), "NZD": _fred("nz10y")}).sort_index()
ym = y.resample("MS").mean()
diff = ym.sub(ym["USD"], axis=0).drop(columns=["USD"])
diff_d = diff.reindex(px.index).ffill()
accr = diff_d / 100.0 / 252.0
sig = diff.reindex(px.index).ffill()
ranks = sig.rank(axis=1, ascending=False); n_ok = sig.notna().sum(axis=1)
pos = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
for c in sig.columns:
    pos[c] = np.where(ranks[c] <= 2, 0.25, np.where(ranks[c] > n_ok-2, -0.25, 0.0))
ms = sig.groupby([sig.index.year, sig.index.month]).tail(1).index
pos = pos.loc[ms].reindex(pos.index).ffill().fillna(0.0)
pos = pos.loc["2018-07-01":]
fr = px.pct_change().shift(-1)
fr = fr + accr.shift(-1)                      # carry-adjusted fwd return
pnl = (pos * fr).sum(axis=1, min_count=1)
to = pos.diff().abs().sum(axis=1).fillna(pos.abs().sum(axis=1))
rc = pnl - to * D.COST / 1e4
rc = rc * vt_scale(rc)
carry = rc.dropna()

# contango champion (rebuild exactly as r2 script)
V1 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv',
                 parse_dates=['DATE']).set_index('DATE')['vix']
V3 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv',
                 parse_dates=['DATE']).set_index('DATE')['vix3m']
TS = pd.concat([V1, V3], axis=1).dropna()
US = D.fred('us10y').reindex(TS.index).ffill()
R1 = D.closes()["SPY"].pct_change(); R1.index = R1.index.tz_localize(None)
R1 = R1.reindex(TS.index).fillna(0.0)
ratio = TS["vix"] / TS["vix3m"]
st = 0.0; base = []
for v in ratio.values:
    if v < 1.02: st = 1.0
    elif v > 1.07: st = 0.0
    base.append(st)
C = pd.Series(base, index=ratio.index)
shock = (US > 2.75) & ((US - US.shift(150)) > 0.25)
RS = (~shock.fillna(False)).astype(float)
P = C * RS
posc = P.shift(1).fillna(0.0)
toc = posc.diff().abs().fillna(posc.abs())
net0 = posc * R1 - toc * D.COST / 1e4
scc = vt_scale(net0, cap=2.0)
posf = posc * scc
to2 = posf.diff().abs().fillna(posf.abs())
contango = (posf * R1 - to2 * D.COST / 1e4).dropna()

both = pd.concat([carry, contango], axis=1, keys=["c","t"]).dropna()
print("overlap window:", both.index[0].date(), "->", both.index[-1].date(), "n=", len(both))
print("raw corr carry-vs-contango:", round(both.corr().iloc[0,1], 3))
gates_a_c_d("carry solo (2018+)", carry)
gates_a_c_d("contango solo", contango)

def mix_of(w):
    m = (w*both["c"] + (1-w)*both["t"])
    m = m * vt_scale(m)      # keep vt10 on the mix
    return m.dropna()

def shift_scramble(mix, n=200, seed=1):
    """Blend-aware: circular-shift contango leg by random k, keep carry leg; mix SR dist."""
    rng = np.random.default_rng(seed)
    a = both["c"].values; b = both["t"].values
    real = sr(mix)
    cnt = 0
    for _ in range(n):
        k = rng.integers(1, len(a))
        aa = np.roll(a, k)
        mm = pd.Series(aa*0.5 + b*0.5, index=both.index)
        mm = mm * vt_scale(mm)
        if sr(mm.dropna()) >= real: cnt += 1
    return cnt / n

for w in (0.3, 0.5, 0.7):
    m = mix_of(w)
    g = gates_a_c_d(f"mix w_contango={w}", m)
    if g["ok"]:
        p = shift_scramble(m)
        print(f"    shift-scramble p={p:.3f}")
        print(corr_summary(lib_corr(m)))
