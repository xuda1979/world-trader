"""Final record: rev-direction best config yearly + 2008+ windows for all ideas' best."""
import sys; sys.path.insert(0,'.')
import numpy as np, pandas as pd
from d1_lib import *
from idea1 import build, sp, ex, rfc

net,sig=build(504,21,1.0,'rev')
s=stats(net); h=halves(net)
print(f"idea1 REV w504 s21 thr1.0: SR={s['sr']:.2f} mdd={s['mdd']:.1f}% negy={s['negy']} worst={s['worst']:.1f}% H1={h[0]:.2f} H2={h[1]:.2f} corr_champ={corr_to(net,CHAMP):.3f}")
print(" negyrs:",{k:round(v*100,1) for k,v in s['yearly'].items() if v<0})
n08=net[net.index>='2008-09-01']; s8=stats(n08)
print(f" 2008+: SR={s8['sr']:.2f} negy={s8['negy']} worst={s8['worst']:.1f}%")
p,_=rotation_scramble(net,sig,ex.reindex(sig.index),rfc.reindex(sig.index),seed=3)
print(f" rotation scramble p={p:.3f}")
