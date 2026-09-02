# LOOP ITERATION 1 (2026-09-02) — improvement attempts & outcomes

## Primary deliverable: XGB1y flattening bug found + corrected (see FINDINGS.md)
Honest champion baselines committed:
- GOAL100_HONEST11_daily_BALANCED_daily.csv  39.6% ann, SR 4.22, MDD -4.85%, OOS17+ 44.1%
- GOAL100_HONEST12_XGBFAIR_daily_BALANCED_daily.csv  45.7% ann, SR 2.23, MDD -4.96%, OOS17+ 49.6%
(Note HONEST12_XGBFAIR's SPX-path is an ESTIMATE; the strictly defensible number is HONEST11.)

## Improvement candidates TESTED this iteration (all failed gates honestly — do NOT re-run):
1. **EM-FX cross-sectional TSMOM** (BRL/INR/KRW/MXN/NOK/SEK/ZAR/SGD/EUR/GBP; lb 10/21/42/63):
   SR 0.35-0.52, H2 ~0, 19-23 neg years, scramble_p 0.89-1.0 (no edge). Corr2blend ~0 (genuinely
   decorrelated domain but NO edge in this signal). FAIL.
2. **OP (profitability) decile 10−1 L/S** (Ken French, daily 1963+): SR 0.63, 9 neg yrs,
   scramble_p 0.99, corr -0.03. FAIL.
3. **INV (investment) decile 10−1 L/S**: SR 0.50, 12 neg yrs, scramble_p 0.995. FAIL.
4. **OP hi30−med L/S**: SR 0.26, scramble_p 0.025. FAIL.

## Path-searching insight
The binding constraint is finding genuinely decorrelated, instrument-real, HIGH-SR **daily**
engines. Naive L/S or TSMOM on new domains does NOT produce edge above the vol-targeted noise
floor. Next iterations should try: (a) proper carry (interest-differential) on FX using the
DGS/rate data, (b) cross-asset macro regimes combining multiple untapped series, (c) statistical
arbitrage on the ff_factors SMB/HML/MOM/RMW/CMA, (d) reconstructing XGB1y's TRUE daily path
from original holdings. Check correlation <0.15 to HONEST11 blend before full gate run.
