# G5_verifier — build the AUDIT HARNESS as permanent code
Write campaign/audit_harness.py: given sleeve CSV + construction script, checks:
(1) script runs, reproduces CSV byte-exact; (2) T+1: corr(signal(t), ret(t)) vs ret(t+1),
flags same-day entry; (3) zero-run report; (4) embedded costs == turnover*6bps;
(5) vol-target shift(1) verified. Run on ALL 14 champion sleeves, produce PASS/FAIL table.
Write FINDINGS.md with the table. Last line: ROUND DONE
