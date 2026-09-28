"""ITER30 reality-pins (2026-09-19, session #12): a6r7 RECIPE-HYPERPARAMETER family.

The #120-charted last unmeasured cell: the champion a6r7 sleeve own recipe knobs
(K / cadence / VT / CAP) swept 90 cells under pure IS-SR@gear-1.0 with the amended
gate set. VERDICT: 4/89 admitted (all CAD=21), ONE reveal of argmax (378,21,0.12,5.0)
- FS-SR 3.754071 PASSES the bar and ALL operator gates pass, but 5-bin OOS dSR is
2/5 positive -> G7 FAIL -> REJECT (ITER17 law kill #6). Champion byte-stable.

Pins assert on recorded artifacts (JSON + file bytes + log lines), never on a
pipeline exit code, per house rule.
"""
import hashlib
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER30 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER30_RECIPE_SWEEP")
CHAMP = os.path.join(ROOT, "campaign", "results", "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
WGT = os.path.join(ROOT, "campaign", "results", "RAWEW13v2_IS_SR_weights.csv")


def _sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def _read(path):
    with open(path) as fh:
        return fh.read()


def _json(name):
    with open(os.path.join(ITER30, name)) as fh:
        return json.load(fh)


def test_champion_of_record_is_adopted_iter43_blob():
    # Re-anchored at the 2026-09-19 ITER43 adoption (A5r2 VT-axis argmax VT=0.15): the
    # live champion of record is now 3c456aa53193eb89 / weights 8313bee1ad8a72fe (ITER47 vt024 re-pin 2026-09-19; was e67446186e269b88/bde8612d0b295068 through ITER46). The
    # ITER30-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER30 memo
    # (the champion WAS byte-stable through ITER30).
    assert _sha16(CHAMP) == "cfa9ec4d38158691"
    assert _sha16(WGT) == "a384d6b92e258fd5"


def test_iter30_seal_chain_disclosed():
    pre = _read(os.path.join(ITER30, "FINDINGS_PRECOMMIT.md"))
    assert _sha16(os.path.join(ITER30, "FINDINGS_PRECOMMIT.md")) == "aa4c7d1cab4a271b"
    assert "AMENDMENT 1" in pre and "AMENDMENT 2" in pre
    findings = _read(os.path.join(ITER30, "FINDINGS.md"))
    assert "93ecd55beb7fa4f5" in findings  # base seal cited in the chain
    assert "4507a4aefda10ba4" in findings and "aa4c7d1cab4a271b" in findings
    assert os.path.getmtime(os.path.join(ITER30, "FINDINGS_PRECOMMIT.md")) < os.path.getmtime(
        os.path.join(ITER30, "driver_iter30.log"))
def test_iter30_incumbent_cell_anchor_exact():
    cells = _json("cells.json")
    assert len(cells) == 90
    inc = [r for r in cells if tuple(r["cell"]) == (378, 42, 0.12, 5.0)]
    assert len(inc) == 1
    r = inc[0]
    assert abs(r["is_sr"] - 4.198632) < 1e-6
    assert abs(r["fs_sr"] - 3.751429) < 1e-6
    assert abs(r["wmax_sf"] - 1.8115) < 1e-3
    assert r["admitted"] is False  # the bar row is never a candidate
    assert all(r["gates"].values())  # amended gate E passes the incumbent


def test_iter30_admissions_are_monthly_cadence_only():
    cells = _json("cells.json")
    adm = sorted(tuple(r["cell"]) for r in cells if r.get("admitted"))
    assert adm == [(252, 21, 0.12, 5.0), (252, 21, 0.16, 5.0),
                   (378, 21, 0.12, 5.0), (378, 21, 0.16, 5.0)]
    assert all(c[1] == 21 for c in adm)


def test_iter30_reveal_rejected_on_oos_bins():
    v = _json("verdict.json")
    assert v["outcome"] == "REJECT" and v["adopted"] is False
    assert v["n_admitted"] == 4
    assert v["argmax_cell"] == [378, 21, 0.12, 5.0]
    assert v["causality_max_dev"] <= 1e-12
    rev = v["reveal"]
    assert abs(rev["stats"]["sr"] - 3.754071) < 1e-5  # FS bar PASSED
    assert rev["fs_gates"]["fs_sr_gt"] is True
    assert rev["fs_gates"]["bins"] is False  # the ONLY failed gate
    assert all(rev["fs_gates"][k] is True for k in
               ("cagr", "arith", "mdd", "negy", "worst", "gross"))
    bins = rev["bins"]
    assert sum(1 for b in bins if b > 0) == 2  # 2/5 -> G7 FAIL
    assert abs(bins[3] - (-0.019501239523522784)) < 1e-9


def test_iter30_driver_log_reproduces_verdict():
    log = _read(os.path.join(ITER30, "driver_iter30.log"))
    assert "VERDICT: REJECT - failed gates ['bins'] (sealed stop rule; no second reveal)" in log
    assert "ADMITTED 4/89" in log
    assert "ARGMAX cell=(378, 21, 0.12, 5.0) is_sr=4.199556" in log
    assert "INCUMBENT CELL: gen-vs-saved dev 0.000e+00  weights-vs-committed dev 8.327e-17" in log
    assert "causality probe max pre-probe dev: 0.000e+00" in log
