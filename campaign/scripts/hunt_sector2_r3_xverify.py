#!/usr/bin/env python3
"""HUNT_SECTOR2 round-3 item (b), completion: independent re-measure of BOTH published
HUNT_FXCARRY2 negatives from their sleeve CSVs.

hunt_sector2_r3.py already cross-verifies FXCARRY2_R2_carry_nominal_EW; this script adds
the R3 ddstop10 variant quoted in FINDINGS (SR=-0.089) so every cross-verify claim has a
saved repro. Read-only w.r.t. HUNT_FXCARRY2 (their directory is not modified).

Repro: python3 campaign/scripts/hunt_sector2_r3_xverify.py
"""
import sys

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/scripts")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2")
import hunt_sector2_lib as L          # noqa: E402

FXS = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/sleeves"
CLAIMS = {
    "FXCARRY2_R2_carry_nominal_EW": dict(sr=-0.0043, ann=-0.02, h1=-0.133, h2=0.164,
                                         negyr=11, nyr=23, worst=-19.4, corr=0.028,
                                         src="HUNT_FXCARRY2-R2 / DEAD_IDEAS row 65"),
    "FXCARRY2_R3_ddstop10_carry_EW": dict(sr=-0.089, ann=-0.26, h1=-0.18, h2=0.03,
                                          negyr=11, nyr=23, worst=-5.8, corr=0.021,
                                          src="HUNT_FXCARRY2-R3 / DEAD_IDEAS row 95"),
}


def main():
    for name, c in CLAIMS.items():
        s = pd.read_csv(f"{FXS}/{name}.csv", index_col=0, parse_dates=True
                        ).iloc[:, 0].astype(float)
        st = L.stats(s)
        cc = L.corr_champ(s)
        print(f"[{name}] n={st['n']} SR={st['sr']:.4f} ann={st['ann']:.2f}% "
              f"H1={st['h1']:.3f} H2={st['h2']:.3f} negyr={st['neg_yr']}/{st['n_yr']} "
              f"worst={st['worst']:.1f}% corr_champ={cc:.3f}")
        checks = [
            ("n", st["n"] == 5680),
            ("sr", abs(st["sr"] - c["sr"]) < 5e-4),
            ("ann", abs(st["ann"] - c["ann"]) < 0.05),
            ("halves", abs(st["h1"] - c["h1"]) < 0.01 and abs(st["h2"] - c["h2"]) < 0.01),
            ("negyr", st["neg_yr"] == c["negyr"] and st["n_yr"] == c["nyr"]),
            ("worst", abs(st["worst"] - c["worst"]) < 0.1),
            ("corr", abs(cc - c["corr"]) < 5e-3),
        ]
        bad = [k for k, ok in checks if not ok]
        verdict = "CONFIRMED" if not bad else f"MISMATCH({','.join(bad)})"
        print(f"    vs claim {c['src']}: SR {c['sr']} ann {c['ann']}% "
              f"H=({c['h1']},{c['h2']}) negyr {c['negyr']}/{c['nyr']} worst {c['worst']}% "
              f"corr {c['corr']} -> {verdict}")
        assert not bad, f"{name}: cross-verify failed on {bad}"
    print("\nBOTH FXCARRY2 negatives CONFIRMED by independent re-measure.")


if __name__ == "__main__":
    main()
