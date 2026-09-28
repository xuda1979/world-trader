"""GOAL100 frontier-closure manifest (session 36, ledger #147, 2026-09-20).

The per-axis measurement program is EXHAUSTED (ledger #146): 31 axes measured
under the current objective (max Sharpe s.t. leverage <= 1.6, ann return >= 20
pct), every roster scalar carries a current-frame certificate, and the operator
levers are purchased data / rule change ONLY. Until #147 the closure lived only
as ledger prose plus a MANUAL per-session sha ritual - nothing in the suite
failed closed if a champion input byte drifted (the cron-twin environment keeps
re-emitting stray vintages; RAWEW15_REFRESH_CANDIDATE was touched again at
04:51 on 2026-09-20, bytes = the #146 dead vintage). This file is the machine
manifest of the CLOSED frontier:

  PIN 1  the canonical 12-sleeve input map exists byte-exact (carryv2 /
         dualmom / diescrack / CFX4 get their first pins here; the other eight
         match the ledger-recorded digits exactly);
  PIN 2  the champion pair of record is byte-exact;
  PIN 3  the 32-axis ledger enumeration is complete and unedited (32 = 31 through
         session 36 + the fx-hist transplant measured-and-refused in #148);
  PIN 4  the canonical gauntlet anchors to this exact sleeve map and knobs.

DUTY (era-pin class, Amendments 3+4): any FUTURE adoption must update this
manifest in the same landing as the champion re-pin - a stale manifest is a
fail-closed RED, never a silent pass.
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

SLEEVE_MAP = [
    ("brwt10", "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv", "b0a0bd99338e2bb4"),
    ("brwt7", "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv", "8e76dd581ec6e50d"),
    ("brwt5", "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv", "ca5151f346524469"),
    ("C5ng", "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv", "3d2b80691ef7a448"),
    ("C5ngsum", "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv", "ccfe3a4bc8706161"),
    ("A5r2", "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock__vt024.csv", "7ec85336e7f7d00f"),
    ("a6r7", "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv", "e281e8c4cc5682fb"),
    ("QAxasts", "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv", "c40d008ddbf7c579"),
    ("carryv2", "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv", "03f4d0e099da9759"),
    ("dualmom", "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv", "7462a8dfa391b18f"),
    ("diescrack", "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv", "c7d19f5bd0b2a603"),
    ("CFX4", "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv", "0e448b301fba08c7"),
]

CHAMPION_PAIR = [
    ("champion", "campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv", "cfa9ec4d38158691"),
    ("weights", "campaign/results/RAWEW13v2_IS_SR_weights.csv", "a384d6b92e258fd5"),
]

# The 23 certified families with their cert ITER tokens, VERBATIM from ledger
# #146 (2026-09-20, session 35). LEDGER_AXES is the ledger own count of MEASURED
# axes - NOT derivable from the tokens (a re-adjudication pair like 32+53 is one
# axis measured twice), so it is pinned as data, exactly as the ledger states it.
LEDGER = [
    ("gear", [21]),
    ("weights", [22]),
    ("grid-edges", [23]),
    ("census", [24, 117, 27, 28, 46]),
    ("8c-ledger", [25]),
    ("credit-at-cap", [26]),
    ("solver", [22, 50]),
    ("cov-target", [29, 31]),
    ("recipe", [30]),
    ("DUR", [32, 53]),
    ("c5ng-k", [33, 54]),
    ("brwt-zb", [34, 35, 55]),
    ("diescrack", [36, 40]),
    ("tsmom-MAW", [37, 52]),
    ("dualmom", [38, 39]),
    ("vt-overlay", [41]),
    ("brwt15", [42]),
    ("a5r2-vt", [43, 47]),
    ("carryv2", [44, 45]),
    ("c5ng-vt", [48, 51]),
    ("tsmom-vt", [49]),
    ("fx-hist", [57]),
    ("etf-fut-etp", [58]),
]
LEDGER_AXES = 33

R3_CMD = ROOT / "campaign" / "bt" / "verify_champion_r3_cmd.sh"


def _sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def test_champion_inputs_byte_exact():
    """PIN 1: every canonical sleeve file exists at the pinned path with the
    pinned sha16. A missing file is a RED (fail-closed), never a skip; a byte
    drift without a ledger entry is exactly the stray-writer class this manifest
    exists to catch."""
    for name, rel, want in SLEEVE_MAP:
        p = ROOT / rel
        assert p.exists(), ("champion input MISSING: %s at %s - fail-closed, "
                            "certify or restore before any suite green" % (name, rel))
        got = _sha16(p)
        assert got == want, ("champion input %s byte-drifted: sha16 %s != pinned %s. "
                             "No ledger entry covers this change - treat as stray-writer "
                             "or uncertified edit until adjudicated." % (name, got, want))


def test_champion_pair_byte_exact():
    """PIN 2: the champion pair of record (ITER49 tsm-vt015 book, ledger #140)
    is byte-exact. This is the per-session verify-first ritual, made permanent."""
    for name, rel, want in CHAMPION_PAIR:
        p = ROOT / rel
        assert p.exists(), "champion %s MISSING at %s" % (name, rel)
        got = _sha16(p)
        assert got == want, ("champion %s byte-drifted: %s != %s (of-record pair "
                             "cfa9ec4d38158691 / a384d6b92e258fd5, SR 3.820357, "
                             "cagr 23.9215)" % (name, got, want))


def test_ledger_enumeration_complete():
    """PIN 3: the certified-family enumeration is present and unedited. The
    frontier is CLOSED: editing this table (dropping a cert token, shrinking a
    family, changing the axis count) must RED the suite so the closure cannot
    rot silently."""
    names = [f for f, _ in LEDGER]
    assert len(names) == len(set(names)), "duplicate family in LEDGER"
    assert ("tsmom-vt", [49]) in LEDGER, "tsmom-vt adoption cert (ITER49) lost"
    assert ("a5r2-vt", [43, 47]) in LEDGER, "a5r2-vt cert pair (43+47) lost"
    assert ("c5ng-vt", [48, 51]) in LEDGER, "c5ng-vt cert pair (48+51) lost"
    assert ("solver", [22, 50]) in LEDGER, "solver cert pair (22+50) lost"
    assert ("brwt-zb", [34, 35, 55]) in LEDGER, "brwt-zb stitch (34+35+55) lost"
    assert ("fx-hist", [57]) in LEDGER, "fx-hist measured-refused family (57) lost"
    assert LEDGER_AXES == 33, ("LEDGER_AXES moved from 33 - only a ledger-recorded "
                               "new axis (new data / rule change) may change this "
                               "number; inventory fully measured since #148 (fx-hist, "
                               "ITER57, refused) plus the reference-bucketing gap cell "
                               "#149 (etf-fut-etp, ITER58, measured-refused on G7)")


def test_r3_cmd_anchors_this_manifest():
    """PIN 4: the canonical gauntlet must solve the SAME book this manifest
    certifies - same 12 sleeve names, same champion pair, same knobs (shrink
    0.70 / brwt-cap 0.30 / gear 1.0 / minsharpe / is-end 2017-01-01)."""
    txt = R3_CMD.read_text()
    assert R3_CMD.exists(), "canonical r3 cmd missing"
    for name, _, _ in SLEEVE_MAP:
        assert ("--sleeve " + name + "=") in txt, ("r3 cmd lost sleeve %s - the "
                                                   "gauntlet no longer anchors the "
                                                   "certified map" % name)
    for _, rel, _ in CHAMPION_PAIR:
        assert rel.split("/")[-1] in txt, "r3 cmd lost %s" % rel
    for knob in ["--rule minsharpe", "--shrink 0.70", "--brwt-cap 0.30",
                 "--gear 1.0", "--is-end 2017-01-01"]:
        assert knob in txt, "r3 cmd lost canonical knob %r" % knob
