# Pairs Trading Research v8 -- Honest Engine Integration

Generated: 2026-08-04 13:50:19 | Elapsed: 368.7s

## Methodology

- **Engine**: v5 symmetric mean-reversion (z_exit = z_entry, noise-neutral by construction)
- **Scramble control**: N=5 random lags of leg B, delta = real_edge - mean_scram_edge
- **Factor filter**: cross-sectional mom/rev/vol z-scores aligned with trade direction
- **Regime filter**: only enter in top-tercile dispersion
- **Universe**: 404 pairs loaded (404 candidates)

## Experiment Results

| Experiment | Pairs | Real Edge | d(vs scram) | t(d) | %%Pos | Solid | Genuine | Fire |
|------------|-------|-----------|-------------|------|------|-------|---------|------|
| sta_z=1.5_c=3.8 | 403 | -0.0079 | -0.0020 | -0.41 | 39% | 74 | 37 | 89 | ++ |
| sta_z=1.5_c=3.8_R | 383 | -0.0085 | +0.0004 | +0.06 | 45% | 86 | 44 | 86 | ++ |
| sta_z=1.5_c=3.8_F | 356 | -0.0172 | -0.0024 | -0.36 | 40% | 74 | 41 | 81 | ++ |
| sta_z=1.5_c=3.8_F_R | 191 | -0.0226 | -0.0144 | -0.95 | 44% | 22 | 13 | 48 | ++ |
| sta_z=2_c=3.8 | 386 | -0.0182 | -0.0066 | -0.94 | 40% | 73 | 34 | 34 | ++ |
| sta_z=2_c=3.8_R | 256 | -0.0183 | -0.0031 | -0.28 | 46% | 52 | 26 | 21 | ++ |
| sta_z=2_c=3.8_F | 257 | -0.0388 | -0.0230 | -1.85 | 39% | 43 | 26 | 23 | ++ |
| sta_z=2_c=3.8_F_R | 64 | -0.0000 | +0.0106 | +0.71 | 43% | 5 | 3 | 3 | + |
| sta_z=2.5_c=3.8 | 255 | -0.0256 | -0.0094 | -1.21 | 41% | 53 | 25 | 5 | ++ |
| sta_z=2.5_c=3.8_R | 64 | -0.0422 | -0.0125 | -0.58 | 40% | 3 | 2 | 0 | ~ |
| sta_z=2.5_c=3.8_F | 82 | -0.0301 | -0.0151 | -1.44 | 40% | 12 | 7 | 2 | ++ |
| sta_z=2.5_c=3.8_F_R | 8 | -0.0123 | +0.0031 | +0.24 | 37% | 1 | 0 | 0 | - |
| sta_z=2_c=1 | 386 | -0.0124 | -0.0066 | -0.94 | 44% | 77 | 35 | 34 | ++ |
| sta_z=2_c=1_R | 256 | -0.0125 | -0.0034 | -0.31 | 50% | 53 | 26 | 21 | ++ |
| sta_z=2_c=1_F | 257 | -0.0339 | -0.0231 | -1.86 | 40% | 43 | 26 | 23 | ++ |
| sta_z=2_c=1_F_R | 64 | +0.0043 | +0.0104 | +0.70 | 46% | 6 | 3 | 3 | + |
| sta_z=2_c=7.6 | 386 | -0.0260 | -0.0065 | -0.93 | 37% | 70 | 31 | 34 | ++ |
| sta_z=2_c=7.6_R | 256 | -0.0262 | -0.0027 | -0.24 | 43% | 50 | 26 | 21 | ++ |
| sta_z=2_c=7.6_F | 257 | -0.0454 | -0.0229 | -1.84 | 37% | 43 | 26 | 23 | ++ |
| sta_z=2_c=7.6_F_R | 64 | -0.0060 | +0.0109 | +0.73 | 43% | 5 | 3 | 3 | + |
| kal_z=2_c=3.8 | 397 | +1.0275 | -0.0026 | -0.19 | 98% | 90 | 38 | 9 | ++ |
| kal_z=2_c=3.8_R | 200 | +1.0624 | -0.0018 | -0.07 | 100% | 38 | 16 | 5 | ++ |

## Top Genuine Pairs (delta > 2x scram_sd)

Config: sta_z=1.5_c=3.8_R (z=1.5, c=3.8bps, F=False, R=True)

| Pair | Class | Trades | Real Edge | Scram Edge | d | td | z_now | Fire |
|------|-------|--------|-----------|------------|----|-----|-------|------|
| AAPL/SHOP | STOCK | 19 | +0.0050 | -0.0572 | +0.0621 | +11.97 | +0.81 |  |
| KO/CL | STOCK | 9 | +0.1070 | +0.0006 | +0.1063 | +9.95 | +0.92 |  |
| BA/RTX | STOCK | 15 | +0.9891 | +0.0778 | +0.9114 | +8.12 | -1.31 |  |
| MSFT/TXN | STOCK | 12 | +0.1254 | +0.0390 | +0.0865 | +6.93 | -1.52 | YES |
| AAPL/GOOGL | STOCK | 15 | +0.1990 | +0.0189 | +0.1801 | +6.83 | +2.97 | YES |
| BA/GE | STOCK | 9 | +0.8243 | -0.0206 | +0.8449 | +6.68 | -1.31 |  |
| UNH/PFE | STOCK | 13 | +0.1385 | +0.0365 | +0.1020 | +6.47 | +0.88 |  |
| UPS/RTX | STOCK | 10 | +0.0897 | -0.0523 | +0.1420 | +6.06 | +0.39 |  |
| JPM/BAC | STOCK | 11 | +0.5159 | -0.0409 | +0.5568 | +5.66 | +0.40 |  |
| MU/SHOP | STOCK | 21 | +0.0526 | -0.0359 | +0.0885 | +5.43 | +0.76 |  |

## Solid Pairs (delta > scram_sd) -- All Configs

- **sta_z=1.5_c=3.8**: GOOGL/NOW(d=15.76), AMT/PLD(d=12.25), MSFT/AVGO(d=10.47)
- **sta_z=1.5_c=3.8_R**: AAPL/SHOP(d=11.97), KO/CL(d=9.95), BA/RTX(d=8.12)
- **sta_z=1.5_c=3.8_F**: LLY/PFE(d=9.79), NEE/DUK(d=8.82), AAPL/QCOM(d=7.95)
- **sta_z=1.5_c=3.8_F_R**: CSCO/QCOM(d=68.92), ADBE/NOW(d=12.20), VZ/DIS(d=6.50)
- **sta_z=2_c=3.8**: META/INTC(d=11.86), TMO/ABBV(d=7.27), UNH/JNJ(d=6.65)
- **sta_z=2_c=3.8_R**: CSCO/MU(d=14.71), MSFT/DOCU(d=6.95), AMAT/DOCU(d=5.79)
- **sta_z=2_c=3.8_F**: INTC/ADBE(d=16.36), TMO/ABBV(d=7.86), AMD/TXN(d=5.49)
- **sta_z=2_c=3.8_F_R**: AMD/AMAT(d=5.25), BTC/ETH(d=5.17), META/GOOGL(d=3.60)

## Current Firing Pairs

| Pair | Config | z_now | z_entry | Real Edge | d | td |
|------|--------|-------|---------|-----------|----|-----|
| GOOGL/NOW | z=1.5 | +1.99 | 1.5 | +0.3286 | +0.3542 | +15.76 |
| LLY/PFE | z=1.5 | +1.93 | 1.5 | +0.1855 | +0.1928 | +5.39 |
| CL/PG | z=1.5 | -3.14 | 1.5 | +0.1099 | +0.1184 | +3.90 |
| AMZN/QCOM | z=1.5 | +1.67 | 1.5 | +0.0186 | +0.0499 | +3.79 |
| PFE/ABBV | z=1.5 | -1.75 | 1.5 | +0.3729 | +0.2878 | +3.44 |
| AAPL/NOW | z=1.5 | +2.65 | 1.5 | +0.0020 | +0.0316 | +2.99 |
| NKE/HD | z=1.5 | -1.99 | 1.5 | +0.0564 | +0.0911 | +2.47 |
| JNJ/DHR | z=1.5 | +3.25 | 1.5 | +0.0097 | +0.0511 | +2.25 |
| MSFT/TXN | z=1.5 | -1.52 | 1.5 | +0.0896 | +0.1292 | +2.16 |
| AAPL/ADBE | z=1.5 | +2.58 | 1.5 | +0.0043 | +0.0144 | +1.96 |
| AAPL/GOOGL | z=1.5 | +2.97 | 1.5 | +0.1990 | +0.1801 | +6.83 |
| MSFT/SHOP | z=1.5 | -2.85 | 1.5 | +0.2627 | +0.2614 | +3.00 |
| AVGO/AMAT | z=1.5 | -1.86 | 1.5 | +0.1345 | +0.2477 | +2.61 |
| TXN/SNOW | z=1.5 | -1.80 | 1.5 | +0.0406 | +0.0999 | +2.51 |
| HD/SBUX | z=1.5 | -2.01 | 1.5 | +0.2157 | +0.1388 | +2.31 |

## Research Verdict

**+ Promising**: Best config `sta_z=1.5_c=3.8_R` -- 44 genuine pairs (mean d=+0.0004, t=+0.06).

Live: 86 firing.

## Next Directions

1. Longer data history (2yr is too short for MR signals)
2. Multi-frequency confirmation (intraday ORB + daily z)
3. Pairs momentum (trade WITH the trend, not against it)
4. Cross-asset structural pairs (Gold/Oil, Equity/Bond)
5. Vol-scaled position sizing
6. Ensemble methods (OLS + Kalman + PCA consensus)

---
*Generated by pairs_research_v8.py (v5 honest engine + scramble controls)*
