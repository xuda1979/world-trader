import os, glob, json

ROOT = "/Users/daxu/software/world-trader/campaign"
EXCL = ["work_r","backup","snapshot","scratch","audit_backup","frozen",
        "_quarantine","QUARANTINED","internal_r","audit_r","_v8","pre_banner",
        "tests","fixtures","mini_champion"]
manifest=[]
# all clean <dir>/sleeves/*.csv
seen=set()
for d in sorted(glob.glob(os.path.join(ROOT,"**","sleeves"), recursive=True)):
    if any(x in d for x in EXCL):
        continue
    for csv in sorted(glob.glob(os.path.join(d,"*.csv"))):
        if csv.endswith(".meta"): continue
        rel=os.path.relpath(csv,ROOT)
        manifest.append(rel); seen.add(rel)
# curated validated sleeve library
lib="/Users/daxu/software/world-trader/campaign/results/sleeve_library"
for csv in sorted(glob.glob(os.path.join(lib,"*.csv"))):
    rel=os.path.relpath(csv,ROOT)
    if rel not in seen:
        manifest.append(rel)
with open("/Users/daxu/software/world-trader/campaign/work_backtest_oos/manifest.json","w") as f:
    json.dump(manifest,f,indent=1)
print("total strategies:", len(manifest))
