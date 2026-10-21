# A1 r7 — NEW FREE DATA engines (FRED 1990-2026 daily in tools/quant/hedge_fund_strats/data_fred_new/)
Key new data: DCOILWTICO/DCOILBRENTEU (1990+), VIXCLS (1990+), DGS10/DGS2/DGS30 (1990+), 
T10Y2Y, DAAA/DBAA credit, DEXJPUS/DEXUSEU FX, DPROPANE.
Missions (build 1-2 genuine de-correlated engines; SR>=1.0, |corr|<0.25 to champion):
1. **Cross-asset carry-trend at 1990-2026**: gold(need daily - try GOLDAMGBD228NLBM; else use existing
   data_fred/xau.csv), oil(WTI/Brent), US10y (synth TR dur7.5), 2s10s slope. 126/252d dual trend + carry,
   trailing vol-target 12%. The LONG history extends testable window -> better OOS.
2. **Yield momentum**: DGS10 vs its 63d/252d mean + slope DGS10-DGS2 as separate factor books.
3. **Oil-Brent basis / energy seasonality** with the 1990+ daily history (longer than prior 2000-limited).
4. **VIX carry alternative**: DFF fed-funds minus VIX -> risk-appetite regime, long risky when spread>0.
Use honest funding (rf + L*(TR-rf)), T+1, 6bps, scramble/gates. Save sleeves to sleeves/.
Server: append FINDINGS.md, last line ROUND r7 DONE.
