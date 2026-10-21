# make_driver_iter53.py - derive driver_iter53.py from driver_iter52.py by
# asserted-exactly-once substitutions (the make_driver_iter37.py law). py_compile gate.
# NOTE: no triple-quoted literals in this file (heredoc nesting trap); blocks are
# built with chr(10).join of single-quoted lines. Written in 3 append chunks.
import py_compile, hashlib

SRC = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/ITER52_TSMOM_MAW_READJ/driver_iter52.py"
DST = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/ITER53_DUR_READJ/driver_iter53.py"

SUBS = []
def sub(olds, news):
    SUBS.append((chr(10).join(olds), chr(10).join(news)))

sub([
    'OUT = ROOT + "/campaign/agents/chief/coord/ITER52_TSMOM_MAW_READJ"'],
    ['OUT = ROOT + "/campaign/agents/chief/coord/ITER53_DUR_READJ"'])
sub([
    'PRECOMMIT_SHA = "0e4c271945a4be28"'],
    ['PRECOMMIT_SHA = "710a1e7de776dbbd"'])
sub([
    'log(9 * chr(45) + " ITER52 TSMOM-MAW STALENESS RE-ADJUDICATION driver (2026-09-20 session 32). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " sealed BEFORE this run.")'],
    ['log(9 * chr(45) + " ITER53 A6R7-DUR STALENESS RE-ADJUDICATION driver (2026-09-20 session 33). FINDINGS_PRECOMMIT.md sha16 " + PRECOMMIT_SHA + " sealed BEFORE this run.")'])
sub([
    'ARMS = (189, 126, 157, 220, 252)',
    'ANCHOR_MAW = 189',
    'CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"',
    'WGT = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"',
    'TSM_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv"',
    'VT_FROZEN = 0.15'],
    ['ARMS = (1.90, 1.40, 1.65, 2.15, 2.40)',
    'ANCHOR_DUR = 1.90',
    'CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"',
    'WGT = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"',
    'A6R7_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv"',
    'DGS2 = ROOT + "/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv"',
    'K, CAD, VT, CAP = 378, 42, 0.12, 5.0'])

sub([
    'sys.path.insert(0, ROOT + "/campaign/harness")',
    'import data as DH',
    'def _panel_d17(extended=False):',
    '    d = DH.EXT if extended else DH.PANEL',
    '    out = dict()',
    '    for f in os.listdir(d):',
    '        if f.endswith(".csv") and f != "manifest.csv":',
    '            out[f[:-4]] = pd.read_csv(os.path.join(d, f), parse_dates=["date"], index_col="date")',
    '    return out',
    'DH.panel = _panel_d17',
    'import campaign.harness.data as DHF',
    'def _panel_d17_full(extended=False):',
    '    d = DHF.EXT if extended else DHF.PANEL',
    '    out = dict()',
    '    for f in os.listdir(d):',
    '        if f.endswith(".csv") and f != "manifest.csv":',
    '            out[f[:-4]] = pd.read_csv(os.path.join(d, f), parse_dates=["date"], index_col="date")',
    '    return out',
    'DHF.panel = _panel_d17_full',
    'log("D17 Amendment-1 DUAL pre-patch applied (data + campaign.harness.data) BEFORE the r7/r6lib chain - LOAD-BEARING here: manifest.csv live in twelve_big (mtime Sep 8 14:40), probe run-1 died fail-closed on the single-identity form")',
    '',
    'sys.path.insert(0, ROOT + "/campaign/agents/A3_xs_quality")',
    'from r7_idea5_breadth import panel, RET_PAN',
    'from r6lib import wback_rb',
    'from r7lib import wed_rbd',
    'from campaign.agents.B2_highfreq.gates import vol_target',
    '',
    'def build_tsmom(maw):',
    '    R5 = RET_PAN.drop(columns=["CASH"])',
    '    s = np.sign(panel - panel.rolling(maw, min_periods=maw // 2).mean()).fillna(0) * 0.2',
    '    net, _ = wback_rb(s, R5, wed_rbd(panel.index))',
    '    rfull, _ = vol_target(net.dropna(), vt_ann=VT_FROZEN)',
    '    return rfull.dropna()'],
    ['log("D17 SCOPE NOTE: the ITER53 chain is r6lib-FREE - legacy_a6r7 needs only pandas + DGS2 and rawew13v2_build loads the committed sleeve CSVs directly (no data.panel call); the PARENT-driver DUAL-identity D17 patch (iter52 form) is NOT-APPLICABLE here (the documented non-r6lib case) and is substituted OUT. The D17 runtime-patch law remains LOAD-BEARING for every r6lib-resolving chain and is untouched by this note.")',
    '',
    'def legacy_a6r7(dur):',
    '    y = pd.read_csv(DGS2, index_col=0, parse_dates=True)["value"].astype(float) / 100.0',
    '    y = y[~y.index.duplicated(keep="last")].sort_index()',
    '    tr = (-dur * y.diff() + y / 252.0).dropna()',
    '    sig = (tr.rolling(K).mean() > 0).astype(float)',
    '    W = sig.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)',
    '    gross_g = W.shift(1) * tr',
    '    turn = (W.shift(1) - W.shift(2)).abs().fillna(0.0)',
    '    net_g = (gross_g - turn * 6.0 / 1e4).dropna()',
    '    lev = (VT / np.sqrt(252) / net_g.expanding(60).std().shift(1)).clip(0, CAP).fillna(0.0)',
    '    return (net_g * lev).dropna()'])
sub([
    'sT = build_tsmom(ANCHOR_MAW)',
    'okT, devT, niT, ncT = recon(sT, TSM_CSV)',
    'log("A1 regen-maw189-vt015-vs-committed QAxasts ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okT, devT, niT, ncT))',
    'assert okT, "A1 failed - fail closed"'],
    ['sT = legacy_a6r7(ANCHOR_DUR)',
    'okT, devT, niT, ncT = recon(sT, A6R7_CSV)',
    'log("A1 regen-dur1.90-vs-committed a6r7 ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okT, devT, niT, ncT))',
    'assert okT, "A1 failed - fail closed"'])

sub([
    'for maw in ARMS:',
    '    s1 = build_tsmom(maw)',
    '    streams[maw] = s1',
    '    assert s1.index.equals(streams[ANCHOR_MAW].index), "calendar moved with MAW - coverage law violated"',
    '    dfa = df12.copy()',
    '    dfa["QAxasts"] = s1.reindex(df12.index)',
    '    assert int(dfa["QAxasts"].notna().sum()) == int(df12["QAxasts"].notna().sum()), "frame coverage changed - fail closed"',
    '    fit, nrows, kcov = fit_relw(dfa[dfa.index < B.IS_END], names12)'],
    ['for dur in ARMS:',
    '    s1 = legacy_a6r7(dur)',
    '    streams[dur] = s1',
    '    assert s1.index.equals(streams[ANCHOR_DUR].index), "calendar moved with DUR - coverage law violated"',
    '    dfa = df12.copy()',
    '    dfa["a6r7"] = s1.reindex(df12.index)',
    '    assert int(dfa["a6r7"].notna().sum()) == int(df12["a6r7"].notna().sum()), "frame coverage changed - fail closed"',
    '    fit, nrows, kcov = fit_relw(dfa[dfa.index < B.IS_END], names12)'])
sub([
    '    results[maw] = rec',
    '    log("ARM MAW=%d: rows=%d k=%d projid=%.3e IS-SR=%.6f IS-MDD=%.4f pct negyrs=%d Wmax_sf=%.4fx grossmax=%.9f" % (maw, nrows, kcov, rec["proj_id"], rec["is_sr"], rec["is_mdd"] * 100, rec["ny"], rec["wmax_sf"], rec["gmax"]))',
    '    assert nrows == 1809 and kcov == K_COVERED, "arm window/coverage drift - fail closed"',
    '    s1.to_frame("ret").to_csv(OUT + "/arm_maw%d_stream_tsm.csv" % maw)',
    '    rec["relw"].to_frame("relw").to_csv(OUT + "/arm_maw%d_weights.csv" % maw)'],
    ['    results[dur] = rec',
    '    log("ARM DUR=%.2f: rows=%d k=%d projid=%.3e IS-SR=%.6f IS-MDD=%.4f pct negyrs=%d Wmax_sf=%.4fx grossmax=%.9f" % (dur, nrows, kcov, rec["proj_id"], rec["is_sr"], rec["is_mdd"] * 100, rec["ny"], rec["wmax_sf"], rec["gmax"]))',
    '    assert nrows == 1809 and kcov == K_COVERED, "arm window/coverage drift - fail closed"',
    '    s1.to_frame("ret").to_csv(OUT + "/arm_dur" + ("%.2f" % dur) + "_stream_a6r7.csv")',
    '    rec["relw"].to_frame("relw").to_csv(OUT + "/arm_dur" + ("%.2f" % dur) + "_weights.csv")'])
sub([
    'ra = results[ANCHOR_MAW]'],
    ['ra = results[ANCHOR_DUR]'])
sub([
    'adm = [maw for maw in ARMS if maw != ANCHOR_MAW',
    '       and results[maw]["is_sr"] > BAR + 1e-4',
    '       and results[maw]["is_mdd"] >= -0.06',
    '       and results[maw]["ny"] == 0',
    '       and results[maw]["wmax_sf"] <= 2.0 + 1e-9]'],
    ['adm = [dur for dur in ARMS if dur != ANCHOR_DUR',
    '       and results[dur]["is_sr"] > BAR + 1e-4',
    '       and results[dur]["is_mdd"] >= -0.06',
    '       and results[dur]["ny"] == 0',
    '       and results[dur]["wmax_sf"] <= 2.0 + 1e-9]'])

sub([
    '    best = max(adm, key=lambda maw: results[maw]["is_sr"])'],
    ['    best = max(adm, key=lambda dur: results[dur]["is_sr"])'])
sub([
    '    log("REVEAL arm MAW=%d (IS-argmax of admitted), gear 1.0, n=%d (%s..%s)" % (best, len(net), str(net.index[0].date()), str(net.index[-1].date())))'],
    ['    log("REVEAL arm DUR=%.2f (IS-argmax of admitted), gear 1.0, n=%d (%s..%s)" % (best, len(net), str(net.index[0].date()), str(net.index[-1].date())))'])
sub([
    '    pd.DataFrame(dict(ret=net.values), index=net.index).to_csv(OUT + "/candidate_maw%d_daily.csv" % best)'],
    ['    pd.DataFrame(dict(ret=net.values), index=net.index).to_csv(OUT + "/candidate_dur" + ("%.2f" % best) + "_daily.csv")'])
sub([
    'with open(OUT + "/driver_iter52.log", "w") as fh:',
    '    fh.write(chr(10).join(LOG) + chr(10))',
    'print("LOG WRITTEN: " + OUT + "/driver_iter52.log")'],
    ['with open(OUT + "/driver_iter53.log", "w") as fh:',
    '    fh.write(chr(10).join(LOG) + chr(10))',
    'print("LOG WRITTEN: " + OUT + "/driver_iter53.log")'])

src = open(SRC).read()
for i, (o, n) in enumerate(SUBS):
    c = src.count(o)
    assert c == 1, "sub %d matched %d times (want exactly 1)" % (i + 1, c)
    src = src.replace(o, n)
for tok in ("ANCHOR_MAW", "build_tsmom", "TSM_CSV", "MAW", "maw", "VT_FROZEN", "vol_target",
            "QAxasts", "vt015", "ITER52", "driver_iter52", "RET_PAN", "wback_rb", "wed_rbd",
            "r7lib", "_panel_d17", "import data as DH", "126", "157", "220", "0.15"):
    assert tok not in src, "token survived: " + tok
open(DST, "w").write(src)
print("driver written:", DST, len(src), "bytes,", len(SUBS), "substitutions")
py_compile.compile(DST, doraise=True)
print("py_compile OK")
print("driver sha16:", hashlib.sha256(open(DST, "rb").read()).hexdigest()[:16])

