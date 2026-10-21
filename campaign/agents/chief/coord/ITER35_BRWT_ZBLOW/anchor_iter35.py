import sys
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
from campaign.agents.B2_highfreq.gates import vol_target

FRED = ROOT + "/tools/quant/hedge_fund_strats/data_fred"
EIA = ROOT + "/tools/quant/data/eia_weekly"


def _load(pstr):
    df = pd.read_csv(pstr, index_col=0, parse_dates=True)
    v = df.iloc[:, 0]
    return pd.to_numeric(v, errors="coerce").dropna()


def fred(name):
    s = _load(FRED + "/" + name + ".csv")
    return s[~s.index.duplicated(keep="last")].sort_index()


def brwt_load():
    BR = fred("brent")
    WT = fred("wti")
    E_BR = _load(EIA + "/brent_spot_daily.csv")
    E_WT = _load(EIA + "/wti_spot_daily.csv")
    BR = pd.concat([BR, E_BR[E_BR.index > BR.index[-1]]])
    WT = pd.concat([WT, E_WT[E_WT.index > WT.index[-1]]])
    return BR, WT


def brwt_build(lb, zb, min_start):
    BR, WT = brwt_load()
    sp = (np.log(BR) - np.log(WT)).dropna()
    sp = sp[sp.index >= min_start]
    m = sp.rolling(lb, min_periods=lb).mean()
    sd = sp.rolling(lb, min_periods=lb).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -zb] = 1.0
    pos[z > zb] = -1.0
    gross = pos * sp.diff().shift(-1)
    net = gross - pos.diff().abs() * 6.4 / 1e4
    scaled, _ = vol_target(net)
    return scaled


SL = ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/"
ARMS = [(10, "brwt10_2000__costfix.csv", "2000-01-01"),
        (7, "brwt7__costfix.csv", "2008-01-01"),
        (5, "brwt5__costfix.csv", "2008-01-01")]
ok = True
for lb, name, ms in ARMS:
    saved = pd.read_csv(SL + name, index_col=0, parse_dates=True).iloc[:, 0]
    saved = pd.to_numeric(saved, errors="coerce")
    gen = brwt_build(lb, 1.0, ms)
    j = pd.concat([gen.rename("gen"), saved.rename("saved")], axis=1, join="inner").dropna()
    dev = float((j["gen"] - j["saved"]).abs().max())
    print(name, "lb=%d inner_n=%d gen_n=%d saved_n=%d dev=%.6e" % (lb, len(j), len(gen), len(saved), dev))
    print("  gen_tail=%s saved_tail=%s" % (gen.index.max(), saved.index.max()))
    ok = ok and dev < 1e-12
print("A1 ANCHOR:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 2)
