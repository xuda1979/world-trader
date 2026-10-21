"""Finviz quote-page data: analyst consensus + positioning, free.

Replaces the 403'd Finnhub price-target endpoint (wt/altdata.py:analyst_target
notes the 403 as of 2026-07-12). One HTTP GET per ticker to
finviz.com/quote.ashx; returns (dict, err) like every other wt source.

Provides what Finnhub free tier does not:
  target_price      consensus analyst target -> implied upside pct
  eps_next_y_pct    forward-consensus EPS growth (the valuation anchor
                    RESEARCH_LOG.md:3383 said the stack lacked)
  forward_pe / peg  forward valuation multiples
  short_float_pct   positioning (existing Nasdaq SI list 404s)
  inst/insider own  ownership structure
  perf_*            trailing performance ladder

Heavy lifting (fetch/parse/lint) lives in
tools/quant/data/finviz/finviz_dl.py -- this module is a thin adapter so the
agent tool-registry can call it without the quant data path.
"""
from __future__ import annotations
import os
import sys
import threading

from .core import describe_err

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                         "quant", "data", "finviz")
_lock = threading.Lock()
_mod = None


def _load_dl():
    """Import finviz_dl from the quant data dir under any launch mode."""
    global _mod
    with _lock:
        if _mod is not None:
            return _mod
        if _DATA_DIR not in sys.path:
            sys.path.insert(0, _DATA_DIR)
        try:
            import finviz_dl as m
        except Exception as e:  # pragma: no cover
            raise ImportError("finviz_dl import failed: %s" % e)
        _mod = m
        return _mod


def snapshot(sym):
    """ticker -> (dict of consensus fields, err). err None on success."""
    try:
        m = _load_dl()
    except ImportError as e:
        finviz_dl = None
        return None, str(e)
    try:
        body = m.fetch_html(sym)
        d = m.parse_snapshot(body)
        d["ticker"] = sym.upper()
        row = m.to_floats(d)
        row["implied_upside_pct"] = m.implied_upside(row.get("price"),
                                                     row.get("target_price"))
        row["fwd_ey_pct"] = (100.0 / row["forward_pe"]) if row.get("forward_pe") else None
    except Exception as e:
        return None, describe_err(e)
    if not row.get("price"):
        return None, "no price in snapshot (delisted? blocked?)"
    return row, None
