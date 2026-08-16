# Cross-Sectional Same-Sector Reversal Book

Generated: 2026-08-04 13:30:41  |  cost 3.8 bps/leg/side  |  long losers / short winners within sector, overlapping hold

| variant | REAL net | REAL gross | REAL bps/d | SCRAM gross (mean+-sd, 8 seeds) | z(real vs scram) | t(daily mean) |
|---------|----------|------------|------------|-------------------------------|------------------|--------------|
| rev vol-managed 5/10 |  -0.23 |   0.25 | +7.44 | +0.26 +- 1.08 | -0.01 | +0.34 |
| rev vol-managed wk 5/10 |  -0.87 |  -0.58 | -5.55 | -1.15 +- 1.72 | +0.33 | +0.00 |
| mom 20/20 |   0.87 |   0.98 | +118.91 | +0.18 +- 2.55 | +0.31 | +1.37 |
| rev 5/10 + mom 20/20 blend |   1.19 |   1.45 | +80.23 | -0.23 +- 1.78 | +0.95 | +2.02 |

Falsification: the honest comparison is on GROSS (costs cancel in real-minus-scrambled).  A positive deltaGross with the scrambled gross ~ 0 is the signal test.
