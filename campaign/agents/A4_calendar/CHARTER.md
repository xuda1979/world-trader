# A4 — Calendar / seasonality (equity panel + SPX/macro)
Families:
1. Turn-of-month: long equities (SPY proxy = SPX or EW panel) last close of month -1..+3, cash otherwise. 20y, 6bps on switches (~12-16 switches/yr => cheap).
2. Holiday effect: long before/after US holidays.
3. September / Halloween: seasonal long-only windows (Nov-Apr) vs May.
4. Turn-of-month on the 298-name panel xs: TOM premium concentrated in small/high-vol names?
Gate warning: calendar effects are WEAK (SR often 0.3-0.5 gross). Boost odds by combining TOM+holiday+seasonal into one composite calendar book. Scramble test with circular shift PRESERVES weekday alignment (shift by multiples of 5/21 to be fair).
