import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
sys.path.insert(0, '.')
import tff_eng
tff_eng.DATA = '/Users/daxu/software/world-trader/tools/quant/data'
exec(open('run_tff.py').read())
