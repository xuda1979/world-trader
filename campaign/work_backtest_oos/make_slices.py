"""Partition the master manifest into N disjoint agent slices (round-robin, disjoint)."""
import os, json, sys
OUT = "/Users/daxu/software/world-trader/campaign/work_backtest_oos/agent_work"
os.makedirs(OUT, exist_ok=True)
manifest = json.load(open("/Users/daxu/software/world-trader/campaign/work_backtest_oos/manifest.json"))
N = int(sys.argv[1]) if len(sys.argv)>1 else 12
# deterministic round-robin interleave -> each agent gets a scattered, disjoint sample
for i in range(N):
    slice_man = manifest[i::N]
    json.dump(slice_man, open(os.path.join(OUT, f"slice_{i}.json"),"w"))
    print(f"slice_{i}: {len(slice_man)}")
print("total:", len(manifest))
