"""make_driver_iter55.py (2026-09-20 session 35). Rebuilds driver_iter55.py from
a byte-copy of driver_iter54.py (sha16 c5c7855346fbd31c) via 16 asserted-exactly-once
substitutions (brwt generator spliced verbatim from driver_iter34.py source); asserts
the rebuild is byte-equal to the landed driver_iter55.py. Authored in 3 append chunks
(the ~12KB single-heredoc parser cap)."""
import hashlib
C = "/Users/daxu/software/world-trader/campaign/agents/chief/coord"
D = C + "/ITER55_BRWT_ZB_READJ"
src54 = open(C + "/ITER54_C5NG_K_READJ/driver_iter54.py").read()
R6O = '''def build_c5ng(summer, k):
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
    thr = lr.rolling(90).std().shift(1) * k
    pos = pos.mask(lr.abs() > thr, 0.0)
    gr = pos * lr.shift(-1)
    turn = pos.diff().abs()
    turn.iloc[0] = abs(pos.iloc[0])
    net = (gr - turn * COST_SLEEVE).dropna()
    scaled, _ = vol_target(net, vt_ann=VT_FROZEN)
    return scaled.dropna()'''

R6N = '''def dload(pstr):
    df = pd.read_csv(pstr, index_col=0, parse_dates=True)
    v = df.iloc[:, 0]
    return pd.to_numeric(v, errors="coerce").dropna()

def fred(name):
    s = dload(FRED + "/" + name + ".csv")
    return s[~s.index.duplicated(keep="last")].sort_index()

def brwt_load():
    BR = fred("brent")
    WT = fred("wti")
    E_BR = dload(EIA + "/brent_spot_daily.csv")
    E_WT = dload(EIA + "/wti_spot_daily.csv")
    BR = pd.concat([BR, E_BR[E_BR.index > BR.index[-1]]])
    WT = pd.concat([WT, E_WT[E_WT.index > WT.index[-1]]])
    return BR, WT

def brwt_build(lb, zb, min_start):
    BR, WT = brwt_load()
    sp = (np.log(BR) - np.log(WT)).dropna()
    sp = sp[sp.index >= min_start]
    m = sp.rolling(lb, min_periods=lb).mean()
    sd = sp.rolling(lb, min_periods=lb).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -zb] = 1.0
    pos[z > zb] = -1.0
    gross = pos * sp.diff().shift(-1)
    net = gross - pos.diff().abs() * 6.4 / 1e4
    scaled, _ = vol_target(net)
    return scaled'''

R7O = '''sC = build_c5ng(False, ANCHOR_K)
sS = build_c5ng(True, ANCHOR_K)
okC, devC, niC, ncC = recon(sC, CNG_CSV)
okS, devS, niS, ncS = recon(sS, SUM_CSV)
log("A1a regen-k250-vs-committed C5ng ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okC, devC, niC, ncC))
log("A1b regen-k250-vs-committed C5ngsum ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (okS, devS, niS, ncS))
assert okC and okS, "A1 failed - fail closed"'''

R7N = '''okA = True
for lb, nm, ms in ARMS3:
    g = brwt_build(lb, ANCHOR_ZB, ms)
    ok, dev, ni, nc = recon(g, ROOT + "/" + B.PATHS[nm])
    okA = okA and ok
    log("A1 regen-zb100-vs-committed " + nm + " ok=%s maxdev=%.3e inner=%d committed_nonnan=%d" % (ok, dev, ni, nc))
assert okA, "A1 failed - fail closed"'''

R8O = '''streams = dict()
results = dict()
for k in ARMS:
    s1 = build_c5ng(False, k)
    s2 = build_c5ng(True, k)
    streams[k] = (s1, s2)
    assert s1.index.equals(streams[ANCHOR_K][0].index), "calendar moved with K - coverage law violated"
    assert s2.index.equals(streams[ANCHOR_K][1].index), "sum calendar moved with K - coverage law violated"
    dfa = df12.copy()
    dfa["C5ng"] = s1.reindex(df12.index)
    dfa["C5ngsum"] = s2.reindex(df12.index)
    assert int(dfa["C5ng"].notna().sum()) == int(df12["C5ng"].notna().sum()), "frame coverage changed - fail closed"
    assert int(dfa["C5ngsum"].notna().sum()) == int(df12["C5ngsum"].notna().sum()), "sum frame coverage changed - fail closed"
    fit, nrows, kcov = fit_relw(dfa[dfa.index < B.IS_END], names12)
    relw_raw = apply_cap(fit)
    relw = project_wmax(relw_raw, k=kcov, block=B.BRWT_BLOCK)
    netA, WgA, toA = build_book(dfa, relw, gear=1.0)
    i_net = netA[netA.index < B.IS_END]
    rec = dict(nrows=nrows, kcov=kcov, relw=relw, relw_raw=relw_raw, net=netA, Wg=WgA, to=toA,
               is_sr=sr(i_net), is_mdd=mdd(i_net), ny=len(neg_years(i_net)),
               wmax_sf=float(relw.max()) * kcov, gmax=float(WgA.abs().sum(axis=1).max()),
               proj_id=float((relw - relw_raw).abs().max()))
    results[k] = rec
    log("ARM K=%.2f: rows=%d k=%d projid=%.3e IS-SR=%.6f IS-MDD=%.4f pct negyrs=%d Wmax_sf=%.4fx grossmax=%.9f" % (k, nrows, kcov, rec["proj_id"], rec["is_sr"], rec["is_mdd"] * 100, rec["ny"], rec["wmax_sf"], rec["gmax"]))
    assert nrows == 1809 and kcov == K_COVERED, "arm window/coverage drift - fail closed"
    s1.to_frame("ret").to_csv(OUT + "/arm_k" + ("%.2f" % k) + "_stream_cng.csv")
    s2.to_frame("ret").to_csv(OUT + "/arm_k" + ("%.2f" % k) + "_stream_sum.csv")
    rec["relw"].to_frame("relw").to_csv(OUT + "/arm_k" + ("%.2f" % k) + "_weights.csv")'''

R8N = '''streams = dict()
results = dict()
for z in ARMS:
    s3 = dict()
    for lb, nm, ms in ARMS3:
        s3[nm] = brwt_build(lb, z, ms)
    streams[z] = s3
    for lb, nm, ms in ARMS3:
        assert s3[nm].index.equals(streams[ANCHOR_ZB][nm].index), "calendar moved with ZB - coverage law violated"
    dfa = df12.copy()
    for lb, nm, ms in ARMS3:
        dfa[nm] = s3[nm].reindex(df12.index)
        assert int(dfa[nm].notna().sum()) == int(df12[nm].notna().sum()), nm + " frame coverage changed - fail closed"
    fit, nrows, kcov = fit_relw(dfa[dfa.index < B.IS_END], names12)
    relw_raw = apply_cap(fit)
    relw = project_wmax(relw_raw, k=kcov, block=B.BRWT_BLOCK)
    netA, WgA, toA = build_book(dfa, relw, gear=1.0)
    i_net = netA[netA.index < B.IS_END]
    rec = dict(nrows=nrows, kcov=kcov, relw=relw, relw_raw=relw_raw, net=netA, Wg=WgA, to=toA,
               is_sr=sr(i_net), is_mdd=mdd(i_net), ny=len(neg_years(i_net)),
               wmax_sf=float(relw.max()) * kcov, gmax=float(WgA.abs().sum(axis=1).max()),
               proj_id=float((relw - relw_raw).abs().max()))
    results[z] = rec
    log("ARM ZB=%.2f: rows=%d k=%d projid=%.3e IS-SR=%.6f IS-MDD=%.4f pct negyrs=%d Wmax_sf=%.4fx grossmax=%.9f" % (z, nrows, kcov, rec["proj_id"], rec["is_sr"], rec["is_mdd"] * 100, rec["ny"], rec["wmax_sf"], rec["gmax"]))
    assert nrows == 1809 and kcov == K_COVERED, "arm window/coverage drift - fail closed"
    for lb, nm, ms in ARMS3:
        s3[nm].to_frame("ret").to_csv(OUT + "/arm_zb" + ("%.2f" % z) + "_stream_" + nm + ".csv")
    rec["relw"].to_frame("relw").to_csv(OUT + "/arm_zb" + ("%.2f" % z) + "_weights.csv")'''

R9O = '''adm = [k for k in ARMS if k != ANCHOR_K
       and results[k]["is_sr"] > BAR + 1e-4
       and results[k]["is_mdd"] >= -0.06
       and results[k]["ny"] == 0
       and results[k]["wmax_sf"] <= 2.0 + 1e-9]
log("")
log("IS admission: " + str(adm) + " (bar %.6f, anchor arm ineligible by construction)" % BAR)'''

R9N = '''adm = [z for z in ARMS if z != ANCHOR_ZB
       and results[z]["is_sr"] > BAR + 1e-4
       and results[z]["is_mdd"] >= -0.06
       and results[z]["ny"] == 0
       and results[z]["wmax_sf"] <= 2.0 + 1e-9
       and results[z]["proj_id"] == 0.0]
log("")
log("IS admission: " + str(adm) + " (bar %.6f, anchor ineligible, projid==0 addendum per precommit)" % BAR)'''

PAIRS = [
 ('OUT = ROOT + "/campaign/agents/chief/coord/ITER54_C5NG_K_READJ"',
  'OUT = ROOT + "/campaign/agents/chief/coord/ITER55_BRWT_ZB_READJ"'),
 ('PRECOMMIT_SHA = "96f3078f6c940b06"', 'PRECOMMIT_SHA = "3d9e4163bff420b1"'),
 ('ARMS = (2.5, 1.5, 2.0, 3.0, 3.5)', 'ARMS = (1.0, 0.25, 0.5, 0.75, 1.25, 1.5, 1.75, 2.0)'),
 ('ANCHOR_K = 2.5\nVT_FROZEN = 0.10', 'ANCHOR_ZB = 1.0'),
 ('CNG_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv"\nSUM_CSV = ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv"\nDHH = ROOT + "/tools/quant/data/newdata/DHHNGSP.csv"\nCOST_SLEEVE = 6e-4\nMONTHS = list(range(4, 11))',
  'FRED = ROOT + "/tools/quant/hedge_fund_strats/data_fred"\nEIA = ROOT + "/tools/quant/data/eia_weekly"\nARMS3 = [(10, "brwt10", "2000-01-01"), (7, "brwt7", "2008-01-01"), (5, "brwt5", "2008-01-01")]'),
 (R6O, R6N), (R7O, R7N), (R8O, R8N), (R9O, R9N),
 ('ra = results[ANCHOR_K]', 'ra = results[ANCHOR_ZB]'),
 ('best = max(adm, key=lambda k: results[k]["is_sr"])', 'best = max(adm, key=lambda z: results[z]["is_sr"])'),
 ('log("REVEAL arm K=%.2f (IS-argmax of admitted), gear 1.0, n=%d (%s..%s)"',
  'log("REVEAL arm zb=%.2f (IS-argmax of admitted), gear 1.0, n=%d (%s..%s)"'),
 ('to_csv(OUT + "/candidate_k" + ("%.2f" % best) + "_daily.csv")',
  'to_csv(OUT + "/candidate_zb" + ("%.2f" % best) + "_daily.csv")'),
 ('" ITER54 C5NG-K STALENESS RE-ADJUDICATION driver (2026-09-20 session 34). ',
  '" ITER55 BRWT-ZB STALENESS RE-ADJUDICATION driver (2026-09-20 session 35). '),
 ('with open(OUT + "/driver_iter54.log", "w") as fh:',
  'with open(OUT + "/driver_iter55.log", "w") as fh:'),
 ('print("LOG WRITTEN: " + OUT + "/driver_iter54.log")',
  'print("LOG WRITTEN: " + OUT + "/driver_iter55.log")'),
]
out = src54
for i, (old, new) in enumerate(PAIRS, 1):
    cnt = out.count(old)
    assert cnt == 1, "sub R%d count=%d" % (i, cnt)
    out = out.replace(old, new)
HYG = ["C5ng", "c5ng", "C5NG", "VT_FROZEN", "ANCHOR_K", "DHH", "COST_SLEEVE", "MONTHS",
       "arm_k", "candidate_k", "ITER54", "session 34", "results[k]", "build_c5ng",
       "K=%.2f", "driver_iter54.log"]
bad = [t for t in HYG if t in out]
assert not bad, "inherited labels survived: %r" % bad
landed = open(D + "/driver_iter55.py").read()
assert out == landed, "rebuild differs from landed driver"
print("make_driver_iter55: %d/%d subs exactly-once, hygiene clean (incl. log filename), rebuild == landed bytes, sha16 %s" % (len(PAIRS), len(PAIRS), hashlib.sha256(out.encode()).hexdigest()[:16]))
