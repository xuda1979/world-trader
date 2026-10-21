"""HUNT_COT2 R6 fraud-catch: re-execute HUNT_CREDIT2's R5 pipeline OFFLINE with
save_sleeve no-op'd (their files untouched). Capture the full V2 battery dict incl.
scr_p (which their metas never serialized)."""
import sys, json
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import HUNT_CREDIT2_round5 as M
M.save_sleeve = lambda *a, **k: None          # fail-safe: never write their sleeves/
res = M.main()
out = {}
for k, v in res.items():
    v2 = v.get('v2', {})
    out[k] = dict(local_sr=v.get('sr'), v2_sr=v2.get('sr'), scr_p=v2.get('scr_p'),
                  leak_ok=v2.get('leak_ok'), bp_ok=v2.get('beats_passive_ok'),
                  pass_=v2.get('pass'))
json.dump(out, open('/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_COT2/r6/credit2_rerun_battery.json','w'), indent=1)
srs = sorted((v['local_sr'], k) for k, v in out.items())
print(f"\nRERUN: n={len(out)} local_sr range {srs[0][0]:+.3f}..{srs[-1][0]:+.3f} ({srs[-1][1]})")
best = max(out.items(), key=lambda kv: kv[1]['v2_sr'] or -9)
print(f"BEST v2_sr: {best[0]} v2_sr={best[1]['v2_sr']:.4f} scr_p={best[1]['scr_p']}")
