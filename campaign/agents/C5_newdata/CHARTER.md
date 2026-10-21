# C5_newdata — New free-data hunter (NEW DOMAIN: data acquisition + engines)

Mission: find and download NEW free datasets (2006+ daily preferred), then build >=1 passing
sleeve from them. You may use curl/python to fetch. Sources to try (network allows some):

1. STOOQ (https://stooq.com/q/d/l/?s=SYMBOL&i=d) — comma CSVs: futures & indices NOT behind
   hard blocks historically: try ^SPX, ^NDX, ^DJI, ^DAX, ^CAC, ^UKX, ^NKX(or 1329 JP), cl.f, gc.f,
   ng.f, hg.f (copper), zw.f (wheat), zc.f (corn), zs.f (soy), zo.f (oats), zr.f (rice), sb.f (sugar),
   kc.f (coffee), cc.f (cocoa), ct.f (cotton), lb.f (lumber), es.f, nq.f, ym.f, rtt.f, mtx.f, nk.f.
   If JS-blocked (HTML response), try https://stooq.pl mirrors or mark blocked and move on.
2. Ken French additional sets (mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/...):
   Accruals daily? (no) — try: 'ST_Reversal_Factor_Daily_CSV.zip' variants, 'Prior_2_12_Daily',
   '6_Portfolios_2x3_Daily' (have), 'Portfolios_Formed_on_NVLI_Daily_CSV.zip' (investment),
   'Portfolios_Formed_on_OP_Daily_CSV.zip' (profitability), 'Portfolios_Formed_on_CF_Daily',
   'Portfolios_Formed_on_VAR_Daily' (5-factor volatility portfolios!). VAR portfolios = new.
3. FRED extras: DTWEXBGS (dollar index broad 2006+), DCOILWTICO, DCOILBRENTEU, DHHNGSP,
   DPROPANEMTXCF (propane), DAPIUS (insurance), GASREGW (gas), TCU (capacity util monthly),
   NORBGDPMOM? — daily ones only. Also: BAMLH0A0HYM2 (hy yield), BAMLEMHBHYCRPIOAS (lem oas),
   NFCI (weekly financial conditions), STLFSI4 (weekly), VIXCLS have.
4. World Bank / FRED international: daily FX for INR, BRL, ZAR, MXN, KRW, SGD, SEK, NOK via
   DEXINUS, DEXBZUS, DEXSFUS, DEXMXUS, DEXKOUS, DEXSIUS, DEXSEUS, DEXNOUS (FRED daily 2006+).
5. If a source is blocked, DOCUMENT the block and move on — do not burn calls.
6. From any NEW series that lands: build spread/momentum/reversal engines per the harness gates
   (e.g. soft-commodity complex spreads, energy crack spreads [gas x wti], propane-gas spread,
   grain spreads, EM-FX basket momentum, broad-dollar momentum, NFCI-gated books).

NOTES: save raw downloads under tools/quant/data/<newdir>/ with a README.md (source, license-free
status, date fetched). Engines follow ALL gates incl. decorrelation vs current blend.

HONESTY: All gates in GOAL100_AGENT_BRIEF.md. Document every blocked source in FINDINGS.md.
