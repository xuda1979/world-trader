"""A2 r2 shared lib: PIT-correct COT positioning + FRED price mapping + honest mechanics."""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import numpy as np, pandas as pd
from data import fred, panel, apply_cost
from util import t1, fwd_returns, cost, vol_target, gates, scramble_test, halves_ok, yearly

COT = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_cot"
LAG = 4  # trading days: report Tue -> public Fri; use 4 to be safe

_DAILY_CACHE = {}

def _bday(s):
    """daily business-day ffill'd series"""
    s = s.dropna()
    idx = pd.bdate_range(s.index[0], s.index[-1])
    return s.reindex(idx).ffill()

def px_series(name):
    """canonical daily price level series (level, not return) for a mapped asset."""
    if name in _DAILY_CACHE: return _DAILY_CACHE[name]
    if name in ("SPY","QQQ"):
        ps = panel(); s = ps[name]["close"].dropna()
    elif name.startswith("UST"):
        yld = fred({"UST10":"us10y","UST30":"us30y","UST2":"us2y"}[name]).dropna()
        yld = _bday(yld)
        dur = {"UST10":7.5,"UST30":15.0,"UST2":1.8}[name]
        dy = yld.diff()/100.0
        tr = dur*(-dy) + yld.ffill()/100.0/252.0
        s = (1+tr.fillna(0)).cumprod()
    elif name in ("AAA","BAA"):
        yld = _bday(fred(name.lower()).dropna())
        dy = yld.diff()/100.0; tr = 7.0*(-dy) + yld.ffill()/100.0/252.0
        s = (1+tr.fillna(0)).cumprod()
    else:
        m = {"EUR":"eur","JPY":"jpy","GBP":"gbp","CAD":"cad","AUD":"aud","XAU":"xau","SLV":"slv",
             "WTI":"wti","BRENT":"brent","NATGAS":"natgas","COPX":"copx","DXY":"dxy","VIX":"vix"}
        s = _bday(fred(m[name]).dropna())
    _DAILY_CACHE[name] = s
    return s

def _map_tff():
    return {
        "S&P 500 Consolidated":"SPY", "NASDAQ-100 Consolidated":"QQQ",
        "DJIA Consolidated":"DJIA",
        "10-YEAR U.S. TREASURY NOTES":"UST10", "UST 10Y NOTE":"UST10",
        "U.S. TREASURY BONDS":"UST30", "UST BOND":"UST30",
        "ULTRA U.S. TREASURY BONDS":"UST30", "ULTRA UST BOND":"UST30", "ULTRA US T BOND":"UST30",
        "2-YEAR U.S. TREASURY NOTES":"UST2", "UST 2Y NOTE":"UST2",
        "EURO FX":"EUR", "JAPANESE YEN":"JPY", "BRITISH POUND":"GBP",
        "BRITISH POUND STERLING":"GBP", "CANADIAN DOLLAR":"CAD",
        # AUD/NZD dropped: no free daily price pre-2019 (r1 lesson)
    }

def _map_legacy():
    return {"GOLD":"XAU","SILVER":"SLV","COPPER":"COPX",
            "CRUDE OIL":"WTI","NATURAL GAS":"NATGAS"}

def _release_index(dates):
    """map report date -> release date (+LAG trading days)."""
    allbd = pd.bdate_range("1985-01-01", "2027-01-01")
    pos = allbd.searchsorted(pd.to_datetime(dates))
    return pd.DatetimeIndex([allbd[min(p+LAG, len(allbd)-1)] for p in pos])

def cot_weekly(source, field):
    """Return dict canonical_asset -> weekly series (index=release date) of net positioning."""
    if source == "tff":
        df = pd.read_csv(f"{COT}/tff_tidy.csv", parse_dates=["date"])
        mkt, long_c, short_c, mapping = "market", "lev_fund_long", "lev_fund_short", _map_tff()
        if field == "am": long_c, short_c = "asset_mgr_long", "asset_mgr_short"
    else:
        df = pd.read_csv(f"{COT}/legacy_tidy.csv", parse_dates=["date"])
        mkt = "market"; mapping = _map_legacy()
        if field == "spec": long_c, short_c = "noncomm_long", "noncomm_short"
        else: raise ValueError
    df[mkt] = df[mkt].str.strip()
    df["asset"] = df[mkt].map(mapping)
    miss = df["asset"].isna()
    if miss.any():
        def fix(name):
            for k, v in mapping.items():
                if name.startswith(k): return v
            return None
        df.loc[miss, "asset"] = df.loc[miss, mkt].map(fix)
    df = df.dropna(subset=["asset"])
    df = df[df["asset"] != "DJIA"]  # no long price series; skip
    df["net"] = df[long_c] - df[short_c]
    df["rel"] = _release_index(df["date"].values)
    out = {}
    for a, g in df.groupby("asset"):
        g = g.sort_values("rel").drop_duplicates("rel").set_index("rel")["net"]
        # weekly (W-FRI) last release carried
        out[a] = g.resample("W-FRI").last()
    return out

def weekly_pos_from_z(net_w, lookback_w, thr, zcap=2.0, contrarian=True):
    z = (net_w - net_w.rolling(lookback_w).mean()) / net_w.rolling(lookback_w).std()
    z = z.clip(-zcap, zcap)
    s = np.sign(-z if contrarian else z)
    s = s.where(z.abs() >= thr, 0.0)
    return s

def weekly_pos_from_change(net_w, lookback_w, min_frac=0.05):
    chg = net_w.diff(lookback_w)
    scale = net_w.rolling(lookback_w*2).std()
    zc = (chg/scale).clip(-2, 2)
    return np.sign(zc).where(zc.abs() >= min_frac, 0.0)

def daily_align(sig_w, px):
    """weekly signal (W-FRI) -> daily position, decided on info available <= that day.
       signal becomes tradable the NEXT trading day after release week (rebalance Mon)."""
    px = px.dropna()
    s = sig_w.reindex(sig_w.index.union(px.index)).ffill()
    s = s.shift(1)  # one extra day: release Fri -> trade Mon T+1
    return s.reindex(px.index).ffill().fillna(0.0)

def asset_sleeve(sig_w, asset, contrarian_cost=True, vt=True):
    """per-asset net vt'd daily return (decision-date convention, t1)."""
    px = px_series(asset)
    pos = daily_align(sig_w, px)
    fr = px.pct_change().shift(-1)
    gross = (pos * fr).dropna()
    to = pos.diff().abs().fillna(0)
    net = cost(gross, to)
    if vt:
        net = vol_target(net, 0.10)
    return net.dropna()

def run_book(book, vt2=True):
    """book: dict asset -> per-asset net vt'd returns. EW mean + overall vt."""
    df = pd.DataFrame(book).dropna(how="all").fillna(0.0)
    combo = df.mean(axis=1)
    combo = combo[combo.index >= df.ne(0).any(axis=1).idxmax()]
    if vt2: combo = vol_target(combo, 0.10)
    return combo.dropna()

def report(name, r, sig=None, ret_gross=None):
    g = gates(r)
    h1, h2 = halves_ok(r)
    yr = yearly(r)
    line = (f"{name}: pass={g.get('pass_')} SR={g.get('sr',0):.2f} H1={h1:.2f} H2={h2:.2f} "
            f"negyr={int((yr<0).sum())}/{len(yr)} worst={yr.min()*100:.1f}% "
            f"n={len(r)} {r.index[0].date()}..{r.index[-1].date()} ann={r.mean()*252*100:.1f}%")
    if sig is not None:
        _, p = scramble_test(sig, ret_gross)
        line += f" scramble_p={p:.3f}"
    print(line + ("" if g.get("pass_") else f"  [{g.get('why','')}]"))
    return g
