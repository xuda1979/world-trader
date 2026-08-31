"""Coordinator: pre-FOMC drift (Lucca-Moench 2013) on SPX 2008-2026 + risk-arb around it.
FOMC dates parsed from federalreserve.gov calendars (2008-2026). Pre-FOMC = long SPX
from close of day before FOMC day 1 to close of last FOMC day (2-day meetings).
Also: holiday pre-drift, opex week. All T+1, 6bps, trailing vt10, honest gates + calendar scramble."""
import sys, re
sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.agents.B2_highfreq.gates import vol_target, full_stats

import subprocess
html=subprocess.run(['curl','-s','-m','20','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm',
  '-H','User-Agent: Mozilla/5.0'],capture_output=True,text=True).stdout
# FOMC meeting dates appear like "January 26–27" (en-dash) or "April 30–May 1"
pat=re.findall(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\D{1,3}(\d{1,2})',html)
mon={'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}
dates=[]
for m1,d1,d2 in pat:
    y=html.find(f'{m1} {d1}')
    # year inference: search nearest year tag before... simpler: meetings are ordered in html per year headings
    dates.append((m1,int(d1),int(d2)))
print(f"parsed {len(dates)} meetings from current page (2026 backwards ~10y); need historical too")
# Historical: use the 2013-2026 page archive
print("sampling:", dates[:3], dates[-3:])
