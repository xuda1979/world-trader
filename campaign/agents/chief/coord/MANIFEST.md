# GOAL100 CHIEF COORDINATION — 21-AGENT WAVE (iter12 + HUNT_TIMESFM, 2026-09-06/07)
Chief manager: coordinator. 6.4bps full-|dW| one-side, IBKR call 4.5% on (gross-1), borrow 0.5%/yr
on shorts, non-shortable stocks considered, leverage<=1.6, >=0 every year. 21 agents in parallel.
Workstreams:
 A NEW-ENGINE  : HUNT_COT2, HUNT_CRYPTO2, HUNT_INTERNATIONAL2, HUNT_CMDT2, HUNT_MACRO2, HUNT_VOL2,
                 HUNT_FXCARRY2, HUNT_SECTOR2, HUNT_CREDIT2, HUNT_TREASFUT, HUNT_TIMESFM  (11)
 B CONSTRAINTS : CAMP_SHORT, CAMP_BORROW, CAMP_COST                            (3)
 C MORE DATA   : DATA_FREDMORE, DATA_ETF_MORE, DATA_COTMORE                    (3)
 D AUDIT       : AUDIT_CHAMP2, AUDIT_FWBUGS, AUDIT_RECON, AUDIT_GATES2         (4)
Total = 21.

# added 2026-09-07 ~17:4x CST by CIO (user request): HUNT_TIMESFM — Google TimesFM 3.0
# (pypi timesfm==3.0.1, JAX backend, no TF) forecasting sleeves. NEW-ENGINE workstream.
# Forecast PIT series -> tradeable, decorrelated, cost-honest sleeves. Honest negative ok.
