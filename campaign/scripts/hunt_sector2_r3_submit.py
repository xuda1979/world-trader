#!/usr/bin/env python3
"""HUNT_SECTOR2 round-3 item (a2): BLEND_CANDIDATE_SUBMISSION package for HUNT_VOL2's
blend charter.

Submits, AS-IS and with no re-fit:
  A11_rs_ratio#lb126k4  (round-2 Arm A honest ceiling, R2-verdict FAIL_SR only)
  COMP_invvol           (round-3 composite headliner, R3-verdict FAIL_SR|FAIL_NEGYR)
  COMP_50_50_daily      (round-3 composite, worst-case-cost rebalance variant)
  COMP_60_40_daily      (round-3 composite, charter 60/40 split)

Each submission CSV gets a companion .meta stamped BLEND_CANDIDATE_SUBMISSION with
measured own-span corr/vol/SR + A11-vs-COMP corr so the blend lane can pick decorrelated
members. COMP files are byte-identical (hash-pinned) copies of this agent's own sleeves
-- HUNT_VOL2 already ingested pre-fix copies of the COMP_* files and a CORRUPTED
COMP_invvol.csv (weights-as-returns overflow, own_ann 2.9e+20, REJECT_UNUSABLE_FILE);
the fixed originals live here and are re-offered with the fix documented.

Output: sleeves/blend_submit/{name}.csv + {name}.csv.meta + MANIFEST.json
Repro:  python3 campaign/scripts/hunt_sector2_r3_submit.py
"""
import hashlib
import json
import os
import shutil
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/scripts")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2")
import hunt_sector2_lib as L          # noqa: E402
import hunt_sector2_r3 as R           # noqa: E402

SD = f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2/sleeves"
OUT = f"{SD}/blend_submit"
CANDS = ["A11_rs_ratio#lb126k4", "COMP_invvol", "COMP_50_50_daily", "COMP_60_40_daily"]


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(OUT, exist_ok=True)
    ser = {c: R.load_sleeve(c) for c in CANDS}
    j = pd.concat({c[:6]: ser[c] for c in CANDS}, axis=1, join="inner").dropna()

    # pairwise corr matrix on the common overlap (for the blend lane's pick-one)
    cm = j.corr().round(3)

    man = {"label": "BLEND_CANDIDATE_SUBMISSION", "from": "HUNT_SECTOR2",
           "to": "HUNT_VOL2 blend charter (round-3 lane)", "date": "2026-09-07",
           "note": ("AS-IS published NET series, no re-fit. COMP_* are the post-fix "
                    "re-emission of the round-3 composite (the dead 429-killed session "
                    "had written a corrupted COMP_invvol.csv -- weights-as-returns "
                    "overflow, own_ann 2.9e+20 -- which HUNT_VOL2 correctly rejected "
                    "UNUSABLE; fixed series here, hashes pinned)."),
           "pairwise_corr_overlap": cm.to_dict(),
           "overlap_n": int(len(j)),
           "candidates": {}}

    for c in CANDS:
        s = ser[c]
        st = L.stats(s)
        mdd = float((1 + s).cumprod().div(
            (1 + s).cumprod().cummax()).min() - 1) * 100
        cc = L.corr_champ(s)
        lib = L.corr_library(s)
        src = f"{SD}/{c}.csv"
        dst = f"{OUT}/{c}.csv"
        shutil.copyfile(src, dst)
        sha = sha256_file(dst)
        meta = (f"label=BLEND_CANDIDATE_SUBMISSION\nname={c}\nfrom=HUNT_SECTOR2\n"
                f"to=HUNT_VOL2 blend charter round-3 lane\ndate=2026-09-07\n"
                f"sha256={sha}\n"
                f"n={st['n']} start={s.index.min().date()} end={s.index.max().date()}\n"
                f"sr={st['sr']:.3f} ann={st['ann']:.2f} vol={st['vol']:.2f} "
                f"mdd={mdd:.2f}\n"
                f"h1={st['h1']:.2f} h2={st['h2']:.2f} neg_yr={st['neg_yr']}/{st['n_yr']} "
                f"worst={st['worst']:.1f}\n"
                f"corr_champ={cc:.3f} lib_maxabs={lib['maxabs']:.2f} "
                f"(top: {', '.join(f'{k} {v:+.2f}' for k, v in list(lib['top'].items())[:2])})\n"
                f"own_verdict="
                f"{'FAIL_SR only (R2 honest ceiling)' if c.startswith('A11') else 'FAIL_SR|FAIL_NEGYR (R3 composite)'}\n"
                f"cost=6.4bps one-side FULL |dW| + 0.5%/yr borrow, T+1, trailing VT10 clip3 "
                f"(composites: allocation-level 6.4bps + day-0 entry, VT on weighted book)\n"
                f"rationale={('RS-ratio rotation, literal 11-SPDR charter set, lb126/k4, weekly, '
                              'VT10. Sector cross-sectional momentum vs SPY: real (scramble p=0.000) but '
                              'SR 0.679 < 1.0 gate. Dividend-yield-free long book, tier EASY borrow.') if c.startswith('A11') else
                             ('Allocation-level composite of two PUBLISHED round-2 sleeves (A11 + B_barbell), '
                              'no new signal params. Legs correlate 0.718 -> composite SR 0.65 <= A11 0.679; '
                              'SR>=1.0 needs rho<=-0.25. Scramble p=0.010 on the corr/vol-matched random-leg '
                              'control.')}\n")
        with open(f"{dst}.meta", "w") as f:
            f.write(meta)
        man["candidates"][c] = {
            "sha256": sha[:16], "n": int(st["n"]),
            "lib_top": list(lib["top"].items())[:2],
            "sr": round(st["sr"], 3), "ann": round(st["ann"], 2),
            "vol": round(st["vol"], 2), "mdd": round(mdd, 2),
            "h1": round(st["h1"], 2), "h2": round(st["h2"], 2),
            "neg_yr": f"{st['neg_yr']}/{st['n_yr']}", "worst": st["worst"],
            "corr_champ": round(float(cc), 3), "lib_maxabs": round(lib["maxabs"], 2),
        }
        print(f"submitted {c:22s} n={st['n']:5d} SR={st['sr']:.3f} ann={st['ann']:5.2f}% "
              f"vol={st['vol']:5.2f}% mdd={mdd:6.2f}% negyr={st['neg_yr']}/{st['n_yr']} "
              f"corr_champ={cc:+.3f} lib={lib['maxabs']:.2f} sha={sha[:16]}")

    with open(f"{OUT}/MANIFEST.json", "w") as f:
        json.dump(man, f, indent=1)
    print(f"\npairwise corr on common overlap (n={len(j)}):")
    print(cm.to_string())
    print(f"\nwrote {OUT}/MANIFEST.json + 4 csv + 4 csv.meta")


if __name__ == "__main__":
    main()
