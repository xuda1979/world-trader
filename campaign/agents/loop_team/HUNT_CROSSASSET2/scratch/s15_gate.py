"""Gate battery on GLD variants. Same conventions as s14 (correct scramble)."""
import sys; sys.path.insert(0,'.')
import pandas as pd, numpy as np
from s14_final import etf, mkbook, gates, mkdv
G=etf('GLD')
for lb,cap in [(126,2.0),(63,2.0),(126,3.0),(252,2.0),(126,1.5)]:
    net,p_,r_=mkbook(G,etf('TLT'),lb,cap)
    gates(f'GLD-TLT z lb{lb} cap{cap}',net,[p_],[r_])
for lb in [126,252]:
    net,p_,r_=mkbook(G,etf('IEF'),lb,2.0)
    gates(f'GLD-IEF z lb{lb}',net,[p_],[r_])
for lb in [126,252]:
    net,p_,r_=mkbook(etf('GLD'),etf('XLB'),lb,2.0)
    gates(f'GLD-XLB z lb{lb}',net,[p_],[r_])
