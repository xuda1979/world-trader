#!/usr/bin/env python3
"""AUDIT_CHAMP3 TASK D: floored-monitor false-breach mechanism."""
import subprocess, os
ROOT = "/Users/daxu/software/world-trader"
# 1) python exit code when the script path does not resolve
cp = subprocess.run(["python3", "tools/quant/hedge_fund_strats/monitor_tbill_floor.py"], cwd="/tmp", capture_output=True, text=True)
print("monitor invoked from WRONG cwd -> rc =", cp.returncode)
print("  stderr:", cp.stderr.strip()[-160:])
# 2) correct cwd (monitor is read-only: reads data_fred/tbill3m.csv, prints, exits)
cp = subprocess.run(["python3", "tools/quant/hedge_fund_strats/monitor_tbill_floor.py"], cwd=ROOT, capture_output=True, text=True)
print("monitor invoked from ROOT -> rc =", cp.returncode)
print(cp.stdout.strip())
# 3) every logged reading
import glob
logs = sorted(glob.glob(os.path.join(ROOT, "tools/logs/floored-*.log")))
ok = breach = 0
for p in logs:
    t = open(p).read()
    ok += t.count("floor health = OK")
    breach += t.count("!! FLOOR BREACH")
print("logs=%d  floor-health-OK readings=%d  !FLOOR BREACH lines=%d" % (len(logs), ok, breach))
