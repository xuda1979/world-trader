# A2 r6 — NEW-FAMILY directive (the joint goal now: SR_m>=2.0, ann>=20%, MaxDD<5%)
The campaign needs NEW orthogonal alpha, not vol-budget scaling. You own a fresh family:
**OVERNIGHT vs INTRADAY split** (classic premium, unexplored this campaign):
1. Overnight-only equity book: long 298-panel EW from close to next open (overnight premium is
   documented large-cap 1980-2020), 6bps/side charged on the daily round trip, T+1 booking.
   Panel closes/opens in tools/quant/data/twelve_big/*.csv (open + close columns).
   Vol-target 8-10%. SR>=0.8 target; corr to champion likely <0.2 (it is a different risk premium).
2. Overnight + TOM intersection: overnight exposure only during turn-of-month window (A4 found TOM real).
3. Intraday-momentum-only book (close-to-close minus overnight = intraday leg): likely negative
   premium; if positive since 2018, log as finding (regime shift documentation).
CRITICAL: overnight return = open_{t+1}/close_t - 1. Costs: 6bps at close t + 6bps at open t+1 = 12bps per
overnight round trip (charged daily). If net SR < 0.6 after honest costs, log and stop (negative result is fine).
Append FINDINGS.md; last line ROUND r6 DONE.
