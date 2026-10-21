"""T7 end-state: after the R4 rotation, EVERY charter-10 target is resolved
on disk with a matching manifest row. (The original test_r4.T7 guarded the
pre-round premise -- 5 cleared / 5 to rotate; that run happened, so this file
asserts the completion invariant instead of weakening the original.)"""
import csv
import os

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
D = f"{ROOT}/tools/quant/data/more_etf"
CHARTER10 = {"HYG", "EWC", "EIS", "TUR", "DBE", "EPHE", "USCI", "COPX",
             "DBP", "ENOR"}
PRE_CLEARED_R3 = {"HYG", "EWC", "DBE", "DBP", "USCI"}
ROTATED_R4 = {"EIS", "TUR", "EPHE", "COPX", "ENOR"}


def test_t7done_partition_is_exact():
    assert PRE_CLEARED_R3 | ROTATED_R4 == CHARTER10
    assert not (PRE_CLEARED_R3 & ROTATED_R4)


def test_t7done_all_ten_pass_and_match_disk():
    with open(f"{D}/manifest.csv") as f:
        rows = {r["symbol"]: r for r in csv.DictReader(f)}
    for sym in sorted(CHARTER10):
        r = rows[sym]
        assert r["status"] in ("PASS", "PASS_WAIVER"), f"{sym}: {r['status']}"
        df = pd.read_csv(f"{D}/{sym}.csv")
        assert len(df) == int(r["rows"]), sym
        assert df["date"].iloc[0] == r["start"], sym
        assert df["date"].iloc[-1] == r["end"], sym
        assert r["span_class"] in ("pre2007", "2007plus"), sym
