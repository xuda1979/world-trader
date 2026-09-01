# D4_microstruct — Round 1 FINDINGS (2026-09-01)

Mission: find the NEXT cash-market microstructure engine after C5's natgas weekday
calendars. All engines: T+1 execution (position at close t earns logret t->t+1),
6bps/side costs, harness trailing expanding 10% vol target (min 60d, cap 3x),
windows 2008+ unless noted. Scrambles = event/position-map shuffles through the real
pipeline (harness scramble_pval is degenerate — permutes the return series, p≈1 always;
same conclusion C5 documented). Gates per GOAL100_AGENT_BRIEF.md; ALL must pass to save.

Shared lib: campaign/agents/D4_microstruct/d4_lib.py; repro scripts archived in
campaign/scripts/d4_*.py (d4_i1*.py idea1, d4_i2.py idea2, d4_i34.py ideas 3+4,
d4_i5.py idea5, d4_i6.py idea6, d4_au_check.py/d4_fri2.py follow-ups).

## Idea 1 — FOMC x natgas/gold (vol compression + post-FOMC drift + calendar interaction)
Data: DHHNGSP (1997+), xau (2008+), fomc_dates.csv (119 meetings, day1/day2).
Phase A unconditional mean |ret| by FOMC window (bp/d): NG decision -33 (t=-1.1),
NG eve +18, gold decision +22 (t~2.3), gold eve +6. Vol compression does NOT show
up as elevated natgas moves; the charter's "long after FOMC if vol contracts" premise fails.
Phase B post-FOMC k-day LONG books: NG k=1 SR -0.66 (raw t=-3.32 — drift is NEGATIVE),
k=3 -0.35, k=5 -0.14; gold k=1..5 SR -0.21..-0.35. Event scramble (500 rnd dates):
NG k=1 real -0.66 vs p95 +0.25, p=1.000 — the negative drift is itself unremarkable
(vs scrambled p95>0.25 it is not even a significant SHORT edge after costs).
Short-side variants through full gates: best k=1 calm=None SR 0.51, H1 0.22 (FAIL c),
MDD -30.7%. Vol-conditional (short full if trailing 10d vol z<0 else half): SR 0.53, MDD -24.8%.
Gold long-into-decision-day (correct T+1 book, 110 events): raw event mean +20.6bp but
book SR 0.18, negy 5/19. NG short-into-decision-day: SR 0.16.
**FAIL gate (a) SR>=1.0 everywhere (max 0.53); also fails (c) halves.**

## Idea 2 — Heating-oil seasonal switch (a-priori convention documented: EIA heating
season Oct 1-Mar 31; alternative Oct-Feb also run; DHOILNYH spot 1986+)
HO season Oct-Mar L/S(vs WTI): SR 0.10, negy 17/41, MDD -29.3%. Oct-Feb L/S: SR 0.18.
Oct-Mar long-only: SR -0.01, MDD -66.8%. Crack z-rev (HO-WTI lb63/126/252, both signs):
best SR 0.17. Monthly raw-t scan shows the only significant month is AUGUST (t=+2.34),
opposite the heating story; in-season months all |t|<=0.5.
**FAIL gate (a): max SR 0.18. The seasonal-switch premium does not exist in this print.**

## Idea 3 — Jet fuel post-Covid regime (2020+ only, DISCLOSED 6.7y window; DJFUELUSGULF)
Jet-HO spread momentum lb21/63/126 both signs: best SR 0.82 (lb126 reversion) but H1 1.21
/ H2 0.27 and only 7 yearly observations -> fails gate (c) H2 and cannot satisfy gate (d)
with <10 years. All momentum variants negative (down to -1.47).
**FAIL gates (a) 0.82<1.0, (c) H2, (d) window too short.**

## Idea 4 — Copper/gold ratio (copx 2010+/xau): growth-fear gauge
4a ratio 63/126/252d momentum z -> SPX: SR -0.15/-0.10/+0.12 (binary mom63 -0.12).
Conditional SPX SRs: 0.79 high-mom vs 0.42 low-mom (direction right, too weak net of
timing noise). 4b ratio 21/63d z-reversion on COPX vs XAU both signs: best SR 0.12.
**FAIL gate (a): max |SR| 0.12-0.38 range, nothing >= 0.4 even gross-side.**

## Idea 5 — Retail gasoline (GASREGW, Mondays 1990+) vs WTI margin z-reversion,
correct alignment: Monday print -> ffill signal (limit 7d) -> T+1 daily WTI book.
Margin AR(1) = -0.241 (real reversion exists at weekly freq), t of weekly chg = 0.05.
z-rev lb 8/13/26/52w, both signs: best SR 0.25 (lb26w, sgn short-margin) — and the
margin sign is INVERTED vs naive (retail lags wholesale; pump prices mean-revert with
a lag => short-margin/long-WTI side). Still: **FAIL gate (a) 0.25<<1.0.** C5's 0.75
version not reproduced under stricter T+1/ffill-limit alignment.

## Idea 6 — Natgas bid-week (last-3-bd vs first-5-bd of month, DHHNGSP 1997+)
Raw bp/d by position: bd0 -16305bp (t=-1.91), last3 -6959bp (t=-1.65), first5 -4440bp
(t=-1.29), mid +2557bp (t=1.15). Books: long-last3 SR -0.37; short-last3/long-first5
SR 0.10; long-first5 SR -0.08; mid-month long SR 0.12 (corrB 0.119).
**FAIL gate (a): max 0.12. Bid-week roll economics not exploitable in daily spot closes.**

## Follow-up scans (domain completion)
- Weekday scan on HO / jet (2008+): best legs both SHORT Friday t=-2.69/-3.08, but
  through-cost books only SR 0.31 (HO) / 0.43 (jet), H2 ~0.0 — decayed post-2019
  (yearly: 2021 -13.3, 2023 -6.2, 2024 -7.8). Combined avg book SR 0.46, H1 1.05/H2 0.08,
  MDD -43.9%, 7/19 neg years incl -13.3% (2021). **FAIL gates (a),(c),(d).**
- Propane DPROPANEMTXCF.csv is HTML-corrupt on disk (C5 noted same) — skipped.
- NG mid-month calendar: SR 0.12. AU FOMC-day book: SR 0.18. Nothing close.

## Verdicts summary
| # | Idea | Best config | Key numbers | Verdict |
|---|------|-------------|-------------|---------|
| 1 | FOMC x NG/AU vol+drift | short post-FOMC NG k=1 | SR 0.51, H1 0.22, raw t=-3.32 (drift negative) | FAIL (a),(c) |
| 2 | HO heating-season Oct-Mar | L/S vs WTI | SR 0.10-0.18, negy 17/41 | FAIL (a) |
| 3 | Jet post-Covid 2020+ | jet-HO rev lb126 | SR 0.82, H2 0.27, 6.7y window | FAIL (a),(c),(d) |
| 4 | Cu/Au ratio -> SPX / rev | mom252->SPX | SR 0.12 (rev best -0.38) | FAIL (a) |
| 5 | Retail gas-WTI margin weekly z-rev | lb26w short-margin | SR 0.25, AR(1)=-0.24 | FAIL (a) |
| 6 | NG bid-week last3/first5 | short-last3/long-first5 | SR 0.10, raw t<=1.9 | FAIL (a) |
| + | short-Fri distillate (HO+jet) | combined avg | SR 0.46, H2 0.08, 2021 -13.3% | FAIL (a),(c),(d) |

## HONEST BOTTOM LINE
0/6 charter ideas (plus 2 follow-up scans) produced a sleeve meeting gate (a) SR>=1.0
net of 6bps — best honest full-window SR was 0.53 (short post-FOMC natgas, k=1, which
also fails halves). The C5 natgas weekday engine remains the only passing cash-market
microstructure calendar found in this data universe; nothing in FOMC windows, heating-oil
seasonals, jet fuel, Cu/Au ratio, retail-gas margins, or bid-week dynamics comes within
0.45 SR of the bar. No sleeve CSVs saved this round (contract: only ALL-gates-pass saves).
Domain closed for Round 1. Suggested Round-2 angle: intraday/session microstructure
(settlement-vs-close, contract-roll windows) needs data we do not have on disk —
recommend coordinator redirect D4 to a different data domain rather than re-scanning
FRED daily prints.

ROUND 1 DONE

## NUMBERED SUMMARY (Round 1)
1. FOMC x natgas/gold vol-compression & post-FOMC drift: best short-NG k=1 SR 0.51 (raw drift t=-3.32 NEGATIVE; gold decision-day +20.6bp/book SR 0.18; scramble p=1.000) — FAIL gates (a),(c). No save.
2. Heating-oil Oct-Mar seasonal (a-priori EIA convention): L/S SR 0.10, long-only -0.01, crack z-rev best 0.17, only Aug t=+2.34 (opposite story) — FAIL gate (a). No save.
3. Jet fuel post-Covid jet-HO reversion (2020+ disclosed): best SR 0.82, H2 0.27, 6.7y window — FAIL gates (a),(c),(d). No save.
4. Copper-gold ratio mom->SPX (SR 0.12 best) & 21/63d reversion (best 0.12; both-sign sweeps <=0.38) — FAIL gate (a). No save.
5. Retail-gas/WTI weekly margin z-reversion, Monday-aligned T+1: AR(1)=-0.241 but best SR 0.25 (lb26w, inverted sign vs naive) — FAIL gate (a). No save.
6. Natgas bid-week last-3bd/first-5bd: books SR -0.37..+0.12 (raw month-edge t<=1.9) — FAIL gate (a). No save.
7. Follow-up short-Friday distillate book (HO+jet): SR 0.46, H1 1.05/H2 0.08, 2021 -13.3% — FAIL gates (a),(c),(d). No save.

SAVED SLEEVES: none. Best honest full-window net SR 0.53 << 1.0 gate.

ROUND 1 DONE
