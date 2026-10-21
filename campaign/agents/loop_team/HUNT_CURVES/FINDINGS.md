# HUNT_CURVES — FINDINGS (iter8) — NEW-DATA HUNT #2

**VERDICT: NEGATIVE — 56 variants, ZERO reach SR 0.3. Best: eer_GB_mom21->GBP_USD 0.261 (4 neg),
jgb_5Y30Y_mom->EWJ 0.252 (9 neg — fails yearly hard). Full sovereign-curve feature set (JGB
1974+ 15 tenors; BoE nominal/real/OIS; ECB AAA 17 tenors; BIS broad NEER/REER daily 1996+)
mapped through z-scored slope/butterfly mom+rev to their natural FX/equity tradables adds
NOTHING over the already-dead rates-curve/credit families. The new data confirms the prior
negative rather than overturning it: curve SHAPE carries no daily-tradable edge at 6.4bps on
ETF/FX proxies. TDD: 5 tests RED->GREEN (curve_eng.py); bt regression 28 GREEN.**

Gates: ann80 NO | SR5 NO | DD7 NO | 0-neg NO (best variants 4-18 neg years).
DEAD_IDEAS += "sovereign-curve shape features (JGB/BoE/ECB-YC/BIS-EER) on FX/ETF proxies", dead,
"56 variants all <0.3 SR; best 0.261/4neg; confirms prior curve-dead verdicts".
Do not re-run: slope/butterfly z 63-252d mom/rev on USD_JPY/EUR_USD/GBP_USD/EWJ/EWG/EWL/EWA/UUP.
HUNT_CURVES DONE
