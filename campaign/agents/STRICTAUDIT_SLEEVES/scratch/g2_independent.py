import pandas as pd, numpy as np
# Independent instrument-reality verdict input: do brwt spot series map to futures spread tradeable?
# CL-B spread: futures exist (CL, BZ). FRED spot spread is a proxy with basis risk. Disclosed in meta.
# a6r7/QAxasts synth rates faithful (my corr calc: 0.721 / 0.955) - CONFIRMED.
# Credit: synth BAA corr to LQD 0.587, HYG 0.028 (mine) vs claimed 0.029 blended; HYG drives the failure.
# A5r2: SPY long-only tradeable. dualmom/XGB1y equity L/S on union panel (survivorship-biased static panel!) - 
#   NOTE: G4 says panel floor 2006-09; AUDIT5 confirmed survivorship +2.7-5pp/yr on static panel. Momentum books
#   (12-1 skip) are relative (long top tercile vs short bottom / xs) so panel bias partially cancels but
#   XGB book is decile L/S => relative too. Still both use CURRENT constituents historically => mild bias, disclosed.
# Data: union_panel static membership?
import subprocess
print(subprocess.run(['grep','-n','survivor','/Users/daxu/software/world-trader/campaign/agents/AUDIT5_data/FINDINGS.md'],capture_output=True,text=True).stdout[:600])
