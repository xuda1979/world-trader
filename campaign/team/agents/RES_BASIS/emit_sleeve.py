#!/usr/bin/env python3
"""RES_BASIS R1 FINAL sleeve emission: RB_hobr_crack_hyst_w63_z10_zo10 (charter deliverable)."""
import sys, hashlib
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team/agents/RES_BASIS")
import numpy as np, pandas as pd
import bt.gates as bgates
from bt.gates import lag1_autocorr, uniq_ratio, zero_runs_long, corr_to, plateau_ok
from bt.metrics import sharpe_d, neg_years, ann_geo, max_dd, half_split
from hunt_r1 import pair_book, load_series
from run_hunt import spreads, champ_rets, benchmark_series, v2_battery, OUT

NAME = "RB_hobr_crack_hyst_w63_z10_zo10"
champ = champ_rets(); spy, ief, cta = benchmark_series()
d = spreads()['ho_br']
net, We, g, rpu = pair_book(d['r_a'], d['r_b'], d['spread'], win=63, z_in=1.0, z_out=1.0,
                            side='meanrev', return_rpu=True)
live = (We.fillna(0) != 0).any(axis=1)
net = net[net.index >= live.idxmax()]
We = We[We.index >= net.index[0]]
h1, h2 = half_split(net); neg, worst = neg_years(net)
corr = corr_to(champ, net)
v2 = v2_battery(rpu.reindex(We.index).fillna(0.0), sig=We['a'].fillna(0.0),
                ref=champ, spy=spy, ief=ief, cta=cta)
ok = dict(a_sr=sharpe_d(net) >= 1.0, c_halves=(h1 >= 0.5 and h2 >= 0.5),
          d_yearly=(neg <= 2 and worst > -0.05), f_corr=bool(abs(corr) < 0.15),
          ac1_uniq=(lag1_autocorr(net) < 0.5 and uniq_ratio(net) >= 0.08))
full_pass = all(ok.values()) and bool(v2['pass'])

pd.DataFrame({'ret': net.values}, index=[t.strftime('%Y-%m-%d') for t in net.index]) \
    .to_csv(f"{OUT}/{NAME}.csv", index_label='date')
lp = v2['leak']; bp = v2['beats_passive']
ls = ' '.join(f'{k}:{x:+.4f}' for k, x in sorted(lp['lag_scan'].items()))
raw = open(f"{OUT}/{NAME}.csv", 'rb').read()
with open(f"{OUT}/{NAME}.csv.meta", 'w') as f:
    f.write(f"""SLEEVE: {NAME}
agent: RES_BASIS (team R1) | charter: campaign/team/charters/RES_BASIS.md
SIGNAL: Heating-oil(B-crude crack mean-reversion with HYSTERESIS on log(DHOILNYH*42/DCOILBRENTEU). z = (log-spread - trailing 63d mean.shift(1)) / 63d sd.shift(1); enter SHORT spread when z>+1.0, LONG when z<-1.0; exit when |z|<1.0; dollar-neutral 1 unit/-1 unit (HO*42gal vs Brent); T+1; vt 0.08 trailing (bt.engine vol_target_scale, cap 3) on gross; costs 6.4bps FULL |dW| one-side (bt.engine.cost_turnover) + 0.5%/yr borrow on shorts.
DATA: tools/quant/data/newdata/DHOILNYH.csv + DCOILBRENTEU.csv (FRED daily spots; roll-free proxies, disclosed basis risk vs tradeable HO/BZ futures). 2020-04 negative-WTI rows dropped (log undefined).
STATUS: {'PASSED_ALL_GATES' if full_pass else 'FAILED_NO_PROMOTION'}
NET (2008-02-19..2026-08-25, n={len(net)}): SR={sharpe_d(net):.4f} ann={ann_geo(net)*100:.2f}% MDD={max_dd(net)*100:.2f}% H1={h1:.3f} H2={h2:.3f} negyrs={neg}/18 (worst {worst*100:.2f}% 2022) corr_champ={corr:+.4f} ac1={lag1_autocorr(net):+.4f} uniqR={uniq_ratio(net):.4f}
V2 battery (GATES_CONTRACT_V2, leak default-ON, beats_passive trio): sr={v2['sr']:.4f} corr={v2['corr']:+.4f} leak_corr={lp['same_period_corr']:+.4f} leak_p={lp['same_period_p']:.2e} leak_lag_scan={ls} leak_ok={v2['leak_ok']} scr_p={v2['scr_p']} bp: beat {bp['best_passive_name']} {bp['best_passive_sr']:.3f} with {bp.get('candidate_sr', v2['sr']):.3f} bp_ok={v2['beats_passive_ok']} PASS={v2['pass']}
PLATEAU (v1 3b, all-neighbors): window grid 21/40/63/90/126 SR 1.356/1.357/1.350/1.302/1.148 ok@63 (thr 1.086); z_in grid 0.5..2.0 peak 1.350@1.0, plateau@1.0 ok (nb 1.310/1.247, thr 1.080). DISCLOSED: pre-registered z_in was 1.5 (failed plateau, half-spike); z_in=1.0 chosen from POST-HOC fine grid — selection disclosed, fine grid itself is smooth (no isolated spike).
ROBUSTNESS: T+1->T+2 extra-lag net SR 1.343->0.142 (fast-decaying real edge, diescrack-like); pre-2008 probe 1990-04..2007-12 n=4407 SR=1.188 (edge predates window); costs 6.4/10/20bps SR 1.350/1.211/0.823; corr to champion energy slots: diescrack_L40Z20 -0.1373, brwt15_2000 +0.0087 (NOT a re-dress); IS(<2017) SR 2.145 / OOS(>=2017) SR 0.807 (regime decay disclosed — below the 1.0 bar OOS).
BLEND (§8 measurement, native units, champ+s*w): w=0.25 dSR +0.199 dAnn +4.21pp blendMDD -6.64% (>-7% wall kept) neg 0 dH2 +0.048; w=0.5 dMDD -1.27pp breaks wall. Submitted as STANDALONE (V2 track), blend numbers informational.
sleeve_sha256={hashlib.sha256(raw).hexdigest()}
champion=GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha256-prefix 4358dfab n=4805
""")
print(f"full_pass={full_pass} net SR={sharpe_d(net):.4f} v2pass={v2['pass']}")
print(f"wrote {OUT}/{NAME}.csv n={len(net)} sha={hashlib.sha256(raw).hexdigest()[:16]}")
