#!/usr/bin/env python3
"""r7_blotter_day_recon.py — AUDIT_RECON R7 centerpiece (charter item a).

DAY-granularity reconciliation of the champion's daily |dW|-charged cost series
(rawew13v2_build: to = Wg.diff().abs().sum(axis=1), day-1 NaN->0 uncharged) against
the committed trade blotter BLOTTER_CHAMP_RAWEW13v2_GEAR16.csv
(date,sleeve,instrument,side,price,qty_notional,weight_from,weight_to,cost_bps).

Independence: my own weight algebra (nav.shift(1) causal, relw from the committed
weights CSV as INPUT, row-normalize, x GEAR/13) — builder engine called only as a
CROSS-CHECK (expect ~1e-16). No import of bt/verify_champion or blotter_champ.

Publishes (R5 scalar-probe lesson: generator ships WITH the artifact):
  r7_blotter_day_recon.json      the reconciliation row + mismatch tables
  r7_blotter_day_bydate.csv      4805-row day table (charged vs ledger vs dev)
  r7_weight_mismatch_rows.csv    any (date,sleeve) weight mismatch rows (expect empty)
Exit 0 only if every gate passes; exit 1 otherwise (fail-closed).
"""
import sys, os, json, hashlib
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/scripts")
import rawew13v2_build as b  # PATHS/load + engine cross-check ONLY

OUTD = f"{ROOT}/campaign/agents/chief/coord/AUDIT_RECON/r7"
GEAR, BPS, RATE = b.GEAR, b.BPS, b.RATE
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGTS  = f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv"
LEDGER= f"{ROOT}/campaign/results/BLOTTER_CHAMP_RAWEW13v2_GEAR16.csv"

def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]

def main():
    gates = {}
    names = b.NAMES
    K = len(names)
    # --- my own reconstruction (independent algebra; relw is an INPUT, frozen) ---
    df = pd.DataFrame({n: b.load(b.PATHS[n]).dropna() for n in names})
    df = df[df.index >= '2008-03-31']
    relw = pd.read_csv(WGTS, index_col=0).iloc[:, 0]
    relw.index = relw.index.str.strip()
    assert list(relw.index) == names, "weights CSV slot order != builder NAMES"
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)      # T+1 causal
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * K
    Wg = d2 * (GEAR / K)
    to_mine = Wg.diff().abs().sum(axis=1).fillna(0.0)            # builder convention: day-1 = 0
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    net_mine = pd.Series(port, index=df.index) - to_mine * BPS/1e4 - max(GEAR-1,0)*RATE/252

    # --- engine cross-check (charged series + nav bytes) ---
    net_eng, _, gross_eng, to_eng, _ = b.build()
    gates['engine_to_maxdev'] = float((to_mine - to_eng).abs().max())
    j = pd.concat([net_mine.rename('mine'), net_eng.rename('eng')], axis=1).dropna()
    gates['engine_net_maxdev'] = float((j.mine - j.eng).abs().max())
    old = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
    jc = pd.concat([old.rename('old'), net_mine.rename('mine')], axis=1, join='inner').dropna()
    gates['champion_byterepro_maxdev'] = float((jc.old - jc.mine).abs().max())
    gates['champion_byterepro_n'] = int(len(jc))

    # --- ledger ---
    led = pd.read_csv(LEDGER, parse_dates=['date'])
    led['cost_ret'] = led['qty_notional'] * led['cost_bps'] / 1e4
    led_qty = led.groupby('date')['qty_notional'].sum()
    led_cost = led.groupby('date')['cost_ret'].sum()

    # --- DAY-granularity reconciliation ---
    byd = pd.DataFrame({'charged_qty': to_mine, 'charged_cost_bp': to_mine * BPS})
    byd = byd.join(led_qty.rename('ledger_qty'), how='left').fillna({'ledger_qty': 0.0})
    byd = byd.join(led_cost.rename('ledger_cost_bp'), how='left').fillna({'ledger_cost_bp': 0.0})
    byd['ledger_cost_bp'] = byd['ledger_cost_bp'] * 1e4
    byd['dev_qty_exday1'] = (byd.ledger_qty - byd.charged_qty).where(byd.index > byd.index[0])
    byd['absdev'] = byd.dev_qty_exday1.abs()
    frozen = byd.index[(byd.charged_qty <= 1e-14) & (byd.ledger_qty <= 1e-14)]
    gates['days_total'] = int(len(byd))
    gates['days_with_ledger_trades'] = int((byd.ledger_qty > 0).sum())
    gates['frozen_days'] = [str(t.date()) for t in frozen]
    gates['day_recon_n_exday1'] = int(byd.dev_qty_exday1.notna().sum())
    gates['day_recon_max_absdev_exday1'] = float(byd['absdev'].max())
    gates['day_recon_days_over_1e-9'] = int((byd['absdev'] > 1e-9).sum())
    tol = 1e-7  # 8-dp rounding on up to 12 rows/day => <=6e-8 worst case
    gates['day_recon_tol'] = tol
    gates['day_recon_days_over_tol'] = int((byd['absdev'] > tol).sum())
    d1 = byd.index[0]
    gates['day1_date'] = str(d1.date())
    gates['day1_charged_qty'] = float(byd.at[d1, 'charged_qty'])
    gates['day1_ledger_qty'] = float(byd.at[d1, 'ledger_qty'])
    gates['day1_ledger_cost_bp'] = float(byd.at[d1, 'ledger_cost_bp'])
    yrs = len(byd) / 252.0
    gates['charged_total_bp'] = float(byd.charged_qty.sum() * BPS)
    gates['charged_bp_per_yr'] = float(byd.charged_qty.sum() * BPS / yrs)
    gates['ledger_total_bp'] = float(byd.ledger_cost_bp.sum())
    gates['ledger_bp_per_yr'] = float(byd.ledger_cost_bp.sum() / yrs)
    gates['exday1_ledger_bp_per_yr'] = float((byd.ledger_cost_bp.sum() - byd.at[d1,'ledger_cost_bp']) / yrs)

    # --- per-sleeve reconciliation (blotter_champ RECON gate, my own numbers) ---
    pw = Wg.shift(1).fillna(0.0)
    dw = (Wg - pw).abs()
    ps = pd.DataFrame({'ledger': led.groupby('sleeve')['qty_notional'].sum()})
    ps['charged'] = dw.sum()
    ps['dev'] = (ps.ledger - ps.charged).abs()
    gates['sleeves_in_ledger'] = int(led.sleeve.nunique())
    gates['sleeves_absent'] = sorted(set(names) - set(led.sleeve.unique()))
    gates['sleeve_recon_maxdev'] = float(ps['dev'].max())
    gates['sleeve_recon_worst'] = str(ps['dev'].idxmax())
    # rounding-aware bound: qty is round(|dw|,8) => <=5e-9/row accumulates over rows
    nrow = led.groupby('sleeve').size()
    ps['rows'] = nrow
    ps['round_bound'] = 5e-9 * nrow
    gates['sleeve_recon_worst_bound'] = float(ps.at[gates['sleeve_recon_worst'], 'round_bound'])

    # --- day-WEIGHT mismatch rows (weight_from/weight_to vs my path) ---
    chk = led.merge(Wg.stack().rename('my_w').reset_index()
                    .rename(columns={'level_0': 'date', 'level_1': 'sleeve', 'my_w': 'my_wto'}),
                    on=['date', 'sleeve'], how='left')
    chk = chk.merge(pw.stack().rename('my_wfrom').reset_index()
                    .rename(columns={'level_0': 'date', 'level_1': 'sleeve', 'my_wfrom': 'my_wfrom'}),
                    on=['date', 'sleeve'], how='left')
    chk['dev_to'] = (chk.weight_to - chk.my_wto).abs()
    chk['dev_from'] = (chk.weight_from - chk.my_wfrom).abs()
    bad = chk[(chk.dev_to > 1e-8) | (chk.dev_from > 1e-8)]
    bad[['date','sleeve','weight_from','weight_to','my_wfrom','my_wto','dev_to','dev_from']] \
        .to_csv(f"{OUTD}/r7_weight_mismatch_rows.csv", index=False)
    gates['weight_rows_checked'] = int(len(chk))
    gates['weight_mismatch_rows'] = int(len(bad))
    gates['weight_maxdev_to'] = float(chk.dev_to.max())
    gates['weight_maxdev_from'] = float(chk.dev_from.max())

    # --- ledger self-connectivity: weight_from[t] == prior weight_to[t-1] per sleeve ---
    gaps = 0
    for n, g in led.sort_values('date').groupby('sleeve'):
        wf, wt = g.weight_from.values, g.weight_to.values
        gaps += int((np.abs(wf[1:] - wt[:-1]) > 1e-8).sum())
    gates['ledger_self_gap_rows'] = gaps

    # --- pins ---
    gates['sha_champion'] = sha16(CHAMP)
    gates['sha_weights'] = sha16(WGTS)
    gates['sha_ledger'] = sha16(LEDGER)
    gates['sha_builder'] = sha16(f"{ROOT}/campaign/scripts/rawew13v2_build.py")
    gates['ledger_rows'] = int(len(led))

    byd.to_csv(f"{OUTD}/r7_blotter_day_bydate.csv")
    ok = (gates['champion_byterepro_maxdev'] < 1e-12
          and gates['engine_to_maxdev'] < 1e-12
          and gates['day_recon_days_over_tol'] == 0
          and gates['weight_mismatch_rows'] == 0
          and gates['ledger_self_gap_rows'] == 0
          and gates['sleeve_recon_maxdev'] <= gates['sleeve_recon_worst_bound'])
    gates['GATE_OK'] = bool(ok)
    json.dump(gates, open(f"{OUTD}/r7_blotter_day_recon.json", 'w'), indent=1)
    print(json.dumps(gates, indent=1))
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
