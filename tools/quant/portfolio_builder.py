import json, math, os

def load_qualifying():
    p = os.path.join(os.path.dirname(__file__), "reports", "pairs_research.json")
    data = json.load(open(p))
    hl = data["experiments"]["half-life"]
    return [r for r in hl["top20"] if r["qualifies_fdr"]]

def build_portfolio(qual, method="risk_parity"):
    n = len(qual)
    if method == "equal_weight":
        w = [1.0/n]*n
    elif method == "risk_parity":
        inv = [1.0/max(q["oos_edge"],0.01) for q in qual]
        tv = sum(inv)
        w = [i/tv for i in inv]
    elif method == "sharpe_weighted":
        ss = [max(q["oos_edge"],0.01) for q in qual]
        ts = sum(ss)
        w = [s/ts for s in ss]
    else:
        w = [1.0/n]*n
    pe = sum(w[i]*qual[i]["oos_edge"] for i in range(n))
    pv = sum((w[i]*qual[i]["oos_edge"]/math.sqrt(max(qual[i]["oos_n"],1)))**2 for i in range(n))
    ps = math.sqrt(pv)
    psh = pe/ps if ps>0 else 0
    return {"method":method, "n":n, "port_edge":round(pe,3),
            "port_sharpe":round(psh,3),
            "weights":{qual[i]["label"]:round(w[i],4) for i in range(n)}}

if __name__ == "__main__":
    qual = load_qualifying()
    print(f"Qualifying pairs: {len(qual)}")
    for m in ["equal_weight","risk_parity","sharpe_weighted"]:
        pf = build_portfolio(qual, m)
        print(f"{m:15s}  n={pf["n"]}  edge={pf["port_edge"]:+.3f}  sharpe={pf["port_sharpe"]:+.3f}")
        for lbl,w in sorted(pf["weights"].items(), key=lambda x:-x[1]):
            print(f"  {lbl:20s} {w*100:5.1f}%")
    print()
    for p in qual:
        print(f"{p["label"]:20s} OOS={p["oos_edge"]:+.3f}  HL={p["half_life"]:.0f}  z={p["z_now"]:+.2f}  {"FIRE" if p["firing"] else ""}")