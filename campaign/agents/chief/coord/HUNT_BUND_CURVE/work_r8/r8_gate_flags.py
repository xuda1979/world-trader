#!/usr/bin/env python3
"""R8: full V2 gate-flag breakdown per BUND candidate, rebuilt from the SAVED net series
and SAVED positions (artifact-verifiable per GATES_CONTRACT_V2 section 10a).
Repro: python3 campaign/agents/chief/coord/HUNT_BUND_CURVE/work_r8/r8_gate_flags.py
"""
import sys, json, glob, os
import pandas as pd, numpy as np
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/campaign")
import bt.gates as bgates
OUT = ROOT + "/campaign/agents/chief/coord/HUNT_BUND_CURVE/work_r8"
CH = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
KEYS = ["sr","sr_ok","h1","h2","halves_ok","neg_years","worst","neg_ok","ac1","ac1_ok",
        "uniq","uniq_ok","corr","corr_ok","scr_p","scr_ok","leak_ok","beats_passive_ok","pass"]


def load(path, col=None):
    d = pd.read_csv(path, index_col=0, parse_dates=True)
    return d[col].astype(float) if col else d.iloc[:, 0].astype(float)


def main():
    champ = load(CH)
    spy = pd.read_csv(ROOT + "/tools/quant/data/twelvedata/SPY.csv", index_col=0,
                      parse_dates=True)["close"].astype(float).pct_change()
    ief = pd.read_csv(ROOT + "/tools/quant/data/more_etf/IEF.csv", index_col=0,
                      parse_dates=True)["close"].astype(float).pct_change()
    cta = load(ROOT + "/campaign/results/sleeve_library/CTA_15vol.csv", "ret")
    out = {}
    for f in sorted(glob.glob(OUT + "/series/*_net.csv")):
        n = os.path.basename(f).replace("_net.csv", "")
        net = load(f, "ret").dropna()
        we = pd.read_csv(OUT + "/series/" + n + "_positions.csv", index_col=0, parse_dates=True)
        sig = we.abs().sum(axis=1).reindex(net.index).fillna(0.0)
        r_pu = (net / sig.replace(0.0, np.nan)).replace([np.inf, -np.inf], 0.0).fillna(0.0)
        gr = bgates.run(r_pu, ref=champ, sig=sig, leak_check=True, scramble_n=200,
                        beats_passive=True, spy=spy, ief=ief, cta=cta)
        out[n] = {k: (float(gr[k]) if isinstance(gr.get(k), (int, float, np.floating))
                      else gr.get(k)) for k in KEYS}
        out[n]["leak"] = gr.get("leak")
        out[n]["beats_passive"] = {k: v for k, v in (gr.get("beats_passive") or {}).items()
                                   if k != "detail"}
        print("[%s] pass=%s sr_ok=%s halves_ok=%s neg_ok=%s(neg=%d worst=%.3f) corr_ok=%s(%+.4f) "
              "scr_ok=%s(p=%.3f) leak_ok=%s bp_ok=%s" % (
                  n, gr["pass"], gr["sr_ok"], gr["halves_ok"], gr["neg_ok"], gr["neg_years"],
                  gr["worst"], gr["corr_ok"], gr["corr"], gr["scr_ok"], gr["scr_p"],
                  gr.get("leak_ok"), gr.get("beats_passive_ok")))
        print("      sr=%.3f h1=%.2f h2=%.2f ac1=%.3f uniq=%.3f leak=%s" % (
            gr["sr"], gr["h1"], gr["h2"], gr["ac1"], gr["uniq"], gr.get("leak")))
    json.dump(out, open(OUT + "/r8_gate_flags.json", "w"), indent=1, default=str)
    print("saved -> " + OUT + "/r8_gate_flags.json")


if __name__ == "__main__":
    main()
