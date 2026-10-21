#!/usr/bin/env python3
"""HUNT_SECTOR2 R2 definitive gate block: each arm's scan headliner through the FULL
GATES_CONTRACT.md gauntlet (200x scramble, plateau on the arm's scan surface, halves,
yearly, corr-vs-champion, sleeve-library decorrelation). Run after
hunt_sector2_r2_scan.py (reads its pickle + CSV)."""
import sys
import pickle
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import hunt_sector2_r2_harness as H
import hunt_sector2_lib as L

with open("/tmp/sector2_r2_store.pkl", "rb") as f:
    STORE = pickle.load(f)
NETS, WS = STORE["nets"], STORE["ws"]
SCAN = pd.read_csv("/tmp/sector2_r2_scan.csv")

HEAD = {
    "A_rs_ratio":  "A|lb252|k4|long",
    "B_barbell":   "B|m21|mean100|IEFhalf",
    "C_xle_crud":  "C|w126|switch",
    "D_xlu_ief":   "D|lb21|riskoff|IEF",
}
# plateau surface = the arm's scan variants (whole-arm surface; chosen must sit on it)
SURF = {"A_rs_ratio": "A|", "B_barbell": "B|", "C_xle_crud": "C|", "D_xlu_ief": "D|"}


def build_rets():
    bookA = L.book_rets(H.S9, extra=["SPY"])
    bookA = bookA[bookA.index >= H.START]
    bookB = L.book_rets(H.RISK + H.DEF, extra=["IEF"])
    bookB = bookB[bookB.index >= H.START]
    bookC = L.book_rets(["XLE"], extra=["USO", "DBC"])
    bookC = bookC[bookC.index >= H.START]
    retsC = bookC[["XLE"]].copy()
    retsC["IEF"] = L.etf_ret("IEF").reindex(bookC.index)
    bookD = L.book_rets(H.S9, extra=["IEF"])
    bookD = bookD[bookD.index >= H.START]
    return {
        "A": bookA[H.S9],
        "B": bookB[H.RISK + H.DEF + ["IEF"]],
        "C": retsC[["XLE", "IEF"]],
        "D": bookD[H.S9 + ["IEF"]],
    }


RETS = build_rets()


def report(name, variant):
    w, net = WS[variant], NETS[variant]
    arm = variant.split("|")[0]
    surface = {r.variant: float(r.sr)
               for r in SCAN[SCAN.variant.str.startswith(arm + "|")].itertuples()}
    g = H.gates(name, w, RETS[arm], sr_by_param=surface, chosen=variant, save=True)
    return g


if __name__ == "__main__":
    print("=" * 108)
    print("DEFINITIVE GATE BLOCK (200x scramble, plateau on full-arm scan surface)")
    print("=" * 108)
    results = {}
    for arm, variant in HEAD.items():
        results[arm] = report(arm, variant)
    print("\n=== FINAL ===")
    for arm, g in results.items():
        print(f"{g['name']:14s} SR={g['sr']:.3f} ann={g['ann']:.1f}% H1={g['h1']} H2={g['h2']} "
              f"negyr={g['neg_yr']}/{g['n_yr']} worst={g['worst']}% corr={g['corr_champ']} "
              f"lib={g['lib']['maxabs']:.2f} scr_p={g['scramble_p']:.3f} "
              f"plateau={g['plateau']} -> {g['verdict']}")
