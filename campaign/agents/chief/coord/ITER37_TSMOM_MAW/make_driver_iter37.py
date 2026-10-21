import py_compile, sys
SRC = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/ITER36_DIESCRACK_Z/driver_iter36.py"
DST = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/ITER37_TSMOM_MAW/driver_iter37.py"
src = open(SRC).read()
SUBS = []
def sub(old, new):
    SUBS.append((old, new))

sub('OUT = ROOT + "/campaign/agents/chief/coord/ITER36_DIESCRACK_Z"',
    'OUT = ROOT + "/campaign/agents/chief/coord/ITER37_TSMOM_MAW"')
sub('PRECOMMIT_SHA = "946c617d868816e8"', 'PRECOMMIT_SHA = "a8ea3922b5e64de3"')
sub("GRID = [1.5, 1.75, 2.0, 2.25, 2.5]", "GRID = [126, 157, 189, 220, 252]")
sub("ANCHOR_Z = 2.0", "ANCHOR_MAW = 189")
sub('DC_REL = "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv"',
    'QA_REL = "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv"')
sub("import rawew13v2_build as B", """import rawew13v2_build as B

sys.path.insert(0, ROOT + "/campaign/agents/A3_xs_quality")
import campaign.harness.data as _D

def _panel_skip_manifest(extended=False):
    # D17 mitigation (FINDINGS_PRECOMMIT.md): twelve_big/manifest.csv (untracked,
    # landed 2026-09-08) breaks panel(); skipping it restores the original 298-CSV
    # panel byte-faithfully (sleeve predates the manifest; A1 regen-vs-saved 1e-16).
    d = _D.EXT if extended else _D.PANEL
    out = {}
    for f in os.listdir(d):
        if f.endswith(".csv") and f != "manifest.csv":
            df = pd.read_csv(os.path.join(d, f), parse_dates=["date"], index_col="date")
            out[f[:-4]] = df
    return out

_D.panel = _panel_skip_manifest
from r7_idea5_breadth import panel, RET_PAN
from r6lib import wback_rb
from r7lib import wed_rbd
from campaign.agents.B2_highfreq.gates import vol_target""")
sub("""def diescrack_build(gate):
    dj = fred("DJFUELUSGULF", src=NEW)
    wt = fred("wti_full")
    E_WT = dload(EIA + "/wti_spot_daily.csv")
    wt = pd.concat([wt, E_WT[E_WT.index > wt.index[-1]]])
    sp = (np.log(dj * 42.0) - np.log(wt)).dropna()
    sp = sp[sp.index >= "2008-01-01"]
    m = sp.rolling(40, min_periods=40).mean()
    sd = sp.rolling(40, min_periods=40).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -gate] = 1.0
    pos[z > gate] = -1.0
    ret = sp.diff().shift(-1)
    gr = (pos * ret).dropna()
    tup = pos.diff().abs().reindex(gr.index).fillna(0.0)
    base = gr - tup * 6.4 / 1e4
    pi = pos.reindex(base.index).fillna(0.0)
    bmask = ((pi != 0) | (pi.shift(1).fillna(0) != 0)).astype(float)
    sc = (0.08 / (base.expanding(60).std() * np.sqrt(252))).clip(upper=3.0)
    return ((base * sc).fillna(0.0) - bmask * 0.005 / 252).dropna()""",
"""def tsmom_build(maw):
    # Re-typed verbatim from e1_idea5_xasts_detrunc.py (importing it would fire its
    # module-level save_sleeve onto live sleeves). A1: regen-vs-saved 9.996344e-17.
    R5 = RET_PAN.drop(columns=["CASH"])
    s = np.sign(panel - panel.rolling(maw, min_periods=maw // 2).mean()).fillna(0) * 0.2
    net, _ = wback_rb(s, R5, wed_rbd(panel.index))
    rfull, _ = vol_target(net.dropna(), 0.10)
    return rfull.dropna()""")
sub('a = extract(ROOT + "/campaign/agents/chief/coord/ITER34_BRWT_ZB/driver_iter34.py")',
    'a = extract(ROOT + "/campaign/agents/chief/coord/ITER36_DIESCRACK_Z/driver_iter36.py")')
sub('"frozen block diverged from driver_iter34: "', '"frozen block diverged from driver_iter36: "')
sub('log("FROZEN-BLOCK check vs driver_iter34.py: fit_relw/apply_cap/project_wmax/build_book text-identical")',
    'log("FROZEN-BLOCK check vs driver_iter36.py: fit_relw/apply_cap/project_wmax/build_book text-identical")')
sub('ITER36 diescrack gate-Z driver (2026-09-19 session 17). FINDINGS_PRECOMMIT.md sha16 ',
    'ITER37 tsmom-maw driver (2026-09-19 session 18). FINDINGS_PRECOMMIT.md sha16 ')
sub('saved = dload(ROOT + "/" + DC_REL)', 'saved = dload(ROOT + "/" + QA_REL)')
sub("gen0 = diescrack_build(ANCHOR_Z)", "gen0 = tsmom_build(ANCHOR_MAW)")
sub('log("ANCHOR A1 regen Z=2.0 vs saved: maxdev=%.6e (inner n=%d)" % (a1dev, len(j0)))',
    'log("ANCHOR A1 regen MAW=189 vs saved: maxdev=%.6e (inner n=%d)" % (a1dev, len(j0)))')
sub('dc_share = float((relw12 / relw12.sum())["diescrack"])',
    'dc_share = float((relw12 / relw12.sum())["QAxasts"])')
sub("diescrack share=%.4f pct", "QAxasts share=%.4f pct")
sub('log("CELL SWEEP: gate-Z grid at frozen L=40, every other slot frozen per precommit; one sleeve (diescrack), one scalar")',
    'log("CELL SWEEP: MAW grid on the E1 de-truncated 5-leg cross-asset TSMOM (panel/RET_PAN/vt10 frozen), every other slot frozen per precommit; one sleeve (QAxasts), one scalar")')
sub('log("Z      regen-dev   is_sr     IS-ann pct  IS-MDD pct  negy  Wmax_sf   adm")',
    'log("MAW    regen-dev   is_sr     IS-ann pct  IS-MDD pct  negy  Wmax_sf   adm")')
sub("for Z in GRID:", "for MAW in GRID:")
sub("    s = diescrack_build(Z)", "    s = tsmom_build(MAW)")
sub('    label = "%.2f" % Z', '    label = "%d" % MAW')
sub("    if Z == ANCHOR_Z:", "    if MAW == ANCHOR_MAW:")
sub('log("ANCHOR CELL Z=2.00: weights dev', 'log("ANCHOR CELL MAW=189: weights dev')
sub('"/arm_Z" + label + "_weights.csv"', '"/arm_MAW" + label + "_weights.csv"')
sub("rows.append(dict(label=label, Z=Z, isr=i_sr,", "rows.append(dict(label=label, MAW=MAW, isr=i_sr,")
sub('dfc["diescrack"] = s.reindex(dfc.index)', 'dfc["QAxasts"] = s.reindex(dfc.index)')
sub('int(dfc["diescrack"].notna().sum()) == int(df12["diescrack"].notna().sum())',
    'int(dfc["QAxasts"].notna().sum()) == int(df12["QAxasts"].notna().sum())')
sub('win = sorted(adm_rows, key=lambda r: (-r["isr"], abs(r["Z"] - ANCHOR_Z), r["Z"]))[0]',
    'win = sorted(adm_rows, key=lambda r: (-r["isr"], abs(r["MAW"] - ANCHOR_MAW), r["MAW"]))[0]')
sub('log("GLOBAL ARGMAX (IS-only): Z=%s IS-SR=%.6f Wmax_sf=%.4fx block=%.6f"',
    'log("GLOBAL ARGMAX (IS-only): MAW=%s IS-SR=%.6f Wmax_sf=%.4fx block=%.6f"')
sub('log("REVEAL book: 12-pool refit at Z=%s, gear 1.0, n=%d (%s..%s)"',
    'log("REVEAL book: 12-pool refit at MAW=%s, gear 1.0, n=%d (%s..%s)"')
sub('"/candidate_Z" + win["label"] + "_daily.csv"', '"/candidate_MAW" + win["label"] + "_daily.csv"')
sub('"/candidate_Z" + win["label"] + "_weights.csv"', '"/candidate_MAW" + win["label"] + "_weights.csv"')
sub('with open(OUT + "/driver_iter36.log", "w") as fh:', 'with open(OUT + "/driver_iter37.log", "w") as fh:')
sub('print("LOG WRITTEN: " + OUT + "/driver_iter36.log")', 'print("LOG WRITTEN: " + OUT + "/driver_iter37.log")')

for i, (old, new) in enumerate(SUBS):
    n = src.count(old)
    assert n == 1, "sub %d: expected 1 occurrence, found %d: %r" % (i, n, old[:70])
    src = src.replace(old, new)
open(DST, "w").write(src)
py_compile.compile(DST, doraise=True)
print("driver_iter37.py written:", len(src), "bytes;", len(SUBS), "substitutions all asserted-1; py_compile OK")
