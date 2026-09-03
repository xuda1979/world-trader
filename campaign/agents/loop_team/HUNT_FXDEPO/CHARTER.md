# HUNT_FXDEPO — FX deposit-rate & cross-rate carry engines (iter 6)

GOAL: the honest-ceiling analysis says the blend needs ~2 more genuinely decorrelated DAILY engines at
SR>=1.5, corr<0.1 to reach the ann>=80%/SR>=5 target at lev<=1.6. FINAL_STATE explicitly flags "FX
deposit rates" as an uncharted data domain. Current FX sleeve CFX4 uses 8 major pairs z-reversion
(corr 0.00 to blend). We need MORE FX/book variants, cross-rates, and deposit-rate carry.

READ FIRST (avoid dead ideas): campaign/agents/loop_team/HUNT_CARRYFX/FINDINGS.md (CFX4's parent),
HUNT_FXMICRO/FINDINGS.md, HUNT_CROSSREGIME/FINDINGS.md. Do NOT re-run dead carry/regime variants.

DATA AVAILABLE (verify on disk, fail-closed):
- tools/quant/data/fx/ : AUD_USD, EUR_GBP, EUR_USD, GBP_USD, NZD_USD, USD_CAD, USD_CHF, USD_JPY (2007+ daily)
- tools/quant/data/newdata/DEX*.csv : MANY extra EM/Scandinavian crosses against USD
  (DEXBZUS Brazil, DEXDNUS Denmark, DEXINUS India, DEXJPUS, DEXKOUS Korea, DEXMXUS Mexico,
   DEXNOUS Norway, DEXSDUS Sweden, DEXSFUS Switzerland, DEXSIUS Singapore, plus DEXUSAL/DEXUSEU/DEXUSUK).
  These are largely UNUSED by CFX4 — build carry/momentum/reversion books on them.
- FRED rates dir (tools/quant/hedge_fund_strats/data_fred/) — check for deposit/3mo policy rates
  (FEDFUNDS, DGS3MO, TB3MS, and any foreign short rates) to build CARRY blends (long high-yield vs
  short low-yield FX, or realized FX carry using short-rate differentials).
- Search for any deposit-rate proxies on disk: grep -ri "depo\\|3mo\\|sofr\\|euribor\\|libor" in data/.

IDEA SLATE (target SR>=1, corr<0.1 to HONEST14V3 blend):
1. EM/Scandinavian FX z-reversion books (like CFX4 but on DEX crosses; T+1, trailing z).
2. Cross-rate TRIANGLE books (e.g., EUR/USD vs GBP/USD rate, USD/JPY vs AUD/USD) — pairs that
   CFX4 doesn't trade directly.
3. FX CARRY from short-rate differentials (if rate data on disk) — long high-carry vs low-carry,
   vol-managed.
4. FX momentum on the extended cross panel.
Gates (full): SR>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each>-5%, 200x 10d-BLOCK POSITION-LAG scramble
p<0.05 (position-lag, NOT return permutation), |corr|<0.15 to HONEST14V3_BALANCED blend, ac1<0.5,
uniqR>=0.08, T+1, 6.4bps/side on turnover, borrow 0.5%/yr. Use campaign/harness/data.py helpers
(closes, fred, save_sleeve) and gates.py. Log data-missing as BLOCKED.
Deliver sleeves/*.csv+meta + repro script under campaign/scripts/ + FINDINGS.md with exact PASS/FAIL.
Last line exactly: HUNT_FXDEPO DONE
