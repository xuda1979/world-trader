# CHAMP_DATA_FRESH — data freshness / coverage / regression audit of the 12 sleeve inputs

Champion sleeves (12, in rawew13v2_build.py POOL+NEW): brwt10/7/5, C5ng, C5ngsum, A5r2, a6r7,
QAxasts, carryv2, dualmom, diescrack, CFX4. Today is 2026-09-14.

Your job:
1. For each of the 12 sleeve CSVs, report the LAST non-zero/trading date and the gap to 2026-09-12.
   Flag any sleeve truncated/missing recent weeks.
2. Coverage: report each sleeve's start date and the IS-window (<2017) row count; flag any sleeve
   with insufficient <2017 coverage (affects weight fit).
3. Data-provenance: for each sleeve, identify the underlying source (CL/NG/SPY/bond/fx/gold/fails-
   to-deliver/etc.) and whether that source on disk (tools/quant/data/*) is newer than the sleeve
   tail (then a refresh is possible but NETWORK-LIMITED here — just document it).
4. Regression: confirm all 12 sleeve files are byte-stable (identical to what build() reads on a
   fresh run) and that build() --verify is still IDENTICAL.

Output: FINDINGS.md — a freshness/coverage table, flag any data that could be refreshed, and a
verdict on whether any visibly-stale sleeve threatens the champion's current tail.
Note: do NOT fetch network data (this env is proxy-flaky); document, measure, report.
Last line: CHAMP_DATA_FRESH DONE
