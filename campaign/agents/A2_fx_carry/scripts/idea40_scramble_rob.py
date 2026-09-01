"""Scramble robustness for saved carry W11: 500 perms x 3 seeds, pre-vt net."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
import numpy as np, pandas as pd
R=load_pair_rets(); yd=load_ydiff(); acc=yd/100/252; Rf=R.fillna(0)
pos=carry_ls_pos(yd,top=1,bot=1,rule="W")
for seed in [7,42,123]:
    real,p=scramble_df(pos,Rf,n=500,seed=seed)
    print(f"seed {seed}: real={real:.3f} p={p:.4f}")
