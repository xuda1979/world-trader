# make_driver_iter52.py - derive driver_iter52.py from driver_iter51.py by
# asserted-exactly-once substitutions (the make_driver_iter37.py law). py_compile gate.
import py_compile, hashlib

SRC = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/ITER51_C5NG_VT_READJ/driver_iter51.py"
DST = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/ITER52_TSMOM_MAW_READJ/driver_iter52.py"

SUBS = []
SUBS.append((
 '''OUT = ROOT + "/campaign/agents/chief/coord/ITER51_C5NG_VT_READJ"''',
 '''OUT = ROOT + "/campaign/agents/chief/coord/ITER52_TSMOM_MAW_READJ"'''))
SUBS.append((
 '''PRECOMMIT_SHA = "020a8e69de643117"''',
 '''PRECOMMIT_SHA = "0e4c271945a4be28"'''))
SUBS.append((
 '''log(9 * chr(45) + " ITER51 C5NG-VT STALENESS RE-ADJUDICATION driver (2026-09-20 session 31). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " sealed BEFORE this run.")''',
 '''log(9 * chr(45) + " ITER52 TSMOM-MAW STALENESS RE-ADJUDICATION driver (2026-09-20 session 32). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " sealed BEFORE this run.")'''))
SUBS.append((
 '''ARMS = (0.10, 0.06, 0.09, 0.12, 0.15)
ANCHOR_VT = 0.10
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
CNG_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv"
SUM_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv"
DHH = ROOT + "/tools/quant/data/newdata/DHHNGSP.csv"
COST_SLEEVE = 6e-4
MONTHS = list(range(4, 11))''',
 '''ARMS = (189, 126, 157, 220, 252)
ANCHOR_MAW = 189
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
TSM_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv"
VT_FROZEN = 0.15'''))
SUBS.append((
 '''DH.panel = _panel_d17
log("D17 pre-patch applied: harness data.panel wrapped (skip manifest.csv) (retained inert safety patch)")''',
 '''DH.panel = _panel_d17
import campaign.harness.data as DHF
def _panel_d17_full(extended=False):
    d = DHF.EXT if extended else DHF.PANEL
    out = dict()
    for f in os.listdir(d):
        if f.endswith(".csv") and f != "manifest.csv":
            out[f[:-4]] = pd.read_csv(os.path.join(d, f), parse_dates=["date"], index_col="date")
    return out
DHF.panel = _panel_d17_full
log("D17 Amendment-1 DUAL pre-patch applied (data + campaign.harness.data) BEFORE the r7/r6lib chain - LOAD-BEARING here: manifest.csv live in twelve_big (mtime Sep 8 14:40), probe run-1 died fail-closed on the single-identity form")'''))
SUBS.append((
 '''log("Champion sha16 pre-run: " + champ_sha_pre + " / weights " + wgt_sha_pre + " / precommit " + PRECOMMIT_SHA)''',
 '''log("Champion sha16 pre-run: " + champ_sha_pre + " / weights " + wgt_sha_pre + " / precommit " + PRECOMMIT_SHA)
assert (champ_sha_pre, wgt_sha_pre) == ("cfa9ec4d38158691", "a384d6b92e258fd5"), "driver must run against the ADOPTED pair untouched"'''))
SUBS.append((
 '''from campaign.agents.B2_highfreq.gates import vol_target

def build_c5ng(summer, vt):
    s = pd.read_csv(DHH, index_col=0, parse_dates=True).iloc[:, 0]
    s = pd.to_numeric(s, errors="coerce")
    s = s[s > 0].dropna().sort_index()
    lr = np.log(s).diff()
    idx = lr.index
    pos = pd.Series(0.0, index=idx)
    pos[idx.dayofweek == 2] = -1.0
    pos[idx.dayofweek == 3] = -1.0
    pos[idx.dayofweek == 4] = 1.0
    if summer:
        pos[~idx.month.isin(MONTHS)] = 0.0
    thr = lr.rolling(90).std().shift(1) * 2.5
    pos = pos.mask(lr.abs() > thr, 0.0)
    gr = pos * lr.shift(-1)
    turn = pos.diff().abs()
    turn.iloc[0] = abs(pos.iloc[0])
    net = (gr - turn * COST_SLEEVE).dropna()
    scaled, _ = vol_target(net, vt_ann=vt)
    return scaled.dropna()''',
 '''sys.path.insert(0, ROOT + "/campaign/agents/A3_xs_quality")
from r7_idea5_breadth import panel, RET_PAN
from r6lib import wback_rb
from r7lib import wed_rbd
from campaign.agents.B2_highfreq.gates import vol_target

def build_tsmom(maw):
    R5 = RET_PAN.drop(columns=["CASH"])
    s = np.sign(panel - panel.rolling(maw, min_periods=maw // 2).mean()).fillna(0) * 0.2
    net, _ = wback_rb(s, R5, wed_rbd(panel.index))
    rfull, _ = vol_target(net.dropna(), vt_ann=VT_FROZEN)
    return rfull.dropna()'''))
SUBS.append((
 '''sC = build_c5ng(False, ANCHOR_VT)
sS = build_c5ng(True, ANCHOR_VT)
okC, devC, niC, ncC = recon(sC, CNG_CSV)
okS, devS, niS, ncS = recon(sS, SUM_CSV)
log("A1a regen-vt010-vs-committed C5ng ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okC, devC, niC, ncC))
log("A1b regen-vt010-vs-committed C5ngsum ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okS, devS, niS, ncS))
assert okC and okS, "A1 failed - fail closed"''',
 '''sT = build_tsmom(ANCHOR_MAW)
okT, devT, niT, ncT = recon(sT, TSM_CSV)
log("A1 regen-maw189-vt015-vs-committed QAxasts ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okT, devT, niT, ncT))
assert okT, "A1 failed - fail closed"'''))
SUBS.append((
 '''for vt in ARMS:
    s1 = build_c5ng(False, vt)
    s2 = build_c5ng(True, vt)
    streams[vt] = (s1, s2)
    dfa = df12.copy()
    dfa["C5ng"] = s1.reindex(df12.index)
    dfa["C5ngsum"] = s2.reindex(df12.index)
    fit, nrows, kcov = fit_relw(dfa[dfa.index < B.IS_END], names12)''',
 '''for maw in ARMS:
    s1 = build_tsmom(maw)
    streams[maw] = s1
    assert s1.index.equals(streams[ANCHOR_MAW].index), "calendar moved with MAW - coverage law violated"
    dfa = df12.copy()
    dfa["QAxasts"] = s1.reindex(df12.index)
    assert int(dfa["QAxasts"].notna().sum()) == int(df12["QAxasts"].notna().sum()), "frame coverage changed - fail closed"
    fit, nrows, kcov = fit_relw(dfa[dfa.index < B.IS_END], names12)'''))
SUBS.append((
 '''    results[vt] = rec
    log("ARM VT=%.2f: rows=%d k=%d projid=%.3e IS-SR=%.6f IS-MDD=%.4f pct negyrs=%d Wmax_sf=%.4fx grossmax=%.9f" % (vt, nrows, kcov, rec["proj_id"], rec["is_sr"], rec["is_mdd"] * 100, rec["ny"], rec["wmax_sf"], rec["gmax"]))
    assert nrows == 1809 and kcov == K_COVERED, "arm window/coverage drift - fail closed"
    s1.to_frame("ret").to_csv(OUT + "/arm_vt%s_stream_cng.csv" % str(vt).replace(".", ""))
    s2.to_frame("ret").to_csv(OUT + "/arm_vt%s_stream_sum.csv" % str(vt).replace(".", ""))
    rec["relw"].to_frame("relw").to_csv(OUT + "/arm_vt%s_weights.csv" % str(vt).replace(".", ""))''',
 '''    results[maw] = rec
    log("ARM MAW=%d: rows=%d k=%d projid=%.3e IS-SR=%.6f IS-MDD=%.4f pct negyrs=%d Wmax_sf=%.4fx grossmax=%.9f" % (maw, nrows, kcov, rec["proj_id"], rec["is_sr"], rec["is_mdd"] * 100, rec["ny"], rec["wmax_sf"], rec["gmax"]))
    assert nrows == 1809 and kcov == K_COVERED, "arm window/coverage drift - fail closed"
    s1.to_frame("ret").to_csv(OUT + "/arm_maw%d_stream_tsm.csv" % maw)
    rec["relw"].to_frame("relw").to_csv(OUT + "/arm_maw%d_weights.csv" % maw)'''))
SUBS.append((
 '''ra = results[ANCHOR_VT]''',
 '''ra = results[ANCHOR_MAW]'''))
SUBS.append((
 '''adm = [vt for vt in ARMS if vt != ANCHOR_VT
       and results[vt]["is_sr"] > BAR + 1e-4
       and results[vt]["is_mdd"] >= -0.06
       and results[vt]["ny"] == 0
       and results[vt]["wmax_sf"] <= 2.0 + 1e-9]''',
 '''adm = [maw for maw in ARMS if maw != ANCHOR_MAW
       and results[maw]["is_sr"] > BAR + 1e-4
       and results[maw]["is_mdd"] >= -0.06
       and results[maw]["ny"] == 0
       and results[maw]["wmax_sf"] <= 2.0 + 1e-9]'''))
SUBS.append((
 '''    best = max(adm, key=lambda vt: results[vt]["is_sr"])''',
 '''    best = max(adm, key=lambda maw: results[maw]["is_sr"])'''))
SUBS.append((
 '''    log("REVEAL arm VT=%.2f (IS-argmax of admitted), gear 1.0, n=%d (%s..%s)" % (best, len(net), str(net.index[0].date()), str(net.index[-1].date())))''',
 '''    log("REVEAL arm MAW=%d (IS-argmax of admitted), gear 1.0, n=%d (%s..%s)" % (best, len(net), str(net.index[0].date()), str(net.index[-1].date())))'''))
SUBS.append((
 '''    pd.DataFrame(dict(ret=net.values), index=net.index).to_csv(OUT + "/candidate_vt%s_daily.csv" % str(best).replace(".", ""))''',
 '''    pd.DataFrame(dict(ret=net.values), index=net.index).to_csv(OUT + "/candidate_maw%d_daily.csv" % best)'''))
SUBS.append((
 '''with open(OUT + "/driver_iter51.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("LOG WRITTEN: " + OUT + "/driver_iter51.log")''',
 '''with open(OUT + "/driver_iter52.log", "w") as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print("LOG WRITTEN: " + OUT + "/driver_iter52.log")'''))

src = open(SRC).read()
for i, (o, n) in enumerate(SUBS):
    c = src.count(o)
    assert c == 1, "sub %d matched %d times (want exactly 1)" % (i + 1, c)
    src = src.replace(o, n)
for tok in ("ANCHOR_VT", "build_c5ng", "C5NG", "CNG_CSV", "SUM_CSV", "DHH", "COST_SLEEVE", "MONTHS",
            "ARM VT", "REVEAL arm VT", "candidate_vt", "arm_vt", "ITER51", "driver_iter51", "lambda vt", "for vt in"):
    assert tok not in src, "token survived: " + tok
open(DST, "w").write(src)
print("driver written:", DST, len(src), "bytes,", len(SUBS), "substitutions")
py_compile.compile(DST, doraise=True)
print("py_compile OK")
print("driver sha16:", hashlib.sha256(open(DST, "rb").read()).hexdigest()[:16])
