# ITER31 driver (2026-09-19, session #13). FINDINGS_PRECOMMIT.md sha16 70c776c7f82a96c8
# sealed BEFORE this driver was invoked (driver asserts the hash; mutation aborts).
# Machinery copied verbatim: fit_relw target branch + apply_cap from
# coord/ITER29_FIT_TARGET/driver_iter29.py; project_wmax + gates G1-G8 + stop rule from
# coord/ITER26_CREDIT_CAPFIT/driver_2026-09-19.py. ONE declared repair step (pre-commit
# section 2): water-fill the A3/A4 estimator arms to the Wmax invariant at k_covered=11
# (#120 canonical convention), re-adjudicate, ONE global argmax, ONE reveal.
import os, sys, hashlib
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT = '/Users/daxu/software/world-trader'
sys.path.insert(0, ROOT + '/campaign/scripts')
import rawew13v2_build as B

OUT = ROOT + '/campaign/agents/chief/coord/ITER31_FITTARGET_CAPFIT'
OUT29 = ROOT + '/campaign/agents/chief/coord/ITER29_FIT_TARGET'
LOG = []
def log(s=''):
    LOG.append(str(s)); print(s)

W_MAX, SHRINK, BRWT_CAP = 2.0, 0.70, 0.30
BRWT_BLOCK = ('brwt10', 'brwt7', 'brwt5')
PRECOMMIT_SHA = '70c776c7f82a96c8'
K_COVERED = 11
BAR = 4.198632
FS_BAR = 3.751429

def sr(x): return float(x.mean() / x.std(ddof=1) * np.sqrt(252))
def mdd(x):
    nav = (1 + x).cumprod(); return float((nav / nav.cummax() - 1).min())
def ann_arith(x): return float(x.mean() * 252)
def ann_cagr(x): return float((1 + x).prod() ** (252 / len(x)) - 1)
def neg_years(x):
    yr = x.groupby(x.index.year).apply(lambda v: (1 + v).prod() - 1)
    return yr[yr < 0]
def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]

def fit_relw(df_isr, names, shrink=SHRINK, target='diag'):
    have = [n for n in names if df_isr[n].notna().sum() > 0]
    X = df_isr[have].dropna()
    mu = (X.mean() * 252).values
    Sig = X.cov().values * 252
    if target == 'diag':
        Sig = (1.0 - shrink) * Sig + shrink * np.diag(np.diag(Sig))
    elif target == 'constvar':
        Sig = (1.0 - shrink) * Sig + shrink * (float(np.diag(Sig).mean()) * np.eye(len(Sig)))
    else:
        raise RuntimeError('unknown covariance target - fail closed')
    k, sd = len(have), np.sqrt(np.diag(Sig))
    def neg_sharpe(w):
        v = float(np.sqrt(w @ Sig @ w))
        return -(float(w @ mu)) / v if v > 1e-14 else 0.0
    cons = [dict(type='eq', fun=lambda w: w.sum() - 1.0)]
    cap = W_MAX / k
    def solve(bounds):
        best = None
        for w0 in (np.full(k, 1.0 / k),
                   np.maximum(mu, 0.0) / max(float(np.maximum(mu, 0.0).sum()), 1e-12),
                   (1.0 / sd) / (1.0 / sd).sum()):
            r = minimize(neg_sharpe, w0, method='SLSQP', bounds=bounds, constraints=cons,
                         options=dict(maxiter=800, ftol=1e-12))
            if r.success and (best is None or r.fun < best.fun):
                best = r
        return best
    best = solve([(0.0, W_MAX)] * k)
    if best is not None and float(best.x.max()) > cap + 1e-9:
        best = solve([(0.0, cap)] * k)
    if best is None:
        raise RuntimeError('IS max-Sharpe fit failed to converge - fail closed')
    relw = pd.Series(0.0, index=names)
    relw[have] = best.x
    return relw, int(X.shape[0]), int(k)

def apply_cap(relw, cap=BRWT_CAP):
    share = relw / relw.sum(); out = share.copy()
    if cap is not None:
        blk = [n for n in BRWT_BLOCK if n in share.index]
        bs = float(share[blk].sum())
        if bs > cap:
            excess = bs - cap
            out[blk] = share[blk] * (cap / bs)
            nonblk = [n for n in share.index if n not in blk]
            nb = float(share[nonblk].sum())
            out[nonblk] = share[nonblk] + excess * share[nonblk] / nb
    if 'CFX4' in out.index: out['CFX4'] = 0.0
    return out

def project_wmax(relw, k, block=BRWT_BLOCK, tol=1e-12, iters=200):
    # Pre-commit section 2 REPAIR STEP, verbatim ITER26: deterministic parameter-free
    # water-filling into the invariant set share <= 2/k. Receivers: non-block, non-CFX4,
    # strictly below cap. Identity on any already-feasible vector (loop body never fires).
    cap = 2.0 / k
    out = relw.copy()
    s0 = float(out.sum())
    for _ in range(iters):
        over = out > cap + tol
        if not over.any():
            break
        if bool(out[list(block)].max() > cap + tol):
            raise RuntimeError('block name violates invariant - fail closed')
        excess = float((out[over] - cap).sum())
        out[over] = cap
        recv = [n for n in out.index
                if (n not in block) and (n != 'CFX4') and (float(out[n]) < cap - tol)]
        if not recv:
            raise RuntimeError('water-filling has no receivers - fail closed')
        w = out[recv].astype(float); s = float(w.sum())
        if s <= 1e-15:
            raise RuntimeError('water-filling receiver mass zero - fail closed')
        out[recv] = w + excess * w / s
    else:
        raise RuntimeError('water-filling did not converge - fail closed')
    assert abs(float(out.sum()) - s0) < 1e-12, 'sum not preserved'
    if 'CFX4' in out.index: assert float(out['CFX4']) == 0.0
    assert float(out[list(block)].sum()) <= BRWT_CAP + 1e-9, 'block mass grew'
    return out

def build_book(frame, relw, gear=1.0):
    nav = (1 + frame.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw)
    Wg = d2 * (gear / len(relw))
    port = (frame.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = pd.Series(port, index=frame.index) - to * B.BPS / 1e4 - max(gear - 1, 0) * B.RATE / 252
    return net, Wg, to

CHAMP = ROOT + '/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv'
WGT   = ROOT + '/campaign/results/RAWEW13v2_IS_SR_weights.csv'
log(''.join(['# ITER31 estimator-at-cap driver (2026-09-19 session #13). FINDINGS_PRECOMMIT.md sha16 ', PRECOMMIT_SHA, ' sealed BEFORE this run.']))
assert sha16(OUT + '/FINDINGS_PRECOMMIT.md') == PRECOMMIT_SHA, 'precommit mutated - fail closed'
champ_sha_pre, wgt_sha_pre = sha16(CHAMP), sha16(WGT)
log('# Champion sha16 pre-run: ' + champ_sha_pre + ' / weights ' + wgt_sha_pre + ' / precommit ' + PRECOMMIT_SHA)

names12 = list(B.NAMES)
df12 = pd.DataFrame(dict((n, B.load(B.PATHS[n]).dropna()) for n in names12))
df12 = df12[df12.index >= '2008-03-31']

# ---- ANCHORS (pre-commit section 2; fail-closed, before any candidate) ----
_fit12, nrows12, k12 = fit_relw(df12[df12.index < B.IS_END], names12)
relw12_raw = apply_cap(_fit12)
assert k12 == K_COVERED, 'k_covered drift - fail closed'
relw12 = project_wmax(relw12_raw, k=K_COVERED)
ident = float((relw12 - relw12_raw).abs().max())
committed = pd.read_csv(WGT, index_col=0).iloc[:, 0]
wdev = float((relw12 - committed.reindex(relw12.index)).abs().max())
net12, Wg12, _ = build_book(df12, relw12, gear=1.0)
champ = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([champ.rename('csv'), net12.rename('reb')], axis=1, join='inner')
bdev = float((j['csv'] - j['reb']).abs().max())
gmax = float(Wg12.abs().sum(axis=1).max())
isr_net12 = net12[net12.index < B.IS_END]
is_sr_inc = sr(isr_net12)
inc_wmax_sf = float(relw12.max()) * K_COVERED
log('ANCHOR projection-identity on incumbent: maxdev=' + repr(ident) + ' (need exactly 0)')
log('ANCHOR weights maxdev=%.3e (need <1e-12)' % wdev)
log('ANCHOR bytes   maxdev=%.3e (need <1e-12) n=%d' % (bdev, len(j)))
log('ANCHOR grossmax=%.9f  days>1.6: %d' % (gmax, int((Wg12.abs().sum(axis=1) > 1.6 + 1e-9).sum())))
log('ANCHOR incumbent Wmax_sf(x11)=%.4fx (feasible under corrected invariant)' % inc_wmax_sf)
log('ANCHOR incumbent IS-SR=%.6f (continuity 4.198632)' % is_sr_inc)
assert ident == 0.0, 'projection is NOT identity on the feasible incumbent - fail closed'
assert wdev < 1e-12 and bdev < 1e-12 and gmax <= 1.0 + 1e-9
assert abs(is_sr_inc - 4.198632) < 5e-6, 'IS-SR anchor drifted - fail closed'
log('ANCHOR fit rows=%d k_covered=%d' % (nrows12, k12))

# ---- frozen family (pre-commit section 1): the two bar-beating ITER29 arms, at-cap ----
from sklearn.covariance import ledoit_wolf as lw04

ARMS = [('A3', 'constvar', 0.70), ('A4', 'diag-lw04', None)]
log('')
log('arm  target       s_used   unproj-IS-SR  proj-IS-SR  IS-ann pct  IS-MDD pct  negy  Wmax_sf   adm')
rows = []
for arm, tgt, sfix in ARMS:
    isr = df12[df12.index < B.IS_END]
    if tgt == 'diag-lw04':
        have_a = [n for n in names12 if isr[n].notna().sum() > 0]
        Xlw = isr[have_a].dropna()
        s_used = float(lw04(Xlw.values)[1])
        relw_a, nrows_a, k_a = fit_relw(isr, names12, shrink=s_used, target='diag')
    else:
        s_used = sfix
        relw_a, nrows_a, k_a = fit_relw(isr, names12, shrink=sfix, target=tgt)
    assert nrows_a == nrows12 and k_a == K_COVERED, 'fit frame changed - fail closed'
    relw_a = apply_cap(relw_a)
    saved = pd.read_csv(OUT29 + '/arm_' + arm + '_weights.csv', index_col=0).iloc[:, 0]
    rdev = float((relw_a - saved.reindex(relw_a.index)).abs().max())
    assert rdev < 1e-9, 'machinery does not reproduce ITER29 arm - fail closed'
    isu = relw_a.copy()
    net_u, _, _ = build_book(df12, isu, gear=1.0)
    is_sr_u = sr(net_u[net_u.index < B.IS_END])
    relw_p = project_wmax(relw_a, k=K_COVERED)
    wmax_sf = float(relw_p.max()) * K_COVERED
    assert wmax_sf <= 2.0 + 1e-9, 'projection failed its own invariant'
    moved = float((relw_p - relw_a).abs().sum())
    net_p, Wg_p, _ = build_book(df12, relw_p, gear=1.0)
    i_net = net_p[net_p.index < B.IS_END]
    i_sr, i_mdd = sr(i_net), mdd(i_net)
    i_ann = ann_arith(i_net) * 100
    ny = len(neg_years(i_net))
    cfx = float(relw_p['CFX4'])
    adm = (wmax_sf <= 2.0 + 1e-9) and (i_mdd >= -0.06) and (ny == 0) and (i_sr > BAR + 1e-4)
    rows.append(dict(name=arm, tgt=tgt, s_used=s_used, rdev=rdev, moved=moved,
                     is_sr_u=is_sr_u, isr=i_sr, iann=i_ann, imdd=i_mdd, ny=ny,
                     wmax=wmax_sf, cfx=cfx, adm=adm, relw=relw_p, net=net_p))
    relw_p.to_frame('relw').to_csv(OUT + '/arm_' + arm + '_atcap_weights.csv')
    log('%-4s %-11s %7.4f   %8.4f    %8.4f   %8.3f    %8.2f    %d/9  %6.4fx  %s' % (arm, tgt, s_used, is_sr_u, i_sr, i_ann, i_mdd * 100, ny, wmax_sf, 'YES' if adm else 'no'))
    log('     REPRO vs ITER29 saved arm: maxdev=%.3e (need <1e-9); moved mass %.6f' % (rdev, moved))

adm_rows = [r for r in rows if r['adm']]
log('')
log('ADMITTED: %d / %d (jitter tolerance 1e-4 on the IS bar)' % (len(adm_rows), len(ARMS)))

verdict = 'NO-ADMISSION (IS level) -> honest negative, no reveal (per pre-commit stop rule)'
if not adm_rows:
    log('NO arm admitted -> HONEST NEGATIVE, no reveal (per pre-commit STOP RULE).')
else:
    win = sorted(adm_rows, key=lambda r: (-r['isr'], r['name']))[0]
    log('GLOBAL ARGMAX (IS-only): %s (%s, s=%.4f) IS-SR=%.6f Wmax_sf=%.4fx' % (win['name'], win['tgt'], win['s_used'], win['isr'], win['wmax']))
    fs = win['net']; relw13 = win['relw']
    f_sr, f_mdd = sr(fs), mdd(fs)
    f_ann_a, f_ann_c = ann_arith(fs) * 100, ann_cagr(fs) * 100
    nyf = neg_years(fs)
    _, Wg_win, _ = build_book(df12, relw13, gear=1.0)
    grossmax = float(Wg_win.abs().sum(axis=1).max())
    log('')
    log('REVEAL book: 12-pool refit under %s target at invariant cap, gear 1.0, n=%d (%s..%s)' % (win['name'], len(fs), str(fs.index[0].date()), str(fs.index[-1].date())))
    log('  FS SR=%.6f (incumbent 3.751429)  ann arith=%.4f%%  cagr=%.4f%%  MDD=%.4f%%  negyrs=%d' % (f_sr, f_ann_a, f_ann_c, f_mdd * 100, len(nyf)))
    log('  grossmax=%.9f  Wmax_sf=%.4fx  CFX4 relw=%.1e' % (grossmax, win['wmax'], win['cfx']))
    have12 = [n for n in names12 if isr[n].notna().sum() > 0]
    n12a = len(isr[have12].dropna()); n12b = n12a
    shrink_g8 = 1.0 - n12b / float(n12a)
    log('  G8 fit-window complete rows: %d -> %d (same pool), shrink=%.4f%% (bar <= 2%%)' % (n12a, n12b, shrink_g8 * 100))
    bins = [('2017-18', '2017', '2018'), ('2019-20', '2019', '2020'), ('2021-22', '2021', '2022'),
            ('2023-24', '2023', '2024'), ('2025-26', '2025', '2026')]
    dsrc = []
    for lbl, a, b in bins:
        m_c = fs[(fs.index >= a + '-01-01') & (fs.index <= b + '-12-31')]
        m_i = champ[(champ.index >= a + '-01-01') & (champ.index <= b + '-12-31')]
        dsr = sr(m_c) - sr(m_i)
        dsrc.append(dsr)
        log('  bin %s dSR=%+.4f (cand %.4f vs inc %.4f)' % (lbl, dsr, sr(m_c), sr(m_i)))
    pos = sum(1 for d_ in dsrc if d_ > 0)
    g1 = (f_ann_c >= 0.20) or (f_ann_a >= 0.20)
    g2 = grossmax <= 1.6 + 1e-9
    g3 = f_mdd >= -0.07
    g4 = len(nyf) == 0
    g5 = win['cfx'] == 0.0
    g6 = win['wmax'] <= 2.0 + 1e-9
    g7 = (pos >= 4) and (min(dsrc) >= -0.10) and (f_sr > FS_BAR)
    g8 = shrink_g8 <= 0.02
    gates = [g1, g2, g3, g4, g5, g6, g7, g8]
    labels = ['1 FS ann>=20pct', '2 gross<=1.6', '3 FS MDD>=-7pct', '4 0 FS neg yrs',
              '5 CFX4=0', '6 Wmax_sf<=2.0x (k=11)', '7 OOS police', '8 fit-window shrink<=2pct']
    for l, g in zip(labels, gates):
        log('  GATE %-24s %s' % (l, 'PASS' if g else 'FAIL'))
    if all(gates):
        verdict = 'ADOPTABLE (8/8) -> proceed to full battery per pre-commit'
    else:
        fails = [l for l, g in zip(labels, gates) if not g]
        verdict = 'REJECT - failed gates: ' + ', '.join(fails) + ' (no second reveal per pre-commit)'
    pd.DataFrame(dict(ret=fs.values), index=fs.index).to_csv(OUT + '/candidate_' + win['name'] + '_atcap_daily.csv')

log('')
log('VERDICT: ' + verdict)
champ_sha_post, wgt_sha_post = sha16(CHAMP), sha16(WGT)
log('# Champion sha16 post-run: ' + champ_sha_post + ' / weights ' + wgt_sha_post + ' (pre==post: ' + str((champ_sha_pre == champ_sha_post) and (wgt_sha_pre == wgt_sha_post)) + ')')
assert champ_sha_pre == champ_sha_post and wgt_sha_pre == wgt_sha_post
with open(OUT + '/driver_iter31.log', 'w') as fh:
    fh.write(chr(10).join(LOG) + chr(10))
print('LOG WRITTEN:', OUT + '/driver_iter31.log')
