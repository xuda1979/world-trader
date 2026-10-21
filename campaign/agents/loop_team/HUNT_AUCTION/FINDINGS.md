# HUNT_AUCTION — FINDINGS (iter8) — NEW-DATA HUNT #3 (+1 REAL BUG FIXED)

**VERDICT: NEGATIVE — and the screen's headline (ind_bill longflat QQQ 0.585/4neg) was a
BOOK-BUILD DIVERGENCE between screen and deep-check paths. The correct deep rebuild (real
position path = lag(sig)*vol_scale capped, real costs) gives SR −0.015 (QQQ) / −0.167 (DIA),
scramble p=0.93-0.97 (= pure noise), 9-10 neg years. Auction demand carries NO daily equity
timing edge at 6.4bps. The 0.585 screen number came from bt.sleeve receiving an UNLAGGED
daily-ffilled signal (double-lag vs lag semantics differed between the two paths) — caught by
the deep-check rebuild, killed before delivery.**

## BUG FIXED (data layer, TDD)
- tauctions.csv had total_accepted_mmn + competitive_accepted_mmn 100% NULL: ta_dl.to_rows
  mapped WRONG WS FIELD NAMES (totalTenderAccepted vs real totalAccepted). 7852 rows fetched
  with 2 dead columns. Fixed mapping + added primaryDealer/soma/fima (bonus fields, 6220 nonnull).
- TDD regression lock: test_to_rows_field_mapping (RED conceptually: old code returned None for
  totalAccepted; GREEN after fix; 6/6 pass). Re-fetched all 27y; lint PASS (n=7852, btc=7845).

## Screen (64 variants): 13 >= 0.3 SR but ALL are long-flat equity-drift variants failing deep rebuild.
## Deep verdict table (QQQ): SR -0.015, scramble p 0.97, 2008+ 9 neg years incl 2008 -14.4%.
## Gates: ALL NO.
DEAD_IDEAS += "Treasury-auction demand (btc/indirect-share) as equity regime gate", dead,
"screen 0.585 was book-path artifact; honest rebuild SR -0.015..-0.17, scramble 0.93-0.97".
Do not re-run: btc/indirect z-gates 252/504 longflat/inv on QQQ/DIA.
HUNT_AUCTION DONE
