# HUNT_CROSSASSET2 — new decorrelated cross-asset daily engines (iter 6)

GOAL: add >=2 decorrelated high-SR DAILY engines (target SR>=1, corr<0.1) so the blend can push
toward ann>=80%/SR>=5 at lev<=1.6. The current 14 engines are dominated by Brent-WTI, NG, rates,
dualmom equity, dieselfcrack, FX. This hunt targets RELATIVE/DIFF books across asset classes and
EM data that have NOT been tried.

READ FIRST (dead-lists): campaign/GOAL100_FINAL_STATE.md "removed/failed"; loop_team/*/FINDINGS.md.
DO NOT re-run: FF factor premia, industries/deciles, equal-wt BAB, MM naive ivol, gold-silver,
credit-as-paper-synth, FX carry on 8 majors, NG/oil basis, FOMC x gold/NG. Hunt is for GENUINELY NEW
tradeable RELATIVE-PRICE relationships on data in disk.

DATA AVAILABLE (verify fail-closed):
- tools/quant/data/twelve_big (298 names), twelve_extend (440), twelve_liq — equity panel incl
  factor-tilt ETFs (MTUM, QUAL, VLUE, USMV if present) and sector/commodity ETFs (XLK, XLE, GLD, SLV...)
- tools/quant/data/newdata/: BAML credit OAS (BAMLC*, BAMLEM*, BAMLH0A0HYM2), DEX EM FX crosses,
  DCOILBRENTEU/DCOILWTICO, and more. Check full listing before fixing ideas.
- tools/quant/data/ff_factors
- RATES: tools/quant/hedge_fund_strats/data_fred/ (DGS*, T10YIE, DFII10, hy_oas, baa, aaa, international 10y)

IDEA SLATE (target DWARF carry-type decorrelation, SR>=1, corr<0.1):
1. SECTOR-BASKET relative books (e.g., XLE/XLB vs XLK, financials vs industrials) with time-series
   momentum on the SPREAD, T+1 — different domain from the single-commodity sleeves.
2. COMMODITY-INDEX vs COMMODITY-ETF basis books on real daily prices.
3. RATES-CURVE 2s10s / 5s30s steepener books with trailing momentum (rates sleeve a6r7/QAxasts /
   carryv2 exist — pick DIFFERENT tenor/spread or z-reversion to stay <0.15 corr).
4. CREDIT-OAS momentum/reversion (BAML OAS series are real daily tradable proxies via HYG/LQD —
   NOT the forbidden paper-synth that a prior agent built; use the OAS as timing signal on the
   real ETF price).
Gates: as HUNT_FXDEPO (see that charter). T+1, 6.4bps/side, borrow 0.5%/yr, 200x 10d-BLOCK
POSITION-LAG scramble p<0.05, |corr|<0.15, ac1<0.5, uniqR>=0.08, H1/H2>=0.3, <=2 neg yrs.
Deliver sleeves/+meta + repro script + FINDINGS.md. Last line exactly: HUNT_CROSSASSET2 DONE
