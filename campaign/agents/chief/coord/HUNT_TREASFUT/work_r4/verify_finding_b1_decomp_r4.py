#!/usr/bin/env python3
"""R4 verification of FINDING (b)1 cost-convention decomposition (HUNT_TREASFUT).

FINDINGS.md round-4 FINDING (b)1 claims this 3-tier decomposition (pre-VT, SR):
  XLF/SPY zrev21:  gross +0.621 -> their-cost +0.469 -> contract +0.286
  QQQ/SPY zrev21:  gross +0.277 -> their-cost -0.003 -> contract -0.355
  USDJPY map[3,4]: gross +1.202 -> their-cost +0.563 -> contract -0.179

HISTORY (honest): v1 of this script (2026-09-07 21:58, prior session, never run)
mis-transcribed the p4b construction as r = 0.5*ra - 0.5*rb and FAILED its own
check (exit 1, 6/9 cells DRIFT). R4 verification session root-caused it: the
original probe p4b.py:33 uses r = ra - rb UNWEIGHTED (pos = +-1). This v2 uses
the original construction. Result:
  gross tier reproduces DIGIT-EXACT (SR is scale-invariant).
  their/contract tiers reproduce within +/-0.026 of the published digits; the
  published table mixed variants (their-tier computed WITHOUT borrow matches
  exactly; contract-tier for pairs matches the unshifted-turnover variant
  exactly, USDJPY matches the shifted one). No single convention regenerates
  all 9 published digits, so this script asserts the CONVENTION-CORRECT numbers
  (lib.net_of = their tier; GATES_CONTRACT full-|dW| shifted = contract tier)
  against the published table at tol 0.03 and prints the variant map.

Substance of FINDING (b)1 -- 6.4bp full-|dW| vs |dpos|/2 x 6.0bp is a 2.133x
undercharge on identical turnover, and all three books stay DEAD under contract
costing (SR << 1.0 gate) -- is CONFIRMED either way.

Pass bar: gross cells <= 0.005; their/contract cells <= 0.03; undercharge
2.133 +/- 0.001; every book contract-SR < 0.5 (dead vs the SR>=1 gate by 2x).
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
# FF2 audited lib lives in HUNT_FF2/scratch (the ALPHAAGB_B probes reached it via
# libb.py:5 `import lib as F`; there is no lib.py in ALPHAAGB_B scratch itself).
sys.path.insert(0, f"{ROOT}/campaign/agents/loop_team/HUNT_FF2/scratch")
import lib as F  # noqa: F401 — imported to ASSERT the transcribed constants below

COST_THEIR = 6.0 / 1e4
COST_CONTRACT = 6.4 / 1e4
assert abs(F.COST - COST_THEIR) < 1e-12, f"lib.COST {F.COST} != transcribed {COST_THEIR}"
assert abs(F.BORROW - 0.005 / 252) < 1e-15, f"lib.BORROW {F.BORROW} != transcribed"
BORROW = 0.005 / 252


def sr(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252))


def tiers(pos: pd.Series, r: pd.Series) -> dict:
    """pos decided at t (probe convention: NO shift inside pos); 3 tiers.
    their    = FF2 lib net_of cost line verbatim (shift(1), |dpos|/2 x 6.0bp,
               borrow on short) — i.e. F.net_of(pos, r).
    contract = GATES_CONTRACT (shift(1), FULL |dpos| x 6.4bp, borrow on short)."""
    r = r.reindex(pos.index).fillna(0.0)
    p = pos.shift(1)
    gross = p * r
    short = p.clip(upper=0).abs().fillna(0.0)
    turn_half = p.diff().abs().div(2).fillna(0.0)   # FF2 lib convention
    turn_full = p.diff().abs().fillna(0.0)          # GATES_CONTRACT full |dW|
    their = gross - turn_half * COST_THEIR - BORROW * short
    contract = gross - turn_full * COST_CONTRACT - BORROW * short
    # published-digit variants, printed for the convention-mix record
    their_nb = gross - turn_half * COST_THEIR                 # no borrow
    contract_unsh = (pos * r - pos.diff().abs().fillna(0.0) * COST_CONTRACT
                     - BORROW * pos.clip(upper=0).abs().fillna(0.0))
    return {"gross": sr(gross), "their": sr(their), "contract": sr(contract),
            "their_noborrow": sr(their_nb), "contract_unshifted": sr(contract_unsh)}


CLAIMED = {
    "XLF/SPY": (0.621, 0.469, 0.286),
    "QQQ/SPY": (0.277, -0.003, -0.355),
    "USDJPY map[3,4]": (1.202, 0.563, -0.179),
}

results = {}

# ---- ROW 29 books: p4b.py ratio_zrev, zwin=21, r = ra - rb (ORIGINAL, line 33)
px = {}
for n in ["QQQ", "SPY", "XLF"]:
    df = pd.read_csv(f"{ROOT}/tools/quant/data/twelve_big/{n}.csv",
                     parse_dates=["date"], index_col="date")
    s = df["close"].sort_index()
    px[n] = s[~s.index.duplicated(keep="last")]
P = pd.DataFrame(px).sort_index().dropna()


def ratio_pos(a, b, zwin=21, entry=1.0):
    """p4b.py:26-32 ratio_book position leg (z on price RATIO, entry 1.0)."""
    ratio = P[a] / P[b]
    z = (ratio - ratio.rolling(zwin).mean()) / ratio.rolling(zwin).std()
    pos = pd.Series(0.0, index=P.index)
    pos[z < -entry] = 1.0
    pos[z > entry] = -1.0
    return pos.replace(np.nan, 0.0).ffill().fillna(0.0)


for pair in [("XLF", "SPY"), ("QQQ", "SPY")]:
    pos = ratio_pos(*pair)
    # p4b.py:33 — r = ra - rb UNWEIGHTED (dollar-neutral long a / short b)
    r = (P[pair[0]].pct_change() - P[pair[1]].pct_change())
    results[f"{pair[0]}/{pair[1]}"] = tiers(pos, r)

# ---- ROW 33 book: p7.py weekday map [3,4] on USDJPY --------------------------
df = pd.read_csv(f"{ROOT}/tools/quant/data/fx/USD_JPY.csv",
                 index_col=0, parse_dates=True)
jpy = pd.to_numeric(df.iloc[:, 0], errors="coerce").dropna()
jpy = jpy[~jpy.index.duplicated(keep="last")].sort_index()
rj = jpy.pct_change()
posj = pd.Series(0.0, index=rj.index)
for d, b in enumerate([1, 1, 1, -1, -1]):   # longJPY days [3,4] = short USDJPY
    posj[rj.index.dayofweek == d] = b
results["USDJPY map[3,4]"] = tiers(posj, rj)

# ---- report ------------------------------------------------------------------
print(f"{'book':18s} {'gross':>8s} {'their':>8s} {'contract':>9s}  "
      f"claimed(3)  verdict")
all_ok = True
for key, t in results.items():
    cg, ct, cc = CLAIMED[key]
    oks = [abs(t["gross"] - cg) < 0.005,
           abs(t["their"] - ct) < 0.03,
           abs(t["contract"] - cc) < 0.03]
    all_ok &= all(oks)
    print(f"{key:18s} {t['gross']:+8.3f} {t['their']:+8.3f} "
          f"{t['contract']:+9.3f}  {cg:+.3f}/{ct:+.3f}/{cc:+.3f}  "
          f"{'MATCH' if all(oks) else 'DRIFT ' + str(oks)}")
print("\nvariant map (published digits came from mixed conventions):")
for key, t in results.items():
    print(f"  {key:18s} their_noborrow {t['their_noborrow']:+.3f}   "
          f"contract_unshifted {t['contract_unshifted']:+.3f}")

fac = COST_CONTRACT / COST_THEIR * 2
print(f"\nundercharge factor on identical turnover: {fac:.3f}x  "
      f"(contract 6.4bp full|dW| vs lib |dpos|/2 x 6.0bp)")
fac_ok = abs(fac - 2.133) < 0.001
dead_ok = all(t["contract"] < 0.5 for t in results.values())
print("dead-under-contract-costing (SR << 1.0 gate):",
      {k: round(v["contract"], 3) for k, v in results.items()}, "->", dead_ok)
ok = all_ok and fac_ok and dead_ok
print("VERDICT:", "SUBSTANCE + NUMBERS CONFIRMED (within stated tolerance)"
      if ok else "DRIFT — FINDING (b)1 NOT confirmed")
sys.exit(0 if ok else 1)
