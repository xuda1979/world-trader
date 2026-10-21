# Pair Trading Scorecard (multi-aspect, falsification-first)

Generated: 2026-08-04 12:42:54  |  cost 3.8 bps RT  |  404 pairs scored, 47 pass the EDGE gate

Aspects (0-100): **EDGE** (gate: OOS edge must beat scrambled control AND t>0.5), **EFFECT** (OOS per-trade sigma), **ROBUST** (IS/OOS consistency + sample), **COST** (cost drag vs gross edge), **LIQ** (dollar volume), **RISK** (worst trade + maxDD), **STRUCT** (half-life + EG), **FREQ** (trades/yr).  Composite = weighted geometric mean, zeroed if EDGE gate fails.

## Part A -- strategy-level

| strategy | EDGE | ROBUST | COST | EXEC | RISK | DATA | FREQ | note |
|----------|------|--------|------|------|------|------|------|------|
| v4 daily z=2 (artifact) | 10 | 5 | 85 | 90 | 20 | 30 | 70 | Sharpe 9.75 real vs 7.9 scrambled -- 90% artifact, RETRACTED |
| v5 daily z=2.0 | 5 | 8 | 88 | 90 | 40 | 30 | 55 | real ~= scrambled ~= 0 (t-stat +0.15) |
| v5 daily z=1.5 | 5 | 8 | 85 | 90 | 35 | 30 | 65 | real ~= scrambled ~= 0 |
| v5 long-horizon (250d z) | 3 | 5 | 80 | 80 | 20 | 25 | 45 | real +0.97 but scrambled +1.19 -- artifact |
| v5 intraday 5-min | 0 | 5 | 10 | 40 | 30 | 25 | 90 | per-trade net -0.25 real / -0.20 scrambled: cost floor |
| BTC/ETH daily | 2 | 5 | 40 | 70 | 30 | 60 | 50 | real -0.10 vs scrambled +0.03 |
| ETF pairs daily (1k bars) | 2 | 6 | 60 | 85 | 30 | 60 | 50 | real -0.13 vs scrambled -0.10 |

## Part B -- top-40 pairs by composite

| # | pair | comp | EDGE | EFF | ROB | COST | LIQ | RISK | STR | FREQ | expOOS | tOOS | delta |
|---|------|------|------|-----|-----|------|-----|------|-----|------|--------|------|-------|
| 1 | LLY/MRK |  76.4 |   98 |   54 |   38 |   93 |   88 |  100 |  100 |   92 | +0.27 | +3.94 | +0.384 |
| 2 | ABBV/AMGN |  66.1 |   60 |   54 |   48 |   87 |   78 |  100 |   70 |  100 | +0.27 | +2.61 | +0.174 |
| 3 | NVDA/CSCO |  60.3 |   37 |   56 |   60 |   91 |  100 |   83 |   70 |  100 | +0.28 | +1.80 | +0.246 |
| 4 | MU/AMD |  51.6 |   34 |   34 |   38 |   94 |  100 |  100 |   70 |   92 | +0.17 | +1.68 | +0.180 |
| 5 | CSCO/ARM |  47.6 |   31 |   23 |   55 |   88 |   80 |  100 |   40 |  100 | +0.12 | +1.58 | +0.182 |
| 6 | NOW/DOCU |  44.4 |   30 |   25 |   32 |   84 |   81 |  100 |   70 |   77 | +0.12 | +1.54 | +0.101 |
| 7 | NKE/HD |  40.6 |   19 |   32 |   35 |   84 |   76 |  100 |   70 |   84 | +0.16 | +1.15 | +0.189 |
| 8 | NKE/TGT |  39.5 |   18 |   16 |   62 |   78 |   76 |  100 |   70 |  100 | +0.08 | +1.14 | +0.060 |
| 9 | JPM/MS |  37.5 |   17 |   15 |   55 |   67 |   85 |  100 |   70 |  100 | +0.07 | +1.09 | +0.121 |
| 10 | AMZN/NVDA |  37.3 |   13 |   33 |   35 |   83 |  100 |   89 |   70 |   84 | +0.17 | +0.96 | +0.089 |
| 11 | NOW/SNOW |  37.0 |   15 |   18 |   58 |   82 |   81 |  100 |   40 |  100 | +0.09 | +1.03 | +0.183 |
| 12 | IWM/GLD |  36.1 |   11 |   23 |   65 |   76 |   98 |   86 |   70 |  100 | +0.12 | +0.87 | +0.225 |
| 13 | JNJ/AMGN |  31.7 |    9 |   35 |   31 |   75 |   80 |   89 |   70 |   77 | +0.17 | +0.82 | +0.228 |
| 14 | CSCO/SNOW |  29.3 |    8 |   14 |   42 |   80 |   80 |  100 |  100 |  100 | +0.07 | +0.78 | +0.304 |
| 15 | CRM/ADBE |  27.7 |    8 |   29 |   20 |   73 |   83 |  100 |   70 |   38 | +0.14 | +0.80 | +0.162 |
| 16 | LOW/NKE |  27.6 |    7 |   22 |   30 |   83 |   70 |  100 |   85 |   69 | +0.11 | +0.75 | +0.342 |
| 17 | QQQ/GLD |  27.6 |    6 |   11 |   60 |   66 |  100 |  100 |   70 |  100 | +0.06 | +0.72 | +0.495 |
| 18 | LLY/TMO |  27.0 |    6 |   13 |   45 |   70 |   88 |   99 |  100 |  100 | +0.07 | +0.71 | +0.059 |
| 19 | ORCL/QCOM |  25.9 |    5 |   24 |   33 |   87 |   89 |   98 |   70 |   92 | +0.12 | +0.66 | +0.270 |
| 20 | GS/MS |  25.4 |    5 |   15 |   50 |   53 |   80 |   99 |   70 |  100 | +0.08 | +0.69 | +0.127 |
| 21 | JNJ/MRK |  20.1 |    2 |   24 |   35 |   72 |   80 |   74 |   70 |   84 | +0.12 | +0.58 | +0.163 |
| 22 | INTC/ARM |  19.9 |    2 |   13 |   38 |   85 |   92 |  100 |   70 |   92 | +0.07 | +0.59 | +0.068 |
| 23 | SBUX/COST |   1.6 |   54 |   58 |    0 |   86 |   74 |  100 |   40 |  100 | +0.29 | +2.38 | +0.194 |
| 24 | QCOM/PLTR |   1.5 |   43 |   43 |    0 |   93 |   82 |  100 |  100 |   84 | +0.21 | +1.99 | +0.178 |
| 25 | MSFT/NVDA |   1.4 |   33 |   47 |    0 |   88 |  100 |   89 |  100 |  100 | +0.23 | +1.65 | +0.197 |
| 26 | NOW/PLTR |   1.4 |   40 |   48 |    0 |   92 |   81 |  100 |   40 |  100 | +0.24 | +1.92 | +0.328 |
| 27 | PLTR/DOCU |   1.4 |   31 |   62 |    0 |   91 |   97 |  100 |   40 |   77 | +0.31 | +1.58 | +0.352 |
| 28 | BA/GE |   1.1 |   26 |   17 |    0 |   80 |   80 |  100 |   70 |   84 | +0.08 | +1.41 | +0.088 |
| 29 | NVDA/SNOW |   1.1 |   11 |  100 |    0 |   99 |  100 |   90 |   70 |   45 | +1.07 | +0.90 | +1.147 |
| 30 | AVGO/TXN |   1.1 |   24 |   24 |    0 |   88 |   97 |  100 |   70 |  100 | +0.12 | +1.34 | +0.125 |
| 31 | HD/TGT |   1.1 |   27 |   16 |    0 |   79 |   79 |  100 |   70 |  100 | +0.08 | +1.44 | +0.080 |
| 32 | CRM/PLTR |   0.9 |   10 |   53 |    0 |   90 |   83 |   90 |   40 |   30 | +0.27 | +0.83 | +0.383 |
| 33 | ADBE/PLTR |   0.9 |   12 |   37 |    0 |   90 |   79 |  100 |   70 |   45 | +0.18 | +0.91 | +0.197 |
| 34 | UNH/TMO |   0.9 |   12 |   21 |    0 |   84 |   88 |  100 |   70 |  100 | +0.11 | +0.92 | +0.198 |
| 35 | ABT/DHR |   0.9 |    8 |   40 |    0 |   84 |   74 |   95 |  100 |   77 | +0.20 | +0.78 | +0.289 |
| 36 | AMD/TXN |   0.8 |   11 |   16 |    0 |   87 |   98 |   93 |   70 |  100 | +0.08 | +0.89 | +0.162 |
| 37 | AVGO/QCOM |   0.8 |    9 |   22 |    0 |   86 |   97 |  100 |   70 |  100 | +0.11 | +0.81 | +0.275 |
| 38 | ORCL/DOCU |   0.8 |   10 |   13 |    0 |   81 |   89 |  100 |   70 |  100 | +0.07 | +0.84 | +0.174 |
| 39 | META/CRM |   0.7 |    7 |   20 |    0 |   83 |  100 |   95 |   40 |  100 | +0.10 | +0.75 | +0.141 |
| 40 | SNOW/DOCU |   0.7 |    7 |    9 |    0 |   76 |   76 |  100 |   70 |  100 | +0.05 | +0.75 | +0.116 |

## Multiple-comparison calibration (read this first)

- Gate = EDGE aspect > 0 (t_oos > 0.5 AND delta > 0.05).  Under pure noise, ~63 of 404 pairs pass this gate by chance; observed: 47.
- Delta (real minus scrambled per-trade, sigma): mean -0.029, sd 0.199; positives 114 vs negatives 172 -- centered on 0.
- OOS t-stats: mean -0.55, only 3/404 > 2 (noise expects ~9), max 3.94.

Interpretation: the gate passing rate is CONSISTENT WITH PURE NOISE.  No pair is evidenced by this sample; composite scores rank candidates on relative merit only.  Top candidates (e.g. LLY/MRK: cointegrated p=0.005, positive delta, but 15 OOS trades) are flags for focused follow-up with more data -- NOT tradeable signals.
