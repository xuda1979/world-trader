# C1_kfindustry — Ken French daily portfolio cross-sections (NEW DOMAIN)

Mission: mine KF daily portfolios (1926+, 48/49 industries, 25 size-value, 10 momentum deciles,
6 size-factor, ME deciles) for high-SR cross-sectional/TS engines that pass ALL gates.
These are diversified portfolio returns (like ETFs) — treat 6bps as realistic cost.

IDEAS (in order):
1. Industry-momentum: rank 48 VW industry returns over 21d/63d/126d/252d, hold top3-bottom3
   (long winners/short losers, EW), rebalance weekly/daily. Cross-sectional z-score version.
2. Industry mean-reversion: 5d/10d/21d reversal within industries; vol-normalized rank version.
3. Size (ME deciles/25ff): TS momentum on small-vs-big spreads (SMB-like timing), 5x5 value
   spread timing (HML proxies from HiBM-LoBM legs).
4. Momentum-decile (10 prior 12-2): time-series momentum on decile spreads; winner-minus-loser
   daily book with vol-scaling per decile.
5. 6-portfolio 2x3: size x momentum legs as sleeves; BM spread timing.
6. EW-vs-VW industry spread: divergence between EW and VW 48-industry returns as a
   breadth/crowding signal (long EW when dispersion low, etc.).
7. Combine best 2-3 sub-engines into one composite sleeve if individually weak (document!).

NOTES:
- Use VW returns primarily (more tradeable); EW as breadth signal.
- -99.99 = missing -> NaN -> dropna or ffill limited; 1926-1962 sparse (some industries missing).
- Start backtest 1963+ or 2008+; report BOTH. For the campaign the 2006/2008+ window matters most.
- Portfolio returns of long-short legs (e.g. decile spreads) have no per-leg cost; charge
  6bps on the resulting position changes (top3-bottom3 EW book turnover).

HONESTY: All gates in GOAL100_AGENT_BRIEF.md. Corr gate vs CURRENT BLEND mandatory.
