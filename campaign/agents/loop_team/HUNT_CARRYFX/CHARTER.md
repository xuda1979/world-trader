# HUNT_CARRYFX — carry & FX-momentum hybrid on EXISTING verified data (reassigned slot, iter 4)
Two prior slots (HUNT_EQMOM, HUNT_CROSSREGIME) died on API 429s; HUNT_FXMICRO established:
FX daily-OHLC range/OC-reversal/carry-proxy are all DEAD at 6bps; the ONLY near-miss was
GBP/NZD/AUD-cross z-reversion (SR 1.9 standalone but scramble p 0.61 — rejected as unproven).

Your angle is DIFFERENT: blend the surviving FX stat-arb block (campaign/agents/loop_team/
HUNT_FXMICRO/sleeves/FXMR3_42z2_daily.csv if present — read its .meta for the failure disclosure)
with a second small decorrelated book to build ONE composite sleeve that PASSES all gates,
especially the 200x block-scramble (10-day blocks, p<0.05 that SR<=0). Candidates to blend:
- dual-timeframe z (21d + 63d) with different gates (the lb42-single-frame concentration on
  2022 GBP crash is the failure mode: top-20 days = 41% of PnL)
- carry-accrual tilt on the same 3 books (FRED intl 10y monthly, m usable m+1 — PIT-verified
  by HUNT_FXMICRO)
- weekday-conditioned sizing (avoid the dead Monday FX liquidity)
Gates: SR>=0.6, H1/H2>=0.3, 200x 10d-block scramble p<0.05 (the KILLER gate — top-day
concentration must be broken), <=2 neg yrs each >-5%, |corr|<0.15 to
campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv, ac1<0.5, uniqR>=0.08.
T+1, 6bps/side, borrow 0.5%/yr. If you cannot break the scramble gate, REPORT THE FAILURE with
exact p-values — that is a real result and prevents re-running.

Deliver: sleeves/ + FINDINGS.md with exact numbers. Last line: HUNT_CARRYFX DONE
