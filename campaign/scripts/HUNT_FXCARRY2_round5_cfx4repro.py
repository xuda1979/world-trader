#!/usr/bin/env python3
"""HUNT_FXCARRY2 R5 (a): reproduce why CFX4 sits at exactly 0.000 relw in
RAWEW13v2_IS_SR_weights.csv — honestly, from CFX4_DTF21_63_raw_daily.csv + its meta.

Chain to demonstrate, from live data only (no trust of CAMP_COST R4 prose):
  A. CFX4 raw sleeve span starts 2019-09-10 (read the CSV).
  B. Builder IS window is index < IS_END 2017-01-01 (read rawew13v2_build.py constants).
  C. The builder's IS slice of the CFX4 column is EMPTY (n=0 < 200) -> is_sr() returns 0.0
     (len<200 branch, line 58-60 of the builder).
  D. relw = max(IS_SR,0)^0.55 = 0.0^0.55 = 0.0 -> committed weights row is exactly 0.0.
  E. Algebraic inertness: with relw_CFX4=0, CFX4's column contributes 0 to d2 numerator and
     denominator -> dropping the slot reproduces the committed champion to float noise.
  F. The meta's own headline (SR 1.91 on 2019-09-10..2026-08-05, n=1799) recomputes from the
     raw CSV -> the sleeve is NOT dead; it is INELIGIBLE for IS-weighting by construction.
Prints every number; exit 0 iff all six reproduce.
"""
import hashlib
import re
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
CFX4 = f"{ROOT}/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv"
WGT = f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv"
BUILDER = f"{ROOT}/campaign/scripts/rawew13v2_build.py"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

fails = []


def check(name, ok, detail=""):
    print(f"[{'OK' if ok else 'FAIL'}] {name} {detail}")
    if not ok:
        fails.append(name)


# --- A. CFX4 raw span -------------------------------------------------------
cfx = pd.read_csv(CFX4, index_col=0)
cfx.index = pd.to_datetime(cfx.index)
col = "ret" if "ret" in cfx.columns else cfx.columns[0]
r = cfx[col].astype(float).dropna()
sha = hashlib.sha256(open(CFX4, "rb").read()).hexdigest()[:16]
print(f"CFX4 file sha256[:16]={sha}  cols={list(cfx.columns)}")
print(f"A. CFX4 span {r.index.min().date()} .. {r.index.max().date()}  n={len(r)}")
check("A: CFX4 starts after 2017-01-01", r.index.min() >= pd.Timestamp("2017-01-01"),
      f"(first obs {r.index.min().date()})")

# --- B. builder constants (read the file, don't trust prose) ----------------
src = open(BUILDER).read()
m_end = re.search(r"IS_END\s*=\s*pd\.Timestamp\('([0-9-]+)'\)", src)
m_p = re.search(r"^P\s*=\s*([0-9.]+)", src, re.M)
m_len = re.search(r"len\(r\)\s*<\s*(\d+)", src)
IS_END = pd.Timestamp(m_end.group(1))
P = float(m_p.group(1))
MINLEN = int(m_len.group(1))
print(f"B. builder IS_END={IS_END.date()} P={P} min_len={MINLEN}")
check("B: builder parses", m_end is not None and m_p is not None)

# --- C/D. IS slice empty -> is_sr 0.0 -> relw 0.0 ---------------------------
is_slice = r[r.index < IS_END]
print(f"C. IS-window obs for CFX4 = {len(is_slice)}  (<{MINLEN} -> is_sr()==0.0)")
check("C: IS slice below min_len", len(is_slice) < MINLEN)


def is_sr(x):
    x = x.dropna()
    if len(x) < MINLEN or x.std(ddof=1) <= 1e-12:
        return 0.0
    return float(x.mean() / x.std(ddof=1) * np.sqrt(252))


sr_cfx4 = is_sr(is_slice)
relw_repro = max(sr_cfx4, 0.0) ** P
print(f"D. IS-SR(CFX4)={sr_cfx4:.6f}  relw=max(SR,0)^{P}={relw_repro:.6f}")

wgt = pd.read_csv(WGT, index_col=0).iloc[:, 0]
w_cfx4 = float(wgt.loc["CFX4"])
check("D: relw reproduces 0.0", relw_repro == 0.0 and w_cfx4 == 0.0,
      f"(committed {w_cfx4})")
check("D2: every other slot relw > 0", bool((wgt.drop('CFX4') > 0).all()),
      f"(min non-CFX4 relw {wgt.drop('CFX4').min():.4f})")

# --- E. algebraic inertness vs committed champion ----------------------------
# Rebuild the committed book from the committed sleeve paths exactly as the builder does,
# with and without the CFX4 column; both must match the committed champion to float noise.
ns = {}
exec(compile(open(BUILDER).read().split("def main()")[0], BUILDER, "exec"), ns)
net, relw_b, gross, to, df = ns["build"]()

old = pd.read_csv(CHAMP, index_col=0)
old.index = pd.to_datetime(old.index)
oldc = old.iloc[:, 0].astype(float)
j = pd.concat([oldc, net], axis=1, join="inner").dropna()
dev_with = float((j.iloc[:, 0] - j.iloc[:, 1]).abs().max())

df_no = df.drop(columns=["CFX4"])
names_no = [n for n in ns["NAMES"] if n != "CFX4"]
relw_no = relw_b.drop("CFX4")
nav = (1 + df_no.fillna(0)).cumprod().shift(1).fillna(1.0)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw_no, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0) * len(names_no)
Wg = d2 * (ns["GEAR"] / len(names_no))
port = (df_no.fillna(0).values * Wg.values).sum(axis=1)
ton = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
net_no = (pd.Series(port, index=df_no.index)
          - ton * ns["BPS"] / 1e4
          - np.maximum(ns["GEAR"] - 1, 0) * ns["RATE"] / 252)
jn = pd.concat([oldc, net_no], axis=1, join="inner").dropna()
dev_no = float((jn.iloc[:, 0] - jn.iloc[:, 1]).abs().max())
print(f"E. builder(with CFX4, relw=0) vs committed champion: maxdev={dev_with:.3e}")
print(f"E. builder(drop CFX4 slot entirely)   vs committed: maxdev={dev_no:.3e}")
check("E: with-slot rebuild byte-faithful", dev_with < 1e-12)
check("E2: drop-slot inert", dev_no < 1e-12,
      f"(drop changes nothing beyond float noise)")

# --- F. meta headline honesty: CFX4 signal itself on its own span ------------
# (recompute, not trust): daily SR annualized, the meta's headline metric family.
n = len(r)
ann_geo = float(np.prod(1 + r) ** (252 / n) - 1)
sr_d = float(r.mean() / r.std(ddof=1) * np.sqrt(252))
mdd = float((r.cumsum() - r.cumsum().cummax()).min())
print(f"F. CFX4 own-span recompute: n={n} {r.index.min().date()}..{r.index.max().date()} "
      f"SR_d={sr_d:.4f} ann_geo={100*ann_geo:.2f}% mdd_log={100*mdd:.2f}%")
check("F: own-span SR ~1.9 (meta 1.9106)", abs(sr_d - 1.9106) < 0.01, f"(got {sr_d:.4f})")
oos17 = r[r.index >= IS_END]
sr_oos = float(oos17.mean() / oos17.std(ddof=1) * np.sqrt(252))
print(f"F. OOS(>=IS_END) n={len(oos17)} SR={sr_oos:.4f} — real, but UNWEIGHTABLE by an "
      f"IS-only rule that requires pre-2017 data.")
check("F2: zero pre-IS_END data, nonzero OOS", len(is_slice) == 0 and len(oos17) > 1000)

print()
if fails:
    print(f"REPRO VERDICT: FAIL ({len(fails)} checks: {fails})")
    sys.exit(1)
print("REPRO VERDICT: ALL CHECKS OK — CFX4 relw=0.0 is the builder's len<200 branch firing "
      "on an EMPTY pre-2017 IS window (data starts 2019-09-10); the slot is algebraically "
      "inert (drop-slot maxdev float noise); the sleeve itself is alive (own-span SR ~1.9) "
      "but structurally unweightable by an IS-only rule.")
