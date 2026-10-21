#!/usr/bin/env python3
"""RES_STATARB R1 hunt library — sector/industry RELATIVE-VALUE engines (no browser).

Charter: campaign/team/charters/RES_STATARB.md. Panel: Ken French 49 industry EW daily
(tools/quant/data/kenfrench). Conventions mirror the GATES_CONTRACT_V2 sec-0 pattern
(RES_BASIS hunt_r1 lineage): T+1 via shift(1), trailing-only stats, vt on the GROSS path,
6.4bps/side FULL |dW| (bt.engine.cost_turnover), 0.5%/yr borrow on shorts, and the V2
battery judged with r = PER-UNIT returns and sig = effective gross book weight so
sig*r == the held book exactly.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

import numpy as np
import pandas as pd
from bt.engine import vol_target_scale, cost_turnover, borrow_cost

ROOT = "/Users/daxu/software/world-trader"
SC = f"{ROOT}/campaign/team/agents/RES_STATARB/scratch"
VT_TARGET, VT_CAP = 0.08, 3.0


def load_panel(path):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return (df / 100.0).apply(pd.to_numeric, errors="coerce")


def ls_weights(R, tr, k):
    """Long top-k industries by `tr` (trailing signal), short bottom-k, 1/k each side.
    Ties broken deterministically by column order (tiny deterministic jitter)."""
    j = pd.DataFrame(np.tile(np.arange(R.shape[1]) * 1e-9, (R.shape[0], 1)),
                     index=R.index, columns=R.columns)
    rk = tr.add(j).rank(axis=1, method="first")  # "first" breaks value-ties by column order
    n = R.shape[1]                                # so exactly k distinct legs per side survive
    is_long = rk > n - k
    is_short = rk <= k
    W = pd.DataFrame(0.0, index=R.index, columns=R.columns)
    W[is_long & ~is_short] = 1.0 / k        # take long legs first ...
    W[is_short & ~is_long] = -1.0 / k       # ... then short legs (no double-count on overlap)
    # Degenerate-tie guard (AUDIT_DAX 2026-09-17): when the top-k and bottom-k rank sets
    # overlap (e.g. all signals identical -> every rank ties), no long/short partition
    # exists. The only dollar-neutral book there is flat -- zero such rows rather than emit
    # overlapping +/-k legs whose row-sum is non-zero.
    degenerate = (is_long & is_short).any(axis=1)
    W.loc[degenerate] = 0.0
    return W


def gross_book(W, R, target=VT_TARGET, vt=True):
    """T+1 effective weights, trailing vt on gross. Returns (rpu, We, gross) where
    rpu = per-unit book return (V2 sec-0: sig*r convention) AFTER vt scaling."""
    We = W.shift(1).fillna(0.0)
    gross = We.abs().sum(axis=1)                     # 2.0 when fully invested
    if vt:
        s = vol_target_scale(gross.to_frame('g'), target=target, cap=VT_CAP)['g']
        We = We.mul(s, axis=0)
    rpu = (We * R.fillna(0.0)).sum(axis=1)
    return rpu, We, gross


def net_of(rpu, We):
    """6.4bps/side full |dW| + 0.5%/yr borrow on shorts. We already T+1 + vt."""
    return (rpu - cost_turnover(We, cost_bps=6.4) - borrow_cost(We)).dropna()


def build(panel_csv, kind, lb, k, target=VT_TARGET):
    """kind='mom': L/S industry momentum (long trailing winners). kind='rev': fade
    trailing extremes. Returns (net, rpu, We) over the live (signal-available) span,
    truncated to 2008-01-01+ (champion overlap)."""
    R = load_panel(panel_csv)
    R = R[R.index >= '2008-01-01']
    tr = R.rolling(lb).mean() if kind == 'mom' else -R.rolling(lb).sum()
    W = ls_weights(R, tr, k)
    rpu, We, gross = gross_book(W, R, target=target)
    net = net_of(rpu, We)
    live = We.abs().sum(axis=1) > 0
    start = live.idxmax() if live.any() else net.index[0]
    sl = net.index >= start
    return net[sl], rpu[sl], We.loc[sl]
