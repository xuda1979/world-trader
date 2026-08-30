"""Charter 1: trend + reinvested carry on XAU/SLV/copper, 126d trend, vt 15%.
Free data carry audit (honest): FRED xau/slv are SPOT series -> storage/lease carry not available;
copper is monthly only. The tradable carry component on free data = 0; we run the trend book
that the charter asks for and document that reinvested carry could not be constructed.
Plateau sweep over lookback; vt15 documented."""
import sys; sys.path.insert(0, __file__.rsplit("/",1)[0])
from r4_lib import *

METALS = {"XAU": "xau", "SLV": "slv"}
COPPER = px_fred("copper_monthly")  # monthly levels

def trend_pos(px, lb, mode="ls"):
    mom = px / px.shift(lb) - 1.0
    if mode == "ls":  return np.sign(mom)
    if mode == "lf":  return (mom > 0).astype(float)
    if mode == "ls_band":
        s = pd.Series(0.0, index=px.index); s[mom > 0.01] = 1.0; s[mom < -0.01] = -1.0
        return s
    raise ValueError

def one(asset, lb, mode, vt):
    px = px_fred(METALS[asset]) if asset in METALS else None
    if px is None: return None
    net, netvt = run_mech(trend_pos(px, lb, mode), px, vt)
    return netvt

def copper_trend(lb, mode="lf", vt=0.15):
    """copper monthly -> signal at month-end m, tradable from month m+1 (publication + 1 month,
    conservative: signal uses only completed months). Daily bday series."""
    m = COPPER.resample("MS").last()
    mom = m / m.shift(lb) - 1.0
    pos_m = (mom > 0).astype(float) if mode == "lf" else np.sign(mom)
    pos_m = pos_m.shift(1)  # publish +1mo
    daily = pos_m.reindex(pd.bdate_range(m.index[0], m.index[-1])).ffill()
    px = COPPER.reindex(daily.index).ffill().dropna()
    daily = daily.reindex(px.index).ffill().fillna(0)
    net, netvt = run_mech(daily, px, vt)
    return netvt

if __name__ == "__main__":
    for asset in METALS:
        px = px_fred(METALS[asset])
        for mode in ("ls", "lf"):
            for lb in (63, 126, 189, 252):
                net, netvt = run_mech(trend_pos(px, lb, mode), px, 0.15)
                g = full_gates(netvt); c, n = corr_to_champ(netvt)
                pr(f"{asset}-{mode}-{lb}-vt15", g, c, f"n={n}")
    # copper (monthly, short daily backtest via levels 2007+ ok)
    for lb in (3, 6, 12):
        for mode in ("lf", "ls"):
            r = copper_trend(lb, mode)
            g = full_gates(r); c, n = corr_to_champ(r)
            pr(f"CU-{mode}-{lb}m-vt15", g, c, f"n={n}")
