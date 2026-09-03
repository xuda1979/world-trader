"""Reconciliation gate (TRADE_RECORD_STANDARD): byte-level repro + ledger PnL == champion.
Short, testable, honest."""
from __future__ import annotations
import numpy as np
import pandas as pd


def max_abs_diff(a: pd.Series, b: pd.Series) -> float:
    j = pd.concat([a.rename('a'), b.rename('b')], axis=1, join='inner').dropna()
    return float((j.a - j.b).abs().max()) if len(j) else np.nan


def repro_ok(a: pd.Series, b: pd.Series, tol: float = 1e-12) -> bool:
    d = max_abs_diff(a, b)
    return d == d and d < tol


def ledgers_reproduce(ledger: pd.DataFrame, champion: pd.Series,
                      pnl_col: str = 'pnl_contrib', cost_col: str = 'cost_total',
                      tol: float = 1e-8) -> dict:
    """From a trade ledger (per-row pnl_contrib - cost_total) reproduce the champion daily PnL.
    Returns {ok, max_diff, n_mismatch}."""
    d = pd.to_datetime(ledger['date'])
    net = ledger[pnl_col].fillna(0.0) - ledger[cost_col].fillna(0.0)
    daily = pd.Series(net.values, index=pd.Index(d)).groupby(level=0).sum()
    j = pd.concat([daily.rename('ledger'), champion.rename('champ')], axis=1, join='inner').dropna()
    md = float((j.ledger - j.champ).abs().max()) if len(j) else np.nan
    return dict(ok=bool(md == md and md < tol), max_diff=md, n=len(j))


def turnover_reconciles(ledger: pd.DataFrame, pos_path: pd.DataFrame,
                        qty_col: str = 'qty_notional', tol: float = 1e-8) -> dict:
    """Per-sleeve sum|qty| == pos_path.diff().abs() charged turnover."""
    led = ledger.groupby(ledger['sleeve'])[qty_col].sum()
    pos = pos_path.diff().abs().sum(axis=0)
    j = pd.concat([led.rename('led'), pos.rename('pos')], axis=1).dropna()
    rel = (j.led - j.pos).abs() / j.pos.abs().replace(0, np.nan)
    ok = bool((rel.fillna(0) <= tol).all())
    return dict(ok=ok, max_rel=float(rel.fillna(0).max()), n=len(j))
