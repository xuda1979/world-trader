#!/usr/bin/env python3
"""HUNT_MACRO2 R7 — dump evidence JSON: my-side derivation vs published scorecards."""
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("eng", HERE / "r7_repro_engine.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BORROW = json.load(open(mod.ROOT + "/campaign/agents/chief/coord/CAMP_SHORT/work_r6/r6_borrow_repro.json"))
COST = json.load(open(mod.ROOT + "/campaign/agents/chief/coord/CAMP_SHORT/work_r6/r6_cost_repro.json"))
LEAK = json.load(open(mod.ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r5/leak_probe_r5.json"))

h, sha = mod.champion_headline()
b = mod.borrow()
c = mod.cost()
s = mod.scalar_probe()
w = mod.wide_probe()


def compare(mine, pub):
    out, bad = {}, []
    for k, v in pub.items():
        if k not in mine:
            bad.append(f"{k}: MISSING")
            continue
        dev = abs(mine[k] - v["theirs"])
        ok = dev <= v["tol"]
        out[k] = dict(mine=mine[k], theirs=v["theirs"], abs_dev=dev, tol=v["tol"], match=bool(ok))
        if not ok:
            bad.append(f"{k}: mine={mine[k]!r} theirs={v['theirs']!r} dev={dev:.3e}")
    extra = set(mine) - set(pub)
    return dict(verdicts=out, mismatches=bad, extra_keys=sorted(extra),
                n=len(out), n_match=sum(1 for x in out.values() if x["match"]))


res = dict(
    agent="HUNT_MACRO2-R7",
    champion=dict(sha16=sha[:16], **{k: (v * 100 if k in ("ann", "mdd") else v)
                                     for k, v in h.items()}),
    borrow=compare(b, BORROW["verdicts"]),
    cost=compare(c, COST["verdicts"]),
    scalar_probe=s,
    wide_probe=w,
    published_scalar=dict(LEAK["scalar_agg_turnover_vs_champ_ret"]),
    charter_named=dict(
        faithful_absdWg_champ_span_corr=s["faithful_champ_span"]["corr"],
        faithful_absdWg_full_history_corr=s["faithful_full_history"]["corr"],
        published_scalar_corr=LEAK["scalar_agg_turnover_vs_champ_ret"]["same_period_corr"],
        published_scalar_p=LEAK["scalar_agg_turnover_vs_champ_ret"]["same_period_p"],
        signed_noise_sum_corr=s["signed_noise_sum"]["corr"],
        signed_noise_sum_p=s["signed_noise_sum"]["p"],
        signed_noise_sum_std=s["signed_noise_sum"]["std"],
        borrow_embedded_bps_yr=b["B9.embedded_bps_yr"],
        borrow_100pct_bps_yr=b["B11.borrow100_bps_yr"],
        borrow_tier2_bps_yr=b["B9.tier2_bps_yr"],
        borrow_tier8_bps_yr=b["B9.tier8_bps_yr"],
    ),
)

outp = HERE / "r7_repro_evidence.json"
json.dump(res, open(outp, "w"), indent=1, default=str)
print(f"wrote {outp}")
print(f"borrow: {res['borrow']['n_match']}/{res['borrow']['n']} match; "
      f"mismatches={res['borrow']['mismatches']}")
print(f"cost:   {res['cost']['n_match']}/{res['cost']['n']} match; "
      f"mismatches={res['cost']['mismatches']}")
print(f"borrow extra keys (mine not in published): {res['borrow']['extra_keys']}")
print(f"cost   extra keys: {res['cost']['extra_keys']}")
print(f"champion sha16={sha[:16]} ann={h['ann']*100:.4f}% SR={h['sr']:.4f} "
      f"MDD={h['mdd']*100:.4f}% neg={h['neg']} n={h['n']}")
cn = res["charter_named"]
print(f"faithful |dWg| champ-span corr {cn['faithful_absdWg_champ_span_corr']:+.6f} vs "
      f"published {cn['published_scalar_corr']:+.6f} (p {cn['published_scalar_p']:.4f}); "
      f"signed-noise sum {cn['signed_noise_sum_corr']:+.6f}/p {cn['signed_noise_sum_p']:.4f} "
      f"(std {cn['signed_noise_sum_std']:.2e})")
print(f"borrow embedded {cn['borrow_embedded_bps_yr']:.4f} bps/yr; 100% drift "
      f"{cn['borrow_100pct_bps_yr']:.4f}; tier2 {cn['borrow_tier2_bps_yr']:.4f}; "
      f"tier8 {cn['borrow_tier8_bps_yr']:.4f}")
