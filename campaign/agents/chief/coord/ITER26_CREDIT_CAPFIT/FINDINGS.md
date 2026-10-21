# ITER26 FINDINGS (2026-09-19, session #9) — recorded post-reveal

Run: driver_2026-09-19.py per FINDINGS_PRECOMMIT.md (sha16 4d3373c65598a1cb, sealed
before this driver existed). Full audit trail: driver_2026-09-19.log.

VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per pre-commit).
Champion sha16 pre == post: 8559fa55ee9a3417 / weights d2d11c92a98683df.

Headline numbers (see campaign/GOAL100_ITER26_CREDIT_CAPFIT.md for the table):
- Repair step: credit clamped 0.19034 -> 0.15385 (= 2/13 exactly, sole violator);
  Wmax 2.0000x by construction; brwt block untouched at 0.30; CFX4 stays 0.
- IS: SR 4.2579 > 4.198632 bar -> ADMITTED (unprojected was 4.2575: the fit's extra
  3.65pp credit = +0.0004 IS-SR, margin noise - the appetite was shadow-pricing, not
  marginal alpha).
- Reveal: FS SR 3.707892 < 3.751429; bins 2/5 positive (min -0.1185 >= -0.10 floor but
  pos count fails); ann/MDD/neg-yrs/gross/CFX4/G8 all PASS. Rejection is purely the OOS
  police. ITER17 law kill #4.

Deviations from pre-commit: NONE of substance.
- Disclosed driver fix (pre-commit section 3 definition made computable, unchanged bar):
  G8 row counts coverage-restricted after CFX4's zero-coverage made the naive all-12
  dropna degenerate (run 1 ZeroDivisionError, fail-closed; fix logged in driver source).
- Suite landed: 509 passed / 0 failed (503 + 6 pins), mutation-checked.

Consequence for the ledger: the #118 operator item "relax Wmax 2.0x?" is DATA-DEAD for
credit. Frontier fully closed and measured.
