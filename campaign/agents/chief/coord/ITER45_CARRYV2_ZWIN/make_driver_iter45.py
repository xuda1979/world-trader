"""make_driver_iter45.py - derive driver_iter45.py from driver_iter44.py (session 25).
ITER45_CARRYV2_ZWIN slice-2 seal; precommit b9efa7675f95cdeb. Pattern: 37/42 derivation-by-
substitution, every anchor asserted to occur EXACTLY once, residual sweeps, py_compile gate."""
import py_compile, hashlib, os
SRC = '/Users/daxu/software/world-trader/campaign/agents/chief/coord/ITER44_CARRYV2_BOOKTGT/driver_iter44.py'
OUT = '/Users/daxu/software/world-trader/campaign/agents/chief/coord/ITER45_CARRYV2_ZWIN'
src = open(SRC).read()
pairs = []
def sub(old, new):
    pairs.append((old, new))
sub('OUT = ROOT + "/campaign/agents/chief/coord/ITER44_CARRYV2_BOOKTGT"',
    'OUT = ROOT + "/campaign/agents/chief/coord/ITER45_CARRYV2_ZWIN"')
sub("    s = build_carryv2(tgt)", "    s = build_carryv2(zwin)")
sub('PRECOMMIT_SHA = "0c1ef55af88b6cd2"', 'PRECOMMIT_SHA = "c825c1e0477a80ff"')
sub('ARMS = (0.07, 0.08, 0.09)', 'ARMS = (63, 126, 252)')
sub('ANCHOR_TGT = 0.08', 'ANCHOR_TGT = 126')
sub('def build_carryv2(tgt):', 'def build_carryv2(zwin):')
sub("    z = (spr - spr.rolling(126).mean()) / spr.rolling(126).std()",
    "    z = (spr - spr.rolling(zwin).mean()) / spr.rolling(zwin).std()")
sub("    sleeve = (m * (tgt / rv).clip(0, 3)).fillna(0)",
    "    sleeve = (m * (0.08 / rv).clip(0, 3)).fillna(0)")
sub('log("A1 anchor recon (tgt=0.08 re-type vs committed CSV): ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okA, devA, niA, ncA))',
    'log("A1 anchor recon (zwin=126 re-type vs committed CSV): ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okA, devA, niA, ncA))')
sub("for tgt in ARMS:", "for zwin in ARMS:")
sub("    streams[tgt] = s", "    streams[zwin] = s")
sub("    results[tgt] = rec", "    results[zwin] = rec")
sub('    log("ARM TGT=%.2f: rows=%d k=%d projid=%.3e IS-SR=%.6f IS-MDD=%.4f pct negyrs=%d Wmax_sf=%.4fx grossmax=%.9f" % (tgt, nrows, kcov, rec["proj_id"], rec["is_sr"], rec["is_mdd"] * 100, rec["ny"], rec["wmax_sf"], rec["gmax"]))',
    '    log("ARM ZWIN=%d: rows=%d k=%d projid=%.3e IS-SR=%.6f IS-MDD=%.4f pct negyrs=%d Wmax_sf=%.4fx grossmax=%.9f" % (zwin, nrows, kcov, rec["proj_id"], rec["is_sr"], rec["is_mdd"] * 100, rec["ny"], rec["wmax_sf"], rec["gmax"]))')
sub('    s.to_frame("ret").to_csv(OUT + "/arm_tgt%s_stream.csv" % str(tgt).replace(".", ""))',
    '    s.to_frame("ret").to_csv(OUT + "/arm_zwin%s_stream.csv" % str(zwin))')
sub('    rec["relw"].to_frame("relw").to_csv(OUT + "/arm_tgt%s_weights.csv" % str(tgt).replace(".", ""))',
    '    rec["relw"].to_frame("relw").to_csv(OUT + "/arm_zwin%s_weights.csv" % str(zwin))')
sub("adm = [tgt for tgt in ARMS if tgt != ANCHOR_TGT",
    "adm = [zwin for zwin in ARMS if zwin != ANCHOR_TGT")
sub('       and results[tgt]["is_sr"] > BAR', '       and results[zwin]["is_sr"] > BAR')
sub('       and results[tgt]["is_mdd"] >= -0.06', '       and results[zwin]["is_mdd"] >= -0.06')
sub('       and results[tgt]["ny"] == 0', '       and results[zwin]["ny"] == 0')
sub('       and results[tgt]["wmax_sf"] <= 2.0 + 1e-9]', '       and results[zwin]["wmax_sf"] <= 2.0 + 1e-9]')
sub('    best = max(adm, key=lambda tgt: results[tgt]["is_sr"])',
    '    best = max(adm, key=lambda zwin: results[zwin]["is_sr"])')
sub('    log("REVEAL arm TGT=%.2f (IS-argmax of admitted), gear 1.0, n=%d (%s..%s)" % (best, len(net), str(net.index[0].date()), str(net.index[-1].date())))',
    '    log("REVEAL arm ZWIN=%d (IS-argmax of admitted), gear 1.0, n=%d (%s..%s)" % (best, len(net), str(net.index[0].date()), str(net.index[-1].date())))')
sub('    pd.DataFrame(dict(ret=net.values), index=net.index).to_csv(OUT + "/candidate_tgt%s_daily.csv" % str(best).replace(".", ""))',
    '    pd.DataFrame(dict(ret=net.values), index=net.index).to_csv(OUT + "/candidate_zwin%s_daily.csv" % str(best))')
sub('log(9 * chr(45) + " ITER44 carryv2 book-tgt sweep driver (2026-09-19 session 24). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " sealed BEFORE this run.")',
    'log(9 * chr(45) + " ITER45 carryv2 zwin slice-2 driver (2026-09-19 session 25). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " sealed BEFORE this run. Derived from driver_iter44.py by asserted substitutions; the build param carries zwin; book re-target frozen at 0.08.")')
n_applied = 0
for old, new in pairs:
    c = src.count(old)
    assert c == 1, "substitution anchor count %d (want 1) for: %s" % (c, old[:70])
    src = src.replace(old, new)
    n_applied += 1
assert "arm_tgt" not in src and "candidate_tgt" not in src, "stale tgt filenames remain"
assert src.count("rolling(126)") == 0, "stale rolling(126) remains"
assert src.count("ITER44_CARRYV2_BOOKTGT") == 0, "stale ITER44 path remains"
dst = os.path.join(OUT, 'driver_iter45.py')
with open(dst, 'w') as f:
    f.write(src)
py_compile.compile(dst, doraise=True)
print("applied %d substitutions; py_compile OK" % n_applied)
print("driver sha16", hashlib.sha256(open(dst,'rb').read()).hexdigest()[:16], "size", os.path.getsize(dst))
