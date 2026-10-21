#!/usr/bin/env python3
"""AUDIT_CHAMP2 R3(b) evidence script — costfix-drift attribution (charter: "any drift =
costfix-delta, documented not new-bug").

Claim 1 (weights-vs-builder): committed RAWEW13v2_IS_SR_weights.csv matches builder relw
    per column to 2.2e-16 (tol 1e-10).
Claim 2 (movers vs git HEAD): exactly {brwt15, QAxasts, dualmom, diescrack} differ; all
    other 9 columns byte-equal to HEAD 8f98da1.
Claim 3 (attribution EXACT): rebuilding with the 4 git-HEAD sleeve blobs substituted
    reproduces the HEAD (pre-costfix) champion to 9.996e-17 — i.e. 100% of the champion
    drift 39.8510% -> 39.6873% is the 4-sleeve costfix, zero new knobs.
"""
import io
import subprocess
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import pandas as pd  # noqa: E402

import scripts.rawew13v2_build as B  # noqa: E402

HEAD = "/Users/daxu"
MODIFIED_PATHS = {
    "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
}


def head_csv(rel):
    return subprocess.run(
        ["git", "show", f"HEAD:software/world-trader/{rel}"],
        capture_output=True, text=True, cwd=HEAD, check=True,
    ).stdout


def main():
    # Claim 1
    net, relw, gross, to, _ = B.build()
    com = pd.read_csv(f"{B.ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv",
                      index_col=0).iloc[:, 0]
    dev = (com - relw).abs()
    print(f"claim1 weights-vs-builder: maxdev={dev.max():.3e} n={len(com)} "
          f"{'PASS(<1e-10)' if dev.max() < 1e-10 else 'FAIL'}")

    # Claim 2
    hw = pd.read_csv(io.StringIO(
        head_csv("campaign/results/RAWEW13v2_IS_SR_weights.csv")), index_col=0).iloc[:, 0]
    d = (com - hw).astype(float)
    movers = set(d[d.abs() > 1e-12].index)
    print(f"claim2 movers-vs-HEAD: {sorted(movers)} expect {sorted(B.MODIFIED_EXPECT)}"
          if hasattr(B, "MODIFIED_EXPECT") else
          f"claim2 movers-vs-HEAD: {sorted(movers)} expect ['QAxasts','brwt15','diescrack','dualmom']")
    others_zero = bool(d.drop(list(movers)).abs().max() == 0) if len(d.drop(list(movers))) else True
    print(f"claim2 all 9 non-mover columns exactly 0 delta: {others_zero}")

    # Claim 3
    orig_load = B.load

    def load_mixed(p):
        if p in MODIFIED_PATHS:
            df = pd.read_csv(io.StringIO(head_csv(p)), index_col=0)
            df.index = pd.to_datetime(df.index)
            c = "ret" if "ret" in df.columns else df.columns[0]
            return df[c].astype(float)
        return orig_load(p)

    B.load = load_mixed
    net_h, _, _, _, _ = B.build()
    B.load = orig_load
    ch_h = pd.read_csv(io.StringIO(
        head_csv("campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")),
        index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([ch_h.rename("head_champ"), net_h.rename("rebuild")], axis=1).dropna()
    md = float((j.head_champ - j.rebuild).abs().max())
    ann_h = ((1 + ch_h).prod() ** (252 / len(ch_h)) - 1) * 100
    ann_r = ((1 + net_h.dropna()).prod() ** (252 / len(net_h.dropna())) - 1) * 100
    print(f"claim3 rebuild(4 HEAD sleeves) vs HEAD champion: maxdev={md:.3e} "
          f"ann {ann_r:.4f}% vs {ann_h:.4f}% "
          f"-> {'ATTRIBUTION EXACT' if md < 1e-12 else 'RESIDUAL UNEXPLAINED'}")


if __name__ == "__main__":
    main()
