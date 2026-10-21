
"""S4: attack on HUNT_CRYPTO2-R7 (Deribit DVOL) rejection.

Row says: best netSR 0.764 (ETH_VOV_60) << sr_min 1.0; span_class inception_fail;
"Decorrelation NOT the binding gate ... no alpha to carry it".

Attack: (c) SPAN/DATA DEFECT - the candidate is span-dead by rule (inception 2021 >
2013-01-01). Is there nevertheless an ADMISSIBLE overlay gain on the DVOL span?
Failure mode (a)/(d): was a positive result discarded?
We reuse their engine (import) so their construction is not misrepresented.
"""
import os
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
R7 = ROOT + "/campaign/agents/chief/coord/HUNT_CRYPTO2/work_r7"
sys.path.insert(0, R7)
sys.path.insert(0, ROOT + "/campaign")
import r7_dvol_engine as E  # their engine, unmodified


def stats(r):
    r = pd.Series(r).dropna()
    nav = (1 + r).cumprod()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {"n": len(r), "ann": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
            "sr": float(r.mean() / r.std(ddof=1) * 252 ** 0.5),
            "mdd": float((nav / nav.cummax() - 1).min()) * 100,
            "vol": float(r.std(ddof=1) * 252 ** 0.5) * 100,
            "neg": int((yr < 0).sum())}


champ = pd.read_csv(E.CHAMP, parse_dates=['date']).set_index('date')['ret']
px = {s: pd.read_csv(os.path.join(ROOT, 'tools/quant/data/more_crypto/%s.csv' % s),
                     parse_dates=['date']).set_index('date')['close'].astype(float)
      for s in ('BTC', 'ETH')}

# ---- reproduce the best config's book exactly as their run_config does ----
def dvol_book(sym, rule, param):
    dvol = E.load_dvol(sym)
    pos_decision, _ = E.weekly_positions(dvol, rule, param)
    rets = px[sym].pct_change()
    idx = pos_decision.dropna().index.intersection(rets.dropna().index).intersection(champ.index)
    ref = champ.reindex(idx).dropna()
    idx = ref.index
    r = rets.reindex(idx).fillna(0.0)
    pos_d = pos_decision.reindex(idx).ffill().fillna(0.0)
    scale = E.vol_target_scale(r.to_frame('a')).iloc[:, 0]
    sig = (E.lag_signal(pos_d) * scale).fillna(0.0)
    book_gross = sig * r
    dW = sig.diff().abs().fillna(0.0)
    dW.iloc[0] = abs(sig.iloc[0])
    cost = dW * E.COST_BPS / 1e4 + (-sig).clip(lower=0.0) * 0.005 / E.ANN
    return book_gross - cost, book_gross, sig, ref


print("COST_BPS from bt.engine =", E.COST_BPS, " ANN =", E.ANN)
print()
print("=== reproduction of their published best config ===")
for sym, rule, param, pub in [("ETH", "vov", 60, 0.764), ("BTC", "vov", 60, None),
                              ("ETH", "zlevel", 90, None), ("ETH", "trend", 60, None)]:
    net, gross, sig, ref = dvol_book(sym, rule, param)
    s = stats(net)
    print("  DVOL_%s_%s_%s  n=%d  netSR %.4f (published %s)  grossSR %.4f  netAnn %.2f%%  "
          "vol %.2f%%  meanGross(sig) %.4f  corr_champ(book) %.4f"
          % (sym, rule.upper(), param, s["n"], s["sr"], pub, stats(gross)["sr"],
             s["ann"], s["vol"], float(sig.abs().mean()),
             float(pd.concat([net.rename('a'), ref.rename('b')], axis=1).corr().iloc[0, 1])))

# ---- the ATTACK: blend into the champion on the DVOL span, both constructions ----
print()
print("=== ATTACK: blend best DVOL book into champion on the shared span ===")
net, gross, sig, ref = dvol_book("ETH", "vov", 60)
j = pd.concat([champ.rename("c"), net.rename("d")], axis=1, join="inner").dropna()
sc = stats(j.c)
print("  champion on DVOL span: n=%d ann %.4f sr %.4f mdd %.4f" % (
    sc["n"], sc["ann"], sc["sr"], sc["mdd"]))
print()
print("  (A) additive overlay  blend = champ + w*dvol     [gross expands]")
print("      %-7s %-9s %-10s %-10s %-9s %-9s" % ("w", "grossMean", "dAnn_pp", "dSR", "dMDD_pp", "neg"))
for w in (0.05, 0.10, 0.15, 0.25):
    b = j.c + w * j.d
    sb = stats(b)
    gmean = 1.6 + w * float(sig.abs().mean())
    print("      %-7.2f %-9.4f %+10.4f %+10.5f %+9.4f %-9d" % (
        w, gmean, sb["ann"] - sc["ann"], sb["sr"] - sc["sr"], sb["mdd"] - sc["mdd"], sb["neg"]))
print()
print("  (B) gross-neutral      blend = (1-w)*champ + w*dvol  [gross ~ 1.6]")
print("      %-7s %-9s %-10s %-10s %-9s %-9s" % ("w", "grossMean", "dAnn_pp", "dSR", "dMDD_pp", "neg"))
for w in (0.05, 0.10, 0.15, 0.25, 0.50):
    b = (1 - w) * j.c + w * j.d
    sb = stats(b)
    gmean = (1 - w) * 1.6 + w * float(sig.abs().mean())
    print("      %-7.2f %-9.4f %+10.4f %+10.5f %+9.4f %-9d" % (
        w, gmean, sb["ann"] - sc["ann"], sb["sr"] - sc["sr"], sb["mdd"] - sc["mdd"], sb["neg"]))
