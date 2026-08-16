# Pairs Trading Research

Generated: 2026-08-04 11:31:03 CST | Elapsed: 119.2s

## v2 Improvements

1. **Kalman filter dynamic hedge ratio** - time-varying beta vs static OLS
2. **Engle-Granger cointegration test** - statistical filter (p<0.10)
3. **FX-specific qualification gates** - IS edge>=0.30 (vs 0.60), OOS cap<=5.0 (vs 3.0)
4. **FDR qualification** (BH) vs Bonferroni
5. **Half-life calibration** per pair
6. **VIX regime filter**
7. **Systematic screening** - all same-sector pairs

## Universe: 404 pairs

## BASELINE (static OLS): 6 Bonf / 6 FDR (FX: 0)

| Pair | Cls | n | edge | t | OOS n | OOS edge | HL | z_now | Fire | Bonf | FDR | EG |
|------|-----|---|------|---|-------|----------|----|-------|------|------|-----|----|
| CRM/SHOP | STOCK | 57 | +0.680 | 5.13 | 19 | +1.402 | 93 | -0.72 |  | YES | YES |  |
| NKE/HD | STOCK | 59 | +0.775 | 5.95 | 23 | +1.189 | 150 | -1.25 |  | YES | YES | C |
| UPS/RTX | STOCK | 54 | +0.726 | 5.34 | 23 | +0.932 | 114 | -1.44 |  | YES | YES |  |
| MSFT/AMZN | STOCK | 58 | +0.732 | 5.58 | 26 | +0.727 | 71 | +0.35 |  | YES | YES |  |
| NOW/DOCU | STOCK | 61 | +0.655 | 5.12 | 21 | +0.601 | 19 | -1.07 |  | YES | YES |  |
| QQQ/IWM | ETF | 62 | +0.752 | 5.92 | 25 | +0.573 | 36 | -1.32 |  | YES | YES | C |
| CRM/ADBE | STOCK | 36 | +1.171 | 7.03 | 11 | +3.639 | 40 | -0.41 |  |  |  |  |
| PLTR/SHOP | STOCK | 50 | +0.550 | 3.89 | 15 | +2.278 | 67 | -0.65 |  |  |  | C |
| ADBE/PLTR | STOCK | 52 | +0.332 | 2.39 | 12 | +2.235 | 112 | +0.13 |  |  |  |  |
| CRM/PLTR | STOCK | 54 | +0.271 | 1.99 | 11 | +2.029 | 124 | -0.13 |  |  |  |  |
| MSFT/PLTR | STOCK | 46 | +0.264 | 1.79 | 12 | +1.783 | 79 | -0.12 |  |  |  |  |
| JNJ/AMGN | STOCK | 54 | +0.610 | 4.48 | 19 | +1.676 | 84 | +0.90 |  |  |  |  |
| SBUX/COST | STOCK | 62 | +0.030 | 0.24 | 23 | +1.459 | 20 | +0.97 |  |  |  | C |
| ADBE/SHOP | STOCK | 58 | +0.318 | 2.42 | 24 | +1.403 | 87 | -0.53 |  |  |  |  |
| DHR/TMO | STOCK | 52 | +0.119 | 0.86 | 11 | +1.275 | 80 | -3.51 | * |  |  |  |
| NOW/PLTR | STOCK | 82 | +0.094 | 0.85 | 32 | +1.249 | 157 | -0.16 |  |  |  |  |
| AAPL/NVDA | STOCK | 42 | +0.167 | 1.08 | 20 | +1.115 | 37 | +1.56 |  |  |  |  |
| WFC/SCHW | STOCK | 51 | +0.229 | 1.64 | 21 | +0.993 | 13 | -0.78 |  |  |  | C |
| PLTR/DOCU | STOCK | 73 | +0.318 | 2.72 | 23 | +0.912 | 138 | -1.06 |  |  |  | C |
| MSFT/ORCL | STOCK | 72 | +0.308 | 2.61 | 35 | +0.879 | 35 | +2.01 | * |  |  | C |
| ABBV/DHR | STOCK | 85 | -0.016 | -0.15 | 29 | +0.875 | 98 | +1.49 |  |  |  |  |
| BAC/SCHW | STOCK | 57 | +0.663 | 5.01 | 18 | +0.857 | 32 | +0.72 |  |  |  |  |
| TMO/ABBV | STOCK | 73 | +0.172 | 1.47 | 22 | +0.831 | 55 | +0.30 |  |  |  |  |
| AMZN/AVGO | STOCK | 38 | +0.399 | 2.46 | 9 | +0.827 | 71 | +0.40 |  |  |  | C |
| AMZN/PLTR | STOCK | 58 | +0.056 | 0.42 | 14 | +0.815 | 78 | -0.29 |  |  |  |  |

## HALF-LIFE (static OLS): 12 Bonf / 12 FDR (FX: 0)

| Pair | Cls | n | edge | t | OOS n | OOS edge | HL | z_now | Fire | Bonf | FDR | EG |
|------|-----|---|------|---|-------|----------|----|-------|------|------|-----|----|
| AMZN/AVGO | STOCK | 24 | +1.011 | 4.95 | 12 | +2.814 | 71 | +0.05 |  | YES | YES | C |
| NOW/DOCU | STOCK | 62 | +1.128 | 8.88 | 21 | +1.900 | 19 | -1.14 |  | YES | YES |  |
| GS/MS | STOCK | 34 | +1.529 | 8.91 | 28 | +1.551 | 39 | -0.66 |  | YES | YES | C |
| JPM/SCHW | STOCK | 60 | +0.706 | 5.47 | 26 | +0.958 | 18 | -0.47 |  | YES | YES | C |
| LLY/PFE | STOCK | 68 | +0.871 | 7.18 | 31 | +0.944 | 42 | +1.40 |  | YES | YES |  |
| NVDA/TXN | STOCK | 42 | +0.763 | 4.94 | 23 | +0.916 | 48 | -0.80 |  | YES | YES |  |
| NVDA/PLTR | STOCK | 44 | +0.789 | 5.23 | 33 | +0.831 | 68 | +0.79 |  | YES | YES |  |
| AVGO/QCOM | STOCK | 47 | +0.656 | 4.50 | 34 | +0.799 | 80 | +0.12 |  | YES | YES |  |
| AAPL/GOOGL | STOCK | 63 | +0.696 | 5.52 | 30 | +0.725 | 148 | +2.25 | * | YES | YES | C |
| DIS/CMCSA | STOCK | 31 | +0.887 | 4.94 | 25 | +0.698 | 156 | +1.35 |  | YES | YES |  |
| TXN/QCOM | STOCK | 59 | +1.010 | 7.76 | 35 | +0.622 | 51 | +0.94 |  | YES | YES |  |
| TXN/PLTR | STOCK | 59 | +0.692 | 5.32 | 38 | +0.483 | 82 | +1.05 |  | YES | YES |  |
| MSFT/PLTR | STOCK | 23 | +2.527 | 12.12 | 7 | +10.314 | 79 | +0.55 |  |  |  |  |
| JNJ/MRK | STOCK | 51 | +0.659 | 4.70 | 15 | +8.878 | 49 | -1.03 |  |  |  |  |
| TMO/ABBV | STOCK | 56 | +0.123 | 0.92 | 18 | +8.584 | 55 | -0.38 |  |  |  |  |
| SBUX/TJX | STOCK | 59 | +0.494 | 3.80 | 19 | +6.048 | 56 | +0.94 |  |  |  | C |
| T/CMCSA | STOCK | 68 | +0.147 | 1.21 | 20 | +5.470 | 121 | +1.92 |  |  |  |  |
| PLTR/SHOP | STOCK | 48 | +0.917 | 6.36 | 24 | +4.868 | 67 | -0.83 |  |  |  | C |
| AMZN/NVDA | STOCK | 47 | +0.323 | 2.21 | 14 | +4.628 | 44 | -0.16 |  |  |  | C |
| JNJ/AMGN | STOCK | 57 | -0.175 | -1.32 | 14 | +4.431 | 84 | +1.29 |  |  |  |  |
| BAC/SCHW | STOCK | 68 | +0.227 | 1.87 | 24 | +4.092 | 32 | +0.98 |  |  |  |  |
| NOW/SHOP | STOCK | 53 | +0.332 | 2.41 | 19 | +3.977 | 141 | -0.65 |  |  |  |  |
| SBUX/TGT | STOCK | 54 | +0.466 | 3.43 | 18 | +3.754 | 28 | -0.55 |  |  |  | C |
| GE/UPS | STOCK | 66 | +0.314 | 2.55 | 24 | +3.603 | 147 | +0.12 |  |  |  |  |
| NVDA/AVGO | STOCK | 37 | +1.726 | 10.50 | 19 | +3.159 | 29 | +0.61 |  |  |  | C |

## +REGIME (static OLS): 14 Bonf / 14 FDR (FX: 0)

| Pair | Cls | n | edge | t | OOS n | OOS edge | HL | z_now | Fire | Bonf | FDR | EG |
|------|-----|---|------|---|-------|----------|----|-------|------|------|-----|----|
| AMZN/AVGO | STOCK | 24 | +1.011 | 4.95 | 12 | +2.814 | 71 | +0.05 |  | YES | YES | C |
| NOW/DOCU | STOCK | 62 | +1.128 | 8.88 | 21 | +1.900 | 19 | -1.14 |  | YES | YES |  |
| GS/MS | STOCK | 29 | +1.396 | 7.52 | 28 | +1.551 | 39 | -0.66 |  | YES | YES | C |
| WFC/SCHW | STOCK | 43 | +0.886 | 5.81 | 17 | +1.076 | 13 | -1.40 |  | YES | YES | C |
| JPM/SCHW | STOCK | 60 | +0.706 | 5.47 | 26 | +0.958 | 18 | -0.47 |  | YES | YES | C |
| LLY/PFE | STOCK | 52 | +1.424 | 10.27 | 31 | +0.944 | 42 | +1.40 |  | YES | YES |  |
| NVDA/TXN | STOCK | 42 | +0.763 | 4.94 | 23 | +0.916 | 48 | -0.80 |  | YES | YES |  |
| GOOGL/PLTR | STOCK | 54 | +0.872 | 6.41 | 42 | +0.856 | 66 | +0.48 |  | YES | YES |  |
| NVDA/PLTR | STOCK | 44 | +0.789 | 5.23 | 33 | +0.831 | 68 | +0.79 |  | YES | YES |  |
| AVGO/QCOM | STOCK | 47 | +0.656 | 4.50 | 34 | +0.799 | 80 | +0.12 |  | YES | YES |  |
| AAPL/GOOGL | STOCK | 63 | +0.696 | 5.52 | 30 | +0.725 | 148 | +2.25 | * | YES | YES | C |
| DIS/CMCSA | STOCK | 31 | +0.887 | 4.94 | 25 | +0.698 | 156 | +1.35 |  | YES | YES |  |
| TXN/QCOM | STOCK | 59 | +1.010 | 7.76 | 35 | +0.622 | 51 | +0.94 |  | YES | YES |  |
| TXN/PLTR | STOCK | 55 | +0.731 | 5.42 | 38 | +0.483 | 82 | +1.05 |  | YES | YES |  |
| MSFT/PLTR | STOCK | 23 | +2.527 | 12.12 | 7 | +10.314 | 79 | +0.55 |  |  |  |  |
| JNJ/MRK | STOCK | 43 | +0.810 | 5.31 | 15 | +8.878 | 49 | -1.03 |  |  |  |  |
| TMO/ABBV | STOCK | 52 | +0.124 | 0.89 | 18 | +8.584 | 55 | -0.38 |  |  |  |  |
| SBUX/TJX | STOCK | 41 | +1.401 | 8.97 | 19 | +6.048 | 56 | +0.94 |  |  |  | C |
| T/CMCSA | STOCK | 68 | +0.147 | 1.21 | 20 | +5.470 | 121 | +1.92 |  |  |  |  |
| PLTR/SHOP | STOCK | 35 | +1.937 | 11.46 | 24 | +4.868 | 67 | -0.83 |  |  |  | C |
| AMZN/NVDA | STOCK | 47 | +0.323 | 2.21 | 14 | +4.628 | 44 | -0.16 |  |  |  | C |
| JNJ/AMGN | STOCK | 51 | -0.315 | -2.25 | 14 | +4.431 | 84 | +1.29 |  |  |  |  |
| BAC/SCHW | STOCK | 56 | +0.198 | 1.48 | 24 | +4.092 | 32 | +0.98 |  |  |  |  |
| NOW/SHOP | STOCK | 53 | +0.332 | 2.41 | 19 | +3.977 | 141 | -0.65 |  |  |  |  |
| SBUX/TGT | STOCK | 54 | +0.466 | 3.43 | 18 | +3.754 | 28 | -0.55 |  |  |  | C |

## HALF-LIFE (Kalman): 63 Bonf / 63 FDR (FX: 0)

| Pair | Cls | n | edge | t | OOS n | OOS edge | HL | z_now | Fire | Bonf | FDR | EG |
|------|-----|---|------|---|-------|----------|----|-------|------|------|-----|----|
| ABBV/AMGN | STOCK | 23 | +1.602 | 7.68 | 12 | +2.998 | 24 | -0.16 |  | YES | YES | C |
| ABT/MRK | STOCK | 24 | +2.905 | 14.23 | 12 | +2.967 | 200 | +0.17 |  | YES | YES | C |
| NKE/HD | STOCK | 26 | +1.945 | 9.92 | 10 | +2.918 | 150 | -0.81 |  | YES | YES | C |
| META/INTC | STOCK | 28 | +2.921 | 15.46 | 14 | +2.847 | 200 | -0.48 |  | YES | YES | C |
| META/DOCU | STOCK | 23 | +2.666 | 12.79 | 16 | +2.835 | 94 | -0.21 |  | YES | YES | C |
| QQQ/DIA | STOCK | 28 | +2.757 | 14.59 | 18 | +2.823 | 76 | +0.80 |  | YES | YES | C |
| META/ORCL | STOCK | 24 | +2.284 | 11.19 | 14 | +2.791 | 47 | -0.55 |  | YES | YES | C |
| AMZN/MU | STOCK | 21 | +2.740 | 12.56 | 11 | +2.789 | 200 | -1.06 |  | YES | YES | C |
| META/AVGO | STOCK | 22 | +2.468 | 11.57 | 15 | +2.787 | 123 | -0.60 |  | YES | YES | C |
| AAPL/GOOGL | STOCK | 24 | +1.730 | 8.47 | 11 | +2.782 | 148 | +0.07 |  | YES | YES | C |
| ADBE/AMAT | STOCK | 24 | +2.647 | 12.97 | 18 | +2.773 | 200 | -1.47 |  | YES | YES | C |
| AMT/PLD | STOCK | 26 | +2.750 | 14.02 | 14 | +2.755 | 200 | -0.04 |  | YES | YES | C |
| CRM/AMAT | STOCK | 25 | +2.744 | 13.72 | 17 | +2.736 | 200 | -1.56 |  | YES | YES | C |
| META/SNOW | STOCK | 28 | +2.535 | 13.41 | 17 | +2.715 | 55 | -0.32 |  | YES | YES | C |
| SPY/DIA | ETF | 25 | +2.034 | 10.17 | 17 | +2.700 | 38 | +0.39 |  | YES | YES | C |
| SBUX/WMT | STOCK | 22 | +2.492 | 11.69 | 10 | +2.699 | 63 | -0.19 |  | YES | YES | C |
| META/QCOM | STOCK | 26 | +2.404 | 12.26 | 15 | +2.686 | 28 | -0.27 |  | YES | YES | C |
| META/CSCO | STOCK | 24 | +2.813 | 13.78 | 17 | +2.668 | 200 | -0.27 |  | YES | YES | C |
| MCD/TGT | STOCK | 24 | +2.275 | 11.15 | 20 | +2.665 | 79 | +0.00 |  | YES | YES | C |
| QQQ/IWM | ETF | 20 | +2.844 | 12.72 | 15 | +2.600 | 36 | +0.23 |  | YES | YES | C |
| TJX/WMT | STOCK | 32 | +2.511 | 14.21 | 17 | +2.585 | 27 | +0.01 |  | YES | YES | C |
| META/TXN | STOCK | 23 | +2.341 | 11.23 | 12 | +2.579 | 86 | -0.41 |  | YES | YES | C |
| CRM/MU | STOCK | 24 | +2.486 | 12.18 | 16 | +2.571 | 200 | -1.66 |  | YES | YES | C |
| META/CRM | STOCK | 23 | +2.480 | 11.89 | 14 | +2.558 | 141 | -0.29 |  | YES | YES | C |
| AMZN/AMAT | STOCK | 22 | +1.563 | 7.33 | 11 | +2.557 | 200 | -0.66 |  | YES | YES | C |

## +REGIME (Kalman): 45 Bonf / 45 FDR (FX: 0)

| Pair | Cls | n | edge | t | OOS n | OOS edge | HL | z_now | Fire | Bonf | FDR | EG |
|------|-----|---|------|---|-------|----------|----|-------|------|------|-----|----|
| ABT/MRK | STOCK | 24 | +2.905 | 14.23 | 12 | +2.967 | 200 | +0.17 |  | YES | YES | C |
| NKE/HD | STOCK | 23 | +2.440 | 11.70 | 10 | +2.918 | 150 | -0.81 |  | YES | YES | C |
| META/INTC | STOCK | 24 | +3.232 | 15.83 | 14 | +2.847 | 200 | -0.48 |  | YES | YES | C |
| QQQ/DIA | STOCK | 25 | +2.899 | 14.49 | 18 | +2.823 | 76 | +0.80 |  | YES | YES | C |
| META/ORCL | STOCK | 21 | +2.138 | 9.80 | 14 | +2.791 | 47 | -0.55 |  | YES | YES | C |
| AMZN/MU | STOCK | 20 | +2.683 | 12.00 | 11 | +2.789 | 200 | -1.06 |  | YES | YES | C |
| ADBE/AMAT | STOCK | 24 | +2.647 | 12.97 | 18 | +2.773 | 200 | -1.47 |  | YES | YES | C |
| AMT/PLD | STOCK | 24 | +3.044 | 14.91 | 14 | +2.755 | 200 | -0.04 |  | YES | YES | C |
| CRM/AMAT | STOCK | 25 | +2.744 | 13.72 | 17 | +2.736 | 200 | -1.56 |  | YES | YES | C |
| META/SNOW | STOCK | 24 | +2.812 | 13.78 | 17 | +2.715 | 55 | -0.32 |  | YES | YES | C |
| SPY/DIA | ETF | 22 | +2.599 | 12.19 | 17 | +2.700 | 38 | +0.39 |  | YES | YES | C |
| META/QCOM | STOCK | 22 | +2.416 | 11.33 | 15 | +2.686 | 28 | -0.27 |  | YES | YES | C |
| META/CSCO | STOCK | 23 | +2.934 | 14.07 | 17 | +2.668 | 200 | -0.27 |  | YES | YES | C |
| MCD/TGT | STOCK | 23 | +2.588 | 12.41 | 20 | +2.665 | 79 | +0.00 |  | YES | YES | C |
| TJX/WMT | STOCK | 30 | +2.850 | 15.61 | 17 | +2.585 | 27 | +0.01 |  | YES | YES | C |
| META/TXN | STOCK | 22 | +2.286 | 10.72 | 12 | +2.579 | 86 | -0.41 |  | YES | YES | C |
| CRM/MU | STOCK | 24 | +2.486 | 12.18 | 16 | +2.571 | 200 | -1.66 |  | YES | YES | C |
| META/CRM | STOCK | 21 | +2.500 | 11.46 | 14 | +2.558 | 141 | -0.29 |  | YES | YES | C |
| AMZN/AMAT | STOCK | 21 | +1.570 | 7.19 | 11 | +2.557 | 200 | -0.66 |  | YES | YES | C |
| VZ/DIS | STOCK | 21 | +1.876 | 8.60 | 17 | +2.503 | 50 | +0.12 |  | YES | YES | C |
| ADBE/MU | STOCK | 21 | +2.414 | 11.06 | 17 | +2.489 | 200 | -1.49 |  | YES | YES | C |
| SPY/QQQ | ETF | 30 | +2.365 | 12.95 | 24 | +2.474 | 126 | -1.08 |  | YES | YES | C |
| INTC/MU | STOCK | 35 | +2.525 | 14.94 | 14 | +2.455 | 15 | -0.81 |  | YES | YES | C |
| META/MU | STOCK | 22 | +2.502 | 11.74 | 15 | +2.416 | 200 | -0.81 |  | YES | YES | C |
| COST/WMT | STOCK | 20 | +2.205 | 9.86 | 14 | +2.346 | 111 | +0.88 |  | YES | YES | C |


## Cross-Experiment Summary

| Experiment | OK | Bonf | FDR | FX Qual | EG Coint |
|------------|----|------|-----|---------|----------|
| BASELINE (static OLS) | 404 | 6 | 6 | 0 | 119 |
| HALF-LIFE (static OLS) | 402 | 12 | 12 | 0 | 119 |
| +REGIME (static OLS) | 402 | 14 | 14 | 0 | 119 |
| HALF-LIFE (Kalman) | 337 | 63 | 63 | 0 | 100 |
| +REGIME (Kalman) | 268 | 45 | 45 | 0 | 76 |

### Live Pairs (FDR qual, Kalman spread)

| Pair | Cls | OOS edge | HL | z_now | Firing | EG coint |
|------|-----|----------|----|-------|--------|----------|
| ABBV/AMGN | STOCK | +2.998 | 24 | -0.16 |  | YES |
| ABT/MRK | STOCK | +2.967 | 200 | +0.17 |  | YES |
| NKE/HD | STOCK | +2.918 | 150 | -0.81 |  | YES |
| META/INTC | STOCK | +2.847 | 200 | -0.48 |  | YES |
| META/DOCU | STOCK | +2.835 | 94 | -0.21 |  | YES |
| QQQ/DIA | STOCK | +2.823 | 76 | +0.80 |  | YES |
| META/ORCL | STOCK | +2.791 | 47 | -0.55 |  | YES |
| AMZN/MU | STOCK | +2.789 | 200 | -1.06 |  | YES |
| META/AVGO | STOCK | +2.787 | 123 | -0.60 |  | YES |
| AAPL/GOOGL | STOCK | +2.782 | 148 | +0.07 |  | YES |
| ADBE/AMAT | STOCK | +2.773 | 200 | -1.47 |  | YES |
| AMT/PLD | STOCK | +2.755 | 200 | -0.04 |  | YES |
| CRM/AMAT | STOCK | +2.736 | 200 | -1.56 |  | YES |
| META/SNOW | STOCK | +2.715 | 55 | -0.32 |  | YES |
| SPY/DIA | ETF | +2.700 | 38 | +0.39 |  | YES |

## Cointegration Analysis (EG test, p<0.10)

**100/337 pairs are cointegrated (p<0.10 EG test)**

| Pair | ADF stat | p-value | OOS edge | Qualifies |
|------|----------|---------|----------|----------|
| SBUX/TGT | -4.436 | 0.0050 | +3.159 |  |
| INTC/CSCO | -3.796 | 0.0050 | +3.997 |  |
| INTC/MU | -3.731 | 0.0050 | +2.455 | YES |
| META/ORCL | -3.692 | 0.0050 | +2.791 | YES |
| IWM/DIA | -3.603 | 0.0050 | +3.082 |  |
| WFC/SCHW | -3.586 | 0.0050 | +1.578 | YES |
| LLY/AMGN | -3.585 | 0.0050 | +0.952 | YES |
| META/SNOW | -3.526 | 0.0050 | +2.715 | YES |
| SO/DUK | -3.522 | 0.0050 | +1.662 | YES |
| AAPL/MU | -3.484 | 0.0050 | +1.584 | YES |
| EUR/GBP | -3.462 | 0.0050 | +0.311 |  |
| ADBE/CSCO | -3.435 | 0.0050 | +2.068 | YES |
| GE/RTX | -3.432 | 0.0050 | +0.956 | YES |
| MS/BAC | -3.426 | 0.0103 | +0.914 |  |
| GS/BAC | -3.419 | 0.0108 | +1.171 | YES |
| AAPL/GOOGL | -3.269 | 0.0213 | +2.782 | YES |
| META/PLTR | -3.243 | 0.0231 | +1.000 |  |
| NVDA/AVGO | -3.236 | 0.0236 | +2.682 |  |
| AAPL/AMD | -3.192 | 0.0267 | +1.002 | YES |
| PFE/TMO | -3.181 | 0.0275 | +2.257 | YES |
| AAPL/INTC | -3.138 | 0.0305 | +2.246 | YES |
| META/SHOP | -3.137 | 0.0305 | +3.292 |  |
| META/TXN | -3.113 | 0.0323 | +2.579 | YES |
| INTC/AMAT | -3.105 | 0.0328 | +1.277 |  |
| META/NVDA | -3.104 | 0.0329 | +2.295 | YES |
