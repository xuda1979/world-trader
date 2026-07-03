# Trade Scout -- Worked Example

This is an illustrative, fabricated walkthrough showing the expected output
shape and reasoning. Numbers are made up; do not trade off them.

## Inputs (Phase 1)
- Universe: large-cap US equities + liquid crypto majors
- Horizon: swing (2-10 days)
- Account: $50,000, risk 1% per trade ($500 max loss/idea)
- Constraints: long or short, no options, no leverage

## Filtering (Phase 3)
Started with 40 screened names, kept 3 that cleared all gates
(liquidity, definable stop, R:R >= 2:1, >= 3 confluent signals).

## Report (Phase 5)

```
#1 ACME -- Long | Swing | Score: 82/100
Thesis      : Post-earnings breakout above multi-month resistance on strong volume.
Catalyst    : Beat-and-raise earnings 2 days ago; analyst upgrades following.
Entry       : Buy on hold above 152.00 (prior resistance turned support).
Stop        : 147.50 (below breakout base + 1xATR). Risk = $4.50/share.
Target(s)   : T1 161 (measured move), T2 168 (next supply zone).
Reward:Risk : T1 = 2.0:1, T2 = 3.6:1.
Size        : $500 / $4.50 = 111 shares (~$16.9k notional, 34% of acct).
Signals     : breakout+volume, earnings beat, RS vs sector, 2 upgrades.
Sources     : [earnings PR, date], [exchange volume, date], [analyst notes, date].
Risks       : market-wide risk-off; gap below stop. Confidence: Medium.
```

```
#2 BETACOIN -- Long | Swing | Score: 74/100
Thesis      : Reclaim of key level ahead of protocol upgrade catalyst.
Catalyst    : Network upgrade scheduled in 6 days.
Entry       : Above 2.10 reclaim.
Stop        : 1.96 (below reclaim wick). Risk = $0.14.
Target(s)   : T1 2.40, T2 2.65.
Reward:Risk : T1 = 2.1:1, T2 = 3.9:1.
Size        : $500 / $0.14 = ~3,571 units.
Signals     : level reclaim, rising funding-neutral, upgrade catalyst.
Sources     : [project blog, date], [exchange data, date].
Risks       : crypto-wide drawdown; upgrade delay. Confidence: Low-Medium.
```

### Summary table
| # | Ticker   | Dir  | R:R (T2) | Score |
|---|----------|------|----------|-------|
| 1 | ACME     | Long | 3.6:1    | 82    |
| 2 | BETACOIN | Long | 3.9:1    | 74    |

### Portfolio note
ACME (equity) and BETACOIN (crypto) are weakly correlated; both are long, so
both lose in a broad risk-off. Total risk if both taken = $1,000 (2% of
account) -- within budget. Do not add a third correlated long.

*Research only, not financial advice. Verify live prices before acting.*
