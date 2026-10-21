# DATA_MORE_ETF — download MORE free sector/international/commodity daily ETF data (track C, user:
# "get more free data ... just get more data")

Working API keys in .env.local (TWELVEDATA_KEY, FINNHUB_KEY — TESTED WORKING from coordinator).
Twelvedata free tier: get /time_series?symbol=SYM&interval=1day&outputsize=5000&apikey=KEY
(JSON values are chronologically ASCENDING; reverse before saving). Finnhub for quote/sanity.
Rate limits: Twelvedata free ~8 req/min, ~800/day — be economical, batch, and add sleep(8) between
calls; if 429, back off. DO NOT hammer.

DELIVER MORE FREE DAILY OHLCV (date,open,high,low,close[,vol]) into a NEW dir:
  tools/quant/data/more_etf/<SYMB>.csv   (columns date,open,high,low,close,vol)
Target universe (tradable, decorrelated candidates + instruments for sector/credit/international
engines). Prioritize symbols that EXTEND existing coverage:
- Sector/industry ETFs: XLE,XLB,XLF,XLI,XLK,XLY,XLP,XLU,XLV,XLRE,XLC (note: only XLE/XLB/XLF/XLI
  exist on disk; the other 5 are MISSING — fetch them), KBE,KRE (fin), ITB, XHB, SMH (semis),
  IGV (soft), XOP (oil), XME (metals), GDX, GDXJ, SLV, XLV.
- International equity: EEM,VWO,EFA,EWJ,EWG,EWU,EWP,EWL,MSCI countries; EWT (TW), EWY (KR),
  EWZ (BR), EWW (MX), EWA(ploid AU), FXI (CN), INDA, EWK, EWS, EID.
- Commodity/rates/credit ETFs: GLD,SLV,USO,UNG,TLT,IEF,SHY,LQD,HYG,AGG,JNK,TIP,VNQ (RE),
  TIP (tips), EMB (EM bonds), BIL (cash), IAU, DBC, GSG.
For each symbol you fetch, RUN (in scratch): span lint (start/end, n rows, gaps, 0 returns), and
save a manifest.csv with (symbol,start,end,rows,max_gap_days). Do NOT overwrite existing data dirs.
Only write inside tools/quant/data/more_etf/. Record everything in FINDINGS.md (symbols fetched,
failures, spans). This is a DATA-ONLY task — NO strategy backtests. Last line exactly:
DATA_MORE_ETF DONE
