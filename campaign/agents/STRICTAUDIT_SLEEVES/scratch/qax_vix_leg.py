import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality')
from r7_idea5_breadth import panel, RET_PAN
# VIXS leg: synthetic spot-VIX return (no roll carry). Short-vol-below-MA = short synthetic VIX spot.
# Real tradeable = short VIX futures. Since synth spot-VIX has NO roll carry, and VIX futures are usually
# in contango (futures > spot), short-futures earns roll carry the synth doesn't => synth is CONSERVATIVE? 
# Actually in contango short futures profits more (roll decay) => synth understates. BUT in backwardation spikes,
# short synth loses less... report only.
print("VIXS leg summary:")
v = RET_PAN['VIXS'].dropna()
print(f"  daily mean {v.mean()*100:.3f}% std {v.std()*100:.2f}% min {v.min()*100:.1f}% (worst day)")
print(f"  ann SR of leg (ungated) {v.mean()/v.std()*np.sqrt(252):.2f}")
