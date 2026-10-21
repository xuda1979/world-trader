"""R3(b) reconciliation evidence probes — all claims verified before manifest edits."""
import csv, datetime as dt, sys
from collections import Counter
sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/more_fred")
import fred_dl

MFRED = "/Users/daxu/software/world-trader/tools/quant/data/more_fred"

def load(sid):
    with open(f"{MFRED}/{sid}.csv") as f:
        return [(r[0], float(r[1])) for r in list(csv.reader(f))[1:]]

# --- MORTGAGE30US ---
m = load("MORTGAGE30US")
d = [dt.date.fromisoformat(x[0]) for x in m]
sp = [(d[i+1]-d[i]).days for i in range(len(d)-1)]
print("MORTGAGE30US n=%d %s..%s max_spacing=%d" % (len(m), d[0], d[-1], max(sp)))
print("  spacing histogram:", dict(sorted(Counter(sp).items())))
print("  weekday dist:", dict(sorted(Counter(x.weekday() for x in d).items())))
lr = fred_dl.lint(m, freq="weekly", holiday_tol_days=3)
print("  lint weekly tol3:", {k: lr[k] for k in ("n", "gaps", "pass", "reason")})

# --- GFDEGDQ188S ---
g = load("GFDEGDQ188S")
gd = [dt.date.fromisoformat(x[0]) for x in g]
slots, y, mo = [], gd[0].year, gd[0].month
while (y, mo) <= (gd[-1].year, gd[-1].month):
    slots.append(dt.date(y, mo, 1)); mo += 3
    if mo > 12: y, mo = y+1, mo-12
missing = [s for s in slots if s not in set(gd)]
offgrid = [x for x in gd if not (x.month in (1,4,7,10) and x.day==1)]
print("GFDEGDQ188S n=%d %s..%s slots=%d missing=%d offgrid=%d" % (
    len(g), gd[0], gd[-1], len(slots), len(missing), len(offgrid)))
print("  detect_freq:", fred_dl.detect_freq(g), " lint(q):", fred_dl.lint(g, freq="quarterly"))

# --- TEDRATE: find all contiguous missing-bday runs >=2 ---
t = load("TEDRATE")
td = set(dt.date.fromisoformat(x[0]) for x in t)
missing_b = [x for x in fred_dl._bdays(dt.date(1986,1,2), dt.date(2022,1,21)) if x not in td]
runs, cur, start, best = [], 0, None, None
prev = None
for x in missing_b:
    if prev is not None and (x - prev).days == 1:
        cur += 1
    else:
        if cur >= 2: runs.append((start.isoformat(), cur))
        start, cur = x, 1
    prev = x
if cur >= 2: runs.append((start.isoformat(), cur))
print("TEDRATE missing-bday runs>=2:", runs)
print("  1986-01-20 in missing:", dt.date(1986,1,20) in td)
