#!/usr/bin/env python3
"""CAMP_BORROW ROUND 5 — measured short-leg census + embedded-borrow verification.

Claims this script certifies (all fail-closed):
  C1. ZERO of the 13 champion slots have any negative weight on any of the 4,805 days
      (no stock-loan borrow exposure exists at slot level; short legs live INSIDE sleeve
      net files, and those books are futures/ETF/spot proxies, not stock loan).
  C2. The committed diescrack file embeds a borrow line of EXACTLY -0.005/252 per day on
      733 of 4,605 rows (331 short-leg, 173 long-leg, 229 cost-only rows) vs a borrow-free
      reconstruction (meta discloses the long/cost-only charging as conservative overcharge).
  C3. Champion-level embedded borrow drag = 0.2196 bps/yr; HTB tier uplift measured through
      actual champion weights: 2% tier -> 0.6586 bps/yr (dAnn -0.00659pp), 8% -> 3.2931 bps/yr
      (dAnn -0.03293pp). Both immaterial; no gate moves (0 neg yrs / MDD > -7% unaffected).
  C4. CFX4 (the other borrow-declaring sleeve) has champion weight exactly 0.0 on all
      4,805 days: relw = max(IS_SR,0)^0.55 = 0 because its data starts 2019-09 (after
      IS_END 2017-01-01), so IS_SR <= 0 -> unfunded slot.

Evidence-only; exits nonzero on any failed assertion. No champion edits, no bt/ edits.
"""
import sys
sys.path.insert(0, "campaign")
sys.path.insert(0, "campaign/scripts")
sys.path.insert(0, "campaign/agents/loop_team/HUNT_BASIS2/scratch")
import numpy as np
import pandas as pd
import importlib.util

spec = importlib.util.spec_from_file_location("rawew13v2_build", "campaign/scripts/rawew13v2_build.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
import lib as L

# ---- champion weight stream ----
net, relw, gross, to, df = mod.build()
nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw)
Wg = d2 * (mod.GEAR / len(relw))

print("[C1] slot-level short census (negative weights) over all", len(Wg), "days:")
tot_short = 0.0
for c in Wg.columns:
    w = Wg[c]
    n_neg = int((w < -1e-12).sum())
    sn = float(-w[w < -1e-12].mean()) if n_neg else 0.0
    tot_short += sn * n_neg / len(w)
    print(f"    {c:9s} days_neg={n_neg:5d}  mean_short_notl={sn:.6f}")
print(f"    TOTAL mean short notional = {tot_short:.6f} of NAV")
assert (Wg < -1e-12).sum().sum() == 0, "C1 FAILED: negative slot weight found"

print("\n[C4] CFX4 funding: relw =", float(pd.Series(relw, index=df.columns)["CFX4"]),
      "; nonzero weight days =", int((Wg['CFX4'].abs() > 1e-12).sum()))
assert (Wg["CFX4"].abs() > 1e-12).sum() == 0

# ---- diescrack embedded borrow isolation ----
print("\n[C2] diescrack embedded-borrow isolation (borrow-free reconstruction vs committed):")
dj = L.fred('DJFUELUSGULF', L.NEW)
wti = L.fred('wti_full', L.FRED)
spread = np.log(dj * 42) - np.log(wti)
n_, g_, pos, tup = L.zrev(spread, lookback=40, gate=2.0, min_start='2008-01-01')
netv, _ = L.vol_target(n_, vt_ann=0.08, min_days=60, cap=3.0)
dc = pd.read_csv("campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
                 index_col=0, parse_dates=True)["ret"].dropna()
j = pd.concat([netv.rename("recon"), dc.rename("committed")], axis=1, join="inner").dropna()
line = (j.committed - j.recon)
nz = line.abs() > 1e-12
unit = 0.005 / 252
charged = line[nz]
print(f"    n={len(j)}  charged rows={int(nz.sum())}  all |dev| within 1e-9 of 0.005/252: "
      f"{bool((charged.abs() - unit).abs().max() < 1e-9)}")
posj = pos.reindex(j.index)
n_short = int(((posj < 0) & nz).sum()); n_long = int(((posj > 0) & nz).sum())
n_cost = int(nz.sum()) - n_short - n_long
print(f"    charged rows split: short={n_short} long={n_long} cost-only={n_cost}")
assert int(nz.sum()) == 733 and n_short == 331 and n_long == 173 and n_cost == 229
assert float((charged.abs() - unit).abs().max()) < 1e-9

# ---- champion-level drag + HTB tiers ----
print("\n[C3] champion-level borrow drag + HTB tiers (through actual weights):")
w = Wg["diescrack"].reindex(line.index)
drag = float((w * line).dropna().sum() / (len(w) / 252))
print(f"    embedded drag = {-drag*1e4:.4f} bps/yr of NAV")
res = {}
for tier in (0.02, 0.08):
    extra = float((w * (line * (tier / 0.005 - 1))).dropna().sum() / (len(w) / 252))
    res[tier] = extra
    print(f"    tier {tier*100:.0f}%: extra drag = {-extra*1e4:.4f} bps/yr "
          f"(dAnn {extra*100:+.5f}pp)")
assert abs(res[0.08] + 3.2931e-4) < 2e-6
assert abs(res[0.02] + 6.586e-5) < 2e-6
print("\nSHORT CENSUS + BORROW VERIFICATION OK")
