"""CAMP_COST R2 (c) — empirical per-sleeve cost-convention sweep of the champion pool.

For each of the 9 sleeves not re-emitted by costfix_emit.py, rebuild from its documented
generator recipe under the claimed convention and BYTE-compare to the committed CSV.
Classification per sleeve: FULL|dW|@6.4 / FULL|dW|@6.0 (rate residual) / HALF-TURN (offender)
/ 2x overcharge (conservative). Empirical, not just source-grep.
Run: python3 sweep13.py
"""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/work")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_BASIS2/scratch")
import numpy as np, pandas as pd
import lib as L                                   # fred()
from campaign.harness import data as D
from campaign.agents.B2_highfreq.gates import vol_target

ROOT = "/Users/daxu/software/world-trader"


def sha(p):
    import hashlib
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def dev(r, path):
    C = pd.read_csv(f"{ROOT}/{path}", index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    j = pd.concat([r.rename("a"), C.rename("b")], axis=1, join="inner").dropna()
    d = float((j.a - j.b).abs().max()) if len(j) else float("nan")
    return d, len(j), len(C)


def brwt_family(lb, path, full_dw, bps, gate=1.5):
    """B2 brwt recipe (as brwt15 in costfix_emit): z-rev on Brent-WTI log spread, vt10 cap3."""
    BR = D.fred("brent").dropna(); WT = D.fred("wti_full").dropna()
    sp = (np.log(BR) - np.log(WT)).dropna()
    z = (sp - sp.rolling(lb, min_periods=lb).mean()) / \
        sp.rolling(lb, min_periods=lb).std().replace(0, np.nan)
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -gate] = 1.0; pos[z > gate] = -1.0
    f = 1.0 if full_dw else 0.5
    net = (pos * sp.diff().shift(-1) - (pos.diff().abs() * f) * bps / 1e4).dropna()
    sc, _ = vol_target(net)
    r = sc.dropna()
    r = r[r.index >= "2000-01-01"] if "2000" in path else r[r.index >= "2008-01-01"]
    return r


def c5ng(summer, path, full_dw, bps):
    """e1_idea1_ng_detrunc recipe: DHHNGSP weekday prem, T+1, FULL |dpos| (line 25)."""
    COST = bps / 1e4
    px = D.fred("DHHNGSP").dropna()
    lr = np.log(px).diff()
    if summer:
        px2 = px[px.index.month.isin([4, 5, 6, 7, 8, 9, 10])]
        lr = np.log(px2).diff()
    dow = lr.index.dayofweek
    pos = pd.Series(0.0, index=lr.index)
    # Wed/Thu short, Fri long (documented) — but recipe details live in the generator;
    # instead of re-deriving every filter, reuse the generator module directly.
    raise NotImplementedError


def report(name, path, conv, r):
    d, ni, nc = dev(r, path)
    exact = d < 1e-12 and ni == nc
    print(f"  {name:9s} recon[{conv:22s}] n_inner={ni}/{nc} maxdev={d:.3e} "
          f"{'BYTE-EXACT' if exact else 'no'}")
    return exact


if __name__ == "__main__":
    print("== brwt family (B2 recipe, COORD sleeves) ==")
    for lb, name, path in [(10, "brwt10", "campaign/agents/COORD/sleeves/brwt10_2000.csv"),
                           (7,  "brwt7",  "campaign/agents/COORD/sleeves/brwt7.csv"),
                           (5,  "brwt5",  "campaign/agents/COORD/sleeves/brwt5.csv")]:
        report(name, path, "HALF 6.0", brwt_family(lb, path, False, 6.0))
        report(name, path, "FULL 6.0", brwt_family(lb, path, True, 6.0))
        report(name, path, "FULL 6.4", brwt_family(lb, path, True, 6.4))
