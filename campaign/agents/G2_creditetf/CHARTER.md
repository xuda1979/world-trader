# G2_creditetf — rebuild credit sleeves at REAL ETF cost
A5r7/A1credit use synthetic BAA/HY total returns (no ETF fee, no spread crossing). Rebuild:
1. Check twelvedata/twelve_big for LQD/HYG/AGG (ls | grep -i). Use what exists.
2. Rebuild A1credit long-flat book with ETF prices + 6-10bps + ETF fee: still passes?
3. Same for A5r7 credit legs. Report SR before/after real instruments.
Write FINDINGS.md. Last line: ROUND DONE
