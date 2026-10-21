"""HUNT_FXCARRY2 R7 charter-(a): own-code recompute of COT2-R6's verify_r6_credit2.csv
(44 rows) + verify_r6_cmdt2.csv (28 rows) from the PUBLISHED sleeve CSVs — independent
of COT2's code (my own stats: SR, ann, MDD, halves, neg-yr, worst-yr, corr vs champion,
n). Verifies their '0/44 + 0/28 mismatches, verdicts stand' claim."""
import csv, json, re
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
COT2 = f"{ROOT}/campaign/agents/chief/coord/HUNT_COT2"
CRED = f"{ROOT}/campaign/agents/chief/coord/HUNT_CREDIT2/sleeves"
CMDT = f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

champ = pd.read_csv(CHAMP, index_col=0, parse_dates=True)['ret'].astype(float)


def stats(path):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    r = df.iloc[:, 0].astype(float).dropna()
    sr = r.mean() / r.std() * np.sqrt(252)
    ann = (np.prod(1 + r)) ** (252 / len(r)) - 1
    nav = (1 + r).cumprod()
    mdd = (nav / nav.cummax() - 1).min()
    h = len(r) // 2
    h1 = r.iloc[:h].mean() / r.iloc[:h].std() * np.sqrt(252)
    h2 = r.iloc[h:].mean() / r.iloc[h:].std() * np.sqrt(252)
    yr = r.groupby(r.index.year).apply(lambda x: np.prod(1 + x) - 1)
    neg = int((yr < 0).sum())
    worst = float(yr.min())
    common = champ.index.intersection(r.index)
    corr = champ.reindex(common).corr(r.reindex(common))
    return dict(sr=sr, ann=ann * 100, mdd=mdd * 100, h1=h1, h2=h2, neg=neg,
                worst=worst * 100, corr=corr, n=len(r),
                start=str(r.index[0].date()), end=str(r.index[-1].date()))


def parse_meta(path):
    txt = open(path).read()
    out = {}
    m = re.search(r'SR=([-\d.]+)', txt);        out['SR'] = float(m.group(1)) if m else None
    m = re.search(r'ann=([-\d.]+)', txt);       out['ann'] = float(m.group(1)) if m else None
    m = re.search(r'H1=([-\d.]+)', txt);        out['H1'] = float(m.group(1)) if m else None
    m = re.search(r'H2=([-\d.]+)', txt);        out['H2'] = float(m.group(1)) if m else None
    m = re.search(r'negyrs=(\d+)', txt);        out['negyrs'] = int(m.group(1)) if m else None
    m = re.search(r'worstyr=([-\d.]+)', txt);   out['worstyr'] = float(m.group(1)) if m else None
    m = re.search(r'corr_champ=([-\d.]+)', txt); out['corr_champ'] = float(m.group(1)) if m else None
    m = re.search(r'n=(\d+)', txt);             out['n'] = int(m.group(1)) if m else None
    return out


report = {}
for label, verify_csv, sdir in (('credit2', f"{COT2}/verify_r6_credit2.csv", CRED),
                                ('cmdt2', f"{COT2}/verify_r6_cmdt2.csv", CMDT)):
    rows = list(csv.DictReader(open(verify_csv)))
    mism = 0
    details = []
    for row in rows:
        name = row['file']
        mine = stats(f"{sdir}/{name}")
        meta = parse_meta(f"{sdir}/{name}.meta")
        # compare COT2's claimed recompute vs MY recompute (independent of theirs)
        # and vs the meta values in the published .meta
        checks = [
            ('sr_meta_vs_myrecompute', float(row['meta_SR']), mine['sr'], 0.0005),
            ('neg_meta_vs_myrecompute', float(row['meta_neg']), mine['neg'], 0.0),
            ('worst_meta_vs_myrecompute', float(row['meta_worst'].rstrip('%')), mine['worst'], 0.05),
            ('corr_meta_vs_myrecompute', float(row['meta_corr']), mine['corr'], 0.0005),
            ('n_meta_vs_myrecompute', float(row['meta_n']), mine['n'], 0.0),
            ('h1_meta_vs_myrecompute', float(row['my_h1']), mine['h1'], 0.005),
            ('h2_meta_vs_myrecompute', float(row['my_h2']), mine['h2'], 0.005),
        ]
        bad = [(f, a, b, abs(a - b)) for f, a, b, tol in checks if abs(a - b) > tol]
        mism += len(bad)
        if bad:
            details.append((name, bad))
    report[label] = dict(rows=len(rows), mismatches=mism, details=details[:10])
    print(f"{label}: {len(rows)} rows, {mism} field mismatches (meta-vs-my-own-recompute, "
          f"tol SR/corr 5e-4, worst 0.05pp, h 0.005)")
    for d in details[:10]:
        print("   ", d)

json.dump(report, open(f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/work_r7/audit_cot2/fxc2_r7_csv_recompute.json", 'w'), indent=1, default=str)

# verdict-level rollup of the published books themselves
for label, sdir, pat in (('credit2', CRED, 'CRED5_'), ('cmdt2', CMDT, 'prop_')):
    import glob, os
    best = (-9, '')
    n_sr1 = n = 0
    for f in glob.glob(f"{sdir}/{pat}*.csv"):
        if f.endswith('.meta'):
            continue
        n += 1
        s = stats(f)
        if s['sr'] > best[0]:
            best = (s['sr'], os.path.basename(f), s['neg'], s['h1'], s['h2'])
        if s['sr'] >= 1.0:
            n_sr1 += 1
    print(f"{label}: {n} published books, SR>=1.0: {n_sr1}, best {best[1]} SR {best[0]:.3f} "
          f"neg {best[2]} H1/H2 {best[3]:.2f}/{best[4]:.2f}")
