"""Reconciliation gate (TRADE_RECORD_STANDARD): byte-level repro + ledger PnL == champion.
Short, testable, honest."""
from __future__ import annotations
import numpy as np
import pandas as pd


def max_abs_diff(a: pd.Series, b: pd.Series) -> float:
    j = pd.concat([a.rename('a'), b.rename('b')], axis=1, join='inner')
    # fail-closed: if ANY NaN is present in either series within the comparison, report inf
    if j.isna().any().any():
        return np.inf
    return float((j.a - j.b).abs().max()) if len(j) else np.inf


def repro_ok(a: pd.Series, b: pd.Series, tol: float = 1e-12) -> bool:
    d = max_abs_diff(a, b)
    return bool(d < tol)  # inf fails; NaN fails (inf) too


def ledgers_reproduce(ledger: pd.DataFrame, champion: pd.Series,
                      pnl_col: str = 'pnl_contrib', cost_col: str = 'cost_total',
                      tol: float = 1e-8) -> dict:
    """From a trade ledger (per-row pnl_contrib - cost_total) reproduce the champion daily PnL.
    Returns {ok, max_diff, n_mismatch}."""
    d = pd.to_datetime(ledger['date'])
    net = ledger[pnl_col].fillna(0.0) - ledger[cost_col].fillna(0.0)
    daily = pd.Series(net.values, index=pd.Index(d)).groupby(level=0).sum()
    j = pd.concat([daily.rename('ledger'), champion.rename('champ')], axis=1, join='inner')
    if len(j) != len(champion):
        # coverage hole: ledger must span every champion day
        return dict(ok=False, max_diff=float('inf'), n=len(j))
    if j.isna().any().any():
        return dict(ok=False, max_diff=float('inf'), n=len(j))
    md = float((j.ledger - j.champ).abs().max())
    return dict(ok=bool(md < tol), max_diff=md, n=len(j))


def turnover_reconciles(ledger: pd.DataFrame, pos_path: pd.DataFrame,
                        qty_col: str = 'qty_notional', tol: float = 1e-8) -> dict:
    """Per-sleeve sum|qty| == pos_path.diff().abs() charged turnover."""
    led = ledger.groupby(ledger['sleeve'])[qty_col].sum()
    # day-1 entry is real traded notional: seed prev row with zeros so diff covers it
    # (must match engine.cost_turnover charging semantics, AUDIT_FWBUGS R1).
    prev = pos_path.shift(1)
    prev.iloc[0] = 0.0
    pos = (pos_path - prev).abs().sum(axis=0)
    j = pd.concat([led.rename('led'), pos.rename('pos')], axis=1).fillna(0.0)
    # fail-closed: any |led - pos| > tol, OR a nonzero ledger qty on a zero pos turnover, => FAIL
    diff = (j.led - j.pos).abs()
    pos_zero_nled_nonzero = (j.pos == 0) & (j.led != 0)
    if pos_zero_nled_nonzero.any():
        return dict(ok=False, max_rel=float('inf'), n=len(j))
    denom = j.pos.abs().replace(0.0, np.nan)
    rel = (diff / denom).fillna(0.0)
    ok = bool((rel <= tol).all())
    return dict(ok=ok, max_rel=float(rel.max()) if len(rel) else 0.0, n=len(j))
