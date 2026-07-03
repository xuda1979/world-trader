"""world-trader market intelligence package.

Modules:
  core      -- HTTP, keys, CJK-aware formatting, freshness, shared dataclasses
  sources   -- price/quote fetchers across many free providers (cross-checked)
  news      -- expanded RSS/news + GDELT tone
  altdata   -- FRED macro, CFTC COT, crypto funding/OI, fear&greed, yield curve
  instruments -- instrument universe (equities, futures, FX, rates, commodities)
  analysis  -- technicals, regime, relative strength, R:R scoring, composite rank
  report    -- assembles the full snapshot

Objective: surface short-term, defined-risk, high reward:risk trade ideas.
"""
__all__ = ["core", "sources", "news", "altdata", "instruments", "analysis", "report"]
