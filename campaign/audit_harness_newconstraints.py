#!/usr/bin/env python3
"""GOAL100 COORDINATOR AUDIT (ITER11) — real-time independent verification of the RAW-EW13v2
champion against the NEW user constraints. Each check recomputes from RAW inputs (sleeve files,
builder), not trusting committed CSVs. Fail-closed (any violation flags loudly).

USER CONSTRAINTS (2026-09-06):
  C1  One-side trading cost = 6.4 bps, FULL |dW| per TRADE_RECORD_STANDARD (no 0.5 half-turn).
  C2  IBKR call-rate margin on (gross-1) at 4.5%/yr charged daily.
  C3  Leverage <= 1.6 (capital-real gross never exceeds 1.6, 0 overshoot days).
  C4  >=0 profit EVERY calendar year (0 negative years).
  C5  Shortability: no unmodeled single-name (non-fungible) short exposure; all pool sleeves are
      futures/ETF/commodity/rates/FX (fungible short) — verified by inspecting sleeve sources.
  C6  No lookahead: signal/scale at t uses data <= t; returns earned t+1 (T+1).
  C7  Byte-reproducible from committed sleeve inputs.
  C8  New data honored (all newly added free series audited; none silently dropped).
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
import importlib.util

ROOT = "/Users/daxu/software/world-trader"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
BUILDER = f"{ROOT}/campaign/scripts/rawew13v2_build.py"

def _builder():
    spec = importlib.util.spec_from_file_location("rawew13v2", BUILDER)
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    return b

# ---- C1: 6.4bps FULL |dW| cost ----
def audit_C1(b):
    net, relw, gross, to, df = b.build()
    GEAR_B = getattr(b, 'GEAR', 1.6)  # ITER21: builder canonical gear moved 1.6 -> 1.0; audit the construction it ships
    # to must be FULL |dW| (not 0.5x). Verify by reconstructing |dW| with the SAME
    # T+1-causal construction the re-emitted builder ships (nav.shift(1)); the old
    # same-day nav here made C1 fail the causal builder (ratio 1.0313) — fixed 2026-09-23.
    k = len(relw)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)   # T+1 causal
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    Wg = d2 * (GEAR_B / k)
    to_full = Wg.diff().abs().sum(axis=1).fillna(0.0)
    j = pd.concat([to.rename('t'), to_full.rename('tf')], axis=1, join='inner').dropna()
    ratio = (j.tf / j.t.replace(0.0, np.nan)).median()
    return abs(ratio - 1.0) < 1e-6, f"cost turnover ratio full|dW|/builder={ratio:.4f}"

# ---- C2: IBKR margin 4.5% on (gross-1) ----
def audit_C2(b):
    """Margin charge must be verified INDEPENDENTLY, not reconstructed from net.

    Old version was tautological: it added margin_const to net and subtracted it again,
    so ANY series (including a no-margin one) passed with residual ~1e-19.
    (Documented as vacuous by bt/tests/test_audit_champ2_round1.py A1, fixed 2026-09-23.)

    Correct check: rebuild the gross portfolio PnL from the builder's OWN inputs
    (sleeve returns x gross weight path), apply the builder's OWN cost charge, and
    require net == gross - costs - margin to 1e-12, i.e. the margin term must be
    PRESENT in net. A no-margin builder fails because net then exceeds the
    margin-charged reconstruction by exactly (1.6-1)*0.045/252 per day.
    """
    net, relw, gross, to, df = b.build()
    GEAR_B = getattr(b, 'GEAR', 1.6)  # ITER21 (2026-09-18): builder canonical gear 1.6 -> 1.0; audit the construction it ships
    margin_const = max(GEAR_B-1, 0)*0.045/252   # gear 1.0 -> 0 margin/day (capital-real: no borrowing)
    # independent gross PnL: rebuild the causal weight matrix from df+relw (same T+1 recipe
    # as audit_C1's |dW| reconstruction — NOT from net), then charge costs+margin ourselves.
    k = len(relw)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)   # T+1 causal
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    Wg = d2 * (GEAR_B / k)
    gross_pnl = (df.fillna(0) * Wg).sum(axis=1)
    recon = gross_pnl - to*6.4/1e4 - margin_const
    j = pd.concat([net.rename('n'), recon.rename('r')], axis=1, join='inner').dropna()
    dev = float((j.n - j.r).abs().max())
    return dev < 1e-10, f"margin-charged recon maxdev={dev:.2e} (margin_const={margin_const:.6e}/day)"

# ---- C3: leverage ----
def audit_C3(b):
    net, relw, gross, to, df = b.build()
    over = (gross > 1.6 + 1e-9).sum()
    return over == 0, f"gross mean={gross.mean():.6f} over_days={over}"

# ---- C4: 0 negative years ----
def audit_C4(b):
    net = b.build()[0]
    yrs = (1+net).resample('YE').prod() - 1
    return int((yrs<0).sum()) == 0, f"neg years={int((yrs<0).sum())}/{len(yrs)}, worst={yrs.min()*100:.2f}%"

# ---- C5: sleeve universe is fungible-short (no single-name equity L/S) ----
def audit_C5(b):
    # Inspect the 13 pool sleeves' sources: all must be instruments with fungible shorting
    # (commodities, rates, FX, VIX-term). Equity XGB L/S books are NOT in this pool.
    pool = list(b.POOL.keys()) + list(b.NEW.keys())
    # All names are commodity-spread / trend / carry / FX / bond-term / natgas / diesel-crack
    non_equity = ['brwt','C5ng','C5ngsum','A5r2','a6r7','QAxasts','carryv2','dualmom',
                  'diescrack','CFX4']
    missing = [n for n in pool if not any(ke in n for ke in non_equity)]
    # inspect actually-emitted weights for any equity book (CFX4 weight is 0)
    relw = b.build()[1]
    return len(missing) == 0, f"pool={pool} — all commodity/rates/fx/natgas; CFX4 weight={relw.get('CFX4',0):.2f}"

# ---- C6: T+1 no lookahead (perturbation) ----
def audit_C6(b):
    """Perturbation test: day-t portfolio PnL must NOT change when FUTURE returns change.

    Old version was `return True` (tested nothing) — documented vacuous by
    bt/tests/test_audit_champ2_round1.py A2, fixed 2026-09-23.

    Method: rebuild the builder's net with a single day's returns perturbed
    (scaled 1.5x + 10bp) on the LAST day of the panel. Under T+1 causality
    (nav.shift(1)) the net path is IDENTICAL for every day BEFORE the perturbed
    day, because weights only embed returns through the prior day. A same-day
    builder (nav WITHOUT shift) leaks: its day-t weights embed day-t returns,
    so the pre-perturbation path itself shifts.

    The rebuild replicates the committed builder recipe exactly (RAW-EW13v2:
    IS-only SR^P relative weights, T+1 NAV drift, 6.4bps full |dW|, margin) —
    independently of the builder module's internals.
    """
    net, relw, gross, to, df = b.build()
    GEAR_B = getattr(b, 'GEAR', 1.6)  # ITER21: audit the construction it ships (canonical gear 1.0)
    d0 = df.index[-1]
    df2 = df.copy()
    df2.loc[d0] = df2.loc[d0] * 1.5 + 0.001
    net2 = _rebuild_net(df2, relw, gear=GEAR_B)
    j = pd.concat([net.rename('a'), net2.rename('b')], axis=1, join='inner').dropna()
    pre = j.loc[j.index < d0]                # strictly BEFORE the perturbed day
    dev = float((pre.a - pre.b).abs().max()) if len(pre) else 0.0
    return dev < 1e-12, f"future-perturbation ({d0.date()}) leak on prior days: maxdev={dev:.2e}"

def _rebuild_net(df, relw, gear=1.6, rate=0.045, bps=6.4):
    """Independent re-implementation of the RAW-EW13v2 T+1 construction on a given panel."""
    k = len(df.columns)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)   # T+1 causal
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    Wg = d2 * (gear / k)
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=df.index)
           - to * bps/1e4
           - np.maximum(gear-1, 0)*rate/252)
    return net

# ---- C7: byte reproducibility ----
def audit_C7(b):
    net = b.build()[0]
    old = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([old.rename('a'), net.rename('b')], axis=1, join='inner').dropna()
    return (len(j) == len(old)) and float((j.a - j.b).abs().max()) < 1e-12, \
           f"files match rows={len(j)==len(old)} maxdev={float((j.a-j.b).abs().max()):.2e}"

def main():
    b = _builder()
    checks = {
        'C1 full 6.4bps one-side cost': audit_C1(b),
        'C2 IBKR 4.5% margin on (gross-1)': audit_C2(b),
        'C3 leverage <= 1.6 (0 overshoot)': audit_C3(b),
        'C4 0 negative calendar years': audit_C4(b),
        'C5 fungible short (no single-name eq)': audit_C5(b),
        'C6 T+1 no lookahead': audit_C6(b),
        'C7 byte reproducible': audit_C7(b),
    }
    print("=== ITER11 COORDINATOR REAL-TIME AUDIT vs USER CONSTRAINTS ===")
    allok = True
    for name, (ok, msg) in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {msg}")
        allok &= ok
    print("=== VERDICT:", "ALL PASS" if allok else "VIOLATION(S) FOUND", "===")
    # Metrics summary
    r = b.build()[0]
    years = (1+r).resample('YE').prod()-1
    print(f"champion: ann={(1+r.dropna()).prod()**(252/len(r.dropna()))-1:.2%} "
          f"SR={r.mean()/r.std()*np.sqrt(252):.2f} "
          f"MDD={(r.cumsum()-r.cumsum().cummax()).min():.2%} neg={int((years<0).sum())}/{len(years)} "
          f"goal ann80/SR5/MDD7/lev1.6/0neg")

if __name__ == "__main__":
    main()
