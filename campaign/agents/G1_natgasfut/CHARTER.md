# G1_natgasfut — close the natgas spot->futures basis gap (champion's biggest sleeve risk)
The champion natgas sleeves trade FRED Henry Hub SPOT prints. Live execution = futures (NG)
with basis/roll. NO futures series exists on disk. Mission:
1. Try to fetch natgas front-futures daily from free sources reachable here (stooq blocked,
   Yahoo blocked). If none reachable, PROVE it and stop.
2. If no data: quantify HOW BIG basis risk could be: typical |spot-futures| basis range
   (cite literature values); translate to SR haircut range for the weekday effect.
3. Also test: does the weekday effect survive on MONTHLY-average spot series (M1/M2
   contracts proxy)? Whatever is possible honestly.
Write campaign/agents/G1_natgasfut/FINDINGS.md. Last line: ROUND DONE
