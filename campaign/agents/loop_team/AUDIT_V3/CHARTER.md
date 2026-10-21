# AUDIT_V3 — adversarial audit of the V3 champion + FF2 tradeability (iter 6)

You are an independent ADVERSARIAL auditor. The goal set: ann>=80%, SR>=5, MaxDD<=7%, capital-real
leverage<=1.6, profit>=0 every year, 6.4bps/side cost, call-rate at IBKR, some stocks not shortable.
AUDIT the NEW chFIRSTampion GOAL100_HONEST14V3 (14 engines) and specifically the 3rd new sleeve
FF2_DUALGATE added in iter5. Also re-audit the honesty of the leverage<=1.6 claim and the "0/19 neg
yrs" claim on the V3 file. This is READ-ONLY except your own dir (AUDIT_V3/).

TARGETS (exact, with numbers; for anything UNVERIFIABLE write UNVERIFIED explicitly):
1. BYTE-REPRO: run `python3 campaign/scripts/honest13_build.py --verify-v3` — confirm all 3 V3 CSVs
   max|diff|<1e-12. Also independently rebuild from the sleeve CSVs with your OWN loader (not the
   committed builder) and confirm the headline stats (ann 43.6/SR 3.92/MDD -4.92/0 neg).
2. FF2 TRADEABILITY (disclosed caveat in commit msg): FF2 uses DAILY FF factor data ending 2026-06-30
   (CRSP 202606), factor-proxy execution UNVERIFIED. Dig into it: is the FF2 sleeve's universe truly
   tradeable? What are the underlying holdings? Does it depend on FF factor values at dates where the
   factor data exists? Is 2026-06-30 end-date a problem for a 0/19-neg-yr claim through 2026-09? Flag
   if FF2 is research-only and quantify its contribution to the V3 numbers by re-running the builder
   with NEW3 minus FF2 (use honest13_build.py family() with NEW2) and reporting the delta.
3. LEVERAGE HONESTY: recompute capital-real gross leverage for the V3 BALANCED CSV from the builder's
   full-weight matrix. Confirm the 3.45x mean / p95 7.18x figure and the "at 1.6x ann caps at ~19%"
   statement. State clearly: does V3 violate the leverage<=1.6 goal? (It almost surely does — confirm
   honestly — and re-quote what HONEST11BALANCED/13 balanced achieve at real 1.6x.)
4. 0/19 NEG YRS SCOPING: reproduce the yearly returns on V3 from 2008+; confirm 0 negative. Also report
   the 2006-2007 warmup year(s) (the FINAL_STATE says 2006 stub is -1.4% pre-live warmup) — the goal
   "profit>=0 every year" must be stated with the 2008+ scope caveat. Report 2006-2007 magnitude.
5. COST/ CALL-RATE / SHORTABILITY: confirm costs are 6bps/side on ALL turnover (the goal says 6.4bps —
   flag the 0.4bps gap). Confirm borrow 0.5%/yr on short legs and note IBKR call rate and
   not-shortable-stocks caveats are NOT modeled (state honestly what is and isn't covered).
6. NEW phenomenology: any ac1>0.5 / <8% distinct-value RED-FLAG on ANY of the 14 sleeves (the XGB1y
   flattening trap). Sweep all sleeves.
Write FINDINGS.md with a verdict table (PASS/FAIL/UNVERIFIED per target). Do not modify strategy code.
Last line exactly: AUDIT_V3 DONE
