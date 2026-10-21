import json,os,sys,re,glob; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"11_data_provenance","sleeves":[]}
print("=== 11 DATA PROVENANCE PER SLEEVE ===")
def vt_meta(rel):
    p=os.path.splitext(os.path.join(ROOT,rel))[0]+".csv.meta"
    return p if os.path.exists(p) else None
found_any=0
for s in D['sleeves']:
    b=os.path.basename(s)
    full=os.path.join(ROOT,s)
    meta=vt_meta(s)
    # date span & nonzero days of the sleeve stream itself
    import pandas as _pd
    d=_pd.read_csv(full,index_col=0,parse_dates=[0]); c="ret" if "ret" in d.columns else d.columns[0]
    dd=d[c].dropna()
    span=f"{dd.index.min().date()}->{dd.index.max().date()} ({len(dd)}d, {(dd!=0).sum()} nzd)"
    # find generator script mentioning the basename
    gen=None
    hits=glob.glob(os.path.join(ROOT,"campaign","scripts",b.replace('.csv','')+".py"))
    if not hits:
        for pat in ["campaign/agents","team/agents","results"]:
            pass
    # grep-ish: search likely agent dirs
    if not gen:
        for cand in glob.glob(os.path.join(ROOT,"**",b.replace('.csv','')+".py"),recursive=True):
            gen=os.path.relpath(cand,ROOT); break
    # raw data files referenced in the sleeve's directory scripts (best effort)
    raws=[]
    if gen:
        try: txt=open(os.path.join(ROOT,gen)).read()
        except: txt=""
        for m in list(set(re.findall(r"[\w/.\-]+\.(?:csv|parquet)", txt)))[:12]:
            for base in [ROOT, os.path.join(ROOT,"tools"), os.path.join(ROOT,"campaign")]:
                if os.path.exists(os.path.join(base,m)): raws.append(m); break
    okdata = len(dd)>1000 and (dd!=0).sum()>500
    R["sleeves"].append({"sleeve":b,"meta":bool(meta),"generator":str(gen),
        "raw_refs_found":[str(x) for x in raws[:5]],"span":span,"plausible":bool(okdata)})
    found_any += bool(gen)
    print(f"  {'OK ' if okdata else 'BAD'} meta={'Y' if meta else 'N'} gen={'Y' if gen else 'N'} raw={len(raws)} {b} [{span}]")
n_plaus=sum(1 for x in R["sleeves"] if x["plausible"])
R["checks"]=[{"check":"all sleeves plausible span/coverage","status":"PASS" if n_plaus==20 else "FAIL","detail":f"{n_plaus}/20"},
             {"check":"generators located","status":"PASS" if found_any>=15 else "WARN","detail":f"{found_any}/20"}]
R["overall"]="PASS" if n_plaus==20 else "FAIL"
json.dump(R,open("agents/agent11_report.json","w"),indent=2)
