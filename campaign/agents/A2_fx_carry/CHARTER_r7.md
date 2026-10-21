# A2 r7 — NEW FREE FX + macro data (data_fred_new/, 1990-2026)
New: DEXJPUS (1990+), DEXUSEU (1999+), DTWEXBGS dollar (2006+), DGS1/DGS2/DGS10 yield diff, DFF.
Missions (SR>=1.0, corr<0.25):
1. **FX carry with REAL 20y history** (was 2007-limited in r1): carry = short-rate diff (DGS2-DGS10
   proxies, or DFF/DTB3 diff), long high-yield currencies (JPY short, etc.), 1999-2026, vol-tgt 10%.
   Your r1 found FX carry weak on 2007+; test whether 1999-2026 full history (incl 2008, more cycles) helps.
2. **FX momentum on full 1990/1999 history**: JPY, EUR, GBP, AUD (from data/fx where available; extend via DEX).
3. **Dollar-fade**: DTWEXBGS 126d z-score fade (long risky when dollar cheap) - low corr to equity champion.
4. **Carry-trend blend**: carry when 63d trend agrees, flat otherwise - reduces whipsaw.
All gates. Append FINDINGS.md, last line ROUND r7 DONE.
