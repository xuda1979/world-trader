"""Isolated re-run of HUNT_FXCARRY2's COMMITTED engine (no edits to their files).
Redirects their output globals to my work_r6 so their published artifacts are untouched.
Question: does committed code reproduce r5_results.json's gates dict (gates.sr vs top.sr)?"""
import sys, shutil, os
ROOT = "/Users/daxu/software/world-trader"
MINE = f"{ROOT}/campaign/agents/chief/coord/HUNT_CRYPTO2/work_r6/fxengine_rerun"
os.makedirs(MINE, exist_ok=True)
sys.path.insert(0, f"{ROOT}/campaign/scripts")
import importlib.util
spec = importlib.util.spec_from_file_location("fx5", f"{ROOT}/campaign/scripts/HUNT_FXCARRY2_round5.py")
fx5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fx5)
fx5.SLEEVES = MINE          # redirect CSV output
fx5.HERE = MINE             # redirect json output
rows = fx5.run_all(save=True, verbose=False)
import json
print("configs:", len(rows))
for r in rows:
    print(f"{r['name']:<18} gates.sr {r['gates']['sr']:+.4f}  top.sr {r['sr']:+.4f}  "
          f"equal={abs(r['gates']['sr']-r['sr'])<1e-12}  "
          f"gates.neg {r['gates']['neg_years']}  top.neg {r['neg']}  "
          f"gates.h1 {r['gates']['h1']:+.3f} top.h1 {r['h1']:+.3f}  v2_pass {r['v2_pass']}")
