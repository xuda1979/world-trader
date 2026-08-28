"""FX helpers for A2_fx_carry. Uses campaign harness mechanics only."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import data, util

FRED = data.FRED
FXD  = data.FX

def _fred(n):
    s = data.fred(n); s.index = pd.to_datetime(s.index)
    return s.sort_index()

def _twd(pair, invert=False):
    df = pd.read_csv(f"{FXD}/{pair}.csv", parse_dates=["date"], index_col="date")
    s = df["close"].sort_index()
    return 1.0/s if invert else s

def spots(start=None, end=None):
    """USD per 1 unit of foreign currency, stitched FRED(2000+) + twelvedata(2019+)."""
    out = {}
    out["EUR"] = _fred("eur"); out["GBP"] = _fred("gbp")
    out["JPY"] = 1.0/_fred("jpy"); out["CAD"] = 1.0/_fred("cad")
    out["AUD"] = _twd("AUD_USD"); out["NZD"] = _twd("NZD_USD"); out["CHF"] = _twd("USD_CHF", invert=True)
    px = pd.DataFrame(out).sort_index()
    px = px[~px.index.duplicated(keep="last")]
    px = px.loc[(px.index >= (start or px.index[0])) & (px.index <= (end or px.index[-1]))]
    return px

def yields8():
    """Monthly 10y yields for USD + 7 foreigners (2018+)."""
    y = pd.DataFrame({
        "USD": _fred("us10y"), "EUR": _fred("ez10y"), "GBP": _fred("gb10y"),
        "JPY": _fred("jp10y"), "CAD": _fred("ca10y"), "CHF": _fred("ch10y"),
        "AUD": _fred("au10y"), "NZD": _fred("nz10y")}).sort_index()
    return y

def t1_pnl(pos: pd.DataFrame, px: pd.DataFrame) -> pd.Series:
    """pos decided at t (data<=t), earns FX return t->t+1. Dates = decision dates."""
    fr = px.pct_change().shift(-1)
    return (pos * fr).sum(axis=1, min_count=1)

def turnover(pos: pd.DataFrame) -> pd.Series:
    return pos.diff().abs().sum(axis=1)

def net_of(pnl, pos, vt=True, target=0.10):
    r = util.cost(pnl, turnover(pos))
    if vt: r = util.vol_target(r, target=target)
    return r.dropna()

def report(name, r):
    g = util.gates(r)
    sr = r.mean()/r.std()*np.sqrt(252)
    h1, h2 = util.halves_ok(r)
    yr = util.yearly(r)
    print(f"[{name}] n={len(r)} SR={sr:.2f} H1={h1:.2f} H2={h2:.2f} "
          f"negYr={int((yr<0).sum())} worst={yr.min()*100:.1f}% ann={r.mean()*252*100:.2f}% vol={r.std()*np.sqrt(252)*100:.1f}% pass={g.get('pass_')} {g.get('why','')}")
    return g, sr, h1, h2

def scramble(r_sig, r_ret, n=200, seed=7):
    real, p = util.scramble_test(r_sig, r_ret, n=n, seed=seed)
    print(f"  scramble: real={real:.2f} p={p:.3f} {'PASS' if p<0.05 else 'FAIL'}")
    return real, p
