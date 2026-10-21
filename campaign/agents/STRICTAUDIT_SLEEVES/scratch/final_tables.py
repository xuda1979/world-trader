import pandas as pd, numpy as np
# Numbers for the verdict table: lag1 ac, max single-day, runs, halves (from mech_sanity.json)
import json
d = json.load(open('mech_sanity.json'))
print(f"{'name':9s} {'SRfull':>6} {'H1':>6} {'H2':>6} {'negYr':>5} {'MaxDD%':>7} {'max|d|%':>8} {'ac1':>6} {'lead0':>5} {'runs>=5':>8}")
for k,v in d.items():
    runs = v['runs_ge5']
    print(f"{k:9s} {v['SR_daily']:>6} {v['SR_h1']:>6} {v['SR_h2']:>6} {v['neg_years']:>3}/{v['n_years']:<3} {v['MaxDD_pct']:>7} {v['maxabsret_pct']:>8} {v['lag1_ac']:>6} {v['lead_zeros']:>5} {len(runs):>4} maxrun={max(runs) if runs else 0}")
