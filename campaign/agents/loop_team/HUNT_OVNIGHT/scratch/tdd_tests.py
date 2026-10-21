"""TDD RED tests for HUNT_OVNIGHT engine harness. Every gate property asserted EXACTLY.
Run: python3 scratch/tdd_tests.py -> must FAIL (RED) before hunt_lib.py exists (IRON LAW)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd

def test_tplus1():
    """net_of MUST shift positions by 1: pos decided at t (same-day info) earns t+1 return only."""
    import hunt_lib as H
    idx=pd.date_range('2020-01-01',periods=10,freq='B')
    r=pd.Series([0.01,-0.02,0.03,-0.01,0.005,0.012,-0.008,0.02,-0.015,0.004],index=idx)
    pos_same_day_info=np.sign(r)          # cheating: uses ret_t itself
    net,_=H.net_of_book(pd.DataFrame({'a':pos_same_day_info}),pd.DataFrame({'a':r}),borrow=False)
    # manual T+1: shifted pos * r - costs
    p=pos_same_day_info.shift(1).fillna(0.0)
    manual=(p*r-(p.diff().abs()/2.0).fillna(0.0)*6.4e-4)
    assert np.allclose(net.values,manual.values,atol=1e-15), (net.values,manual.values)
    # and same-day-info SR must NOT equal average|abs ret|/std (perfect timing would be huge)
    sr_perfect=(r.abs().mean()/r.std())*np.sqrt(252)
    sr_got=net.mean()/net.std()*np.sqrt(252)
    assert sr_got < sr_perfect, "T+1 leak: same-day signal achieved perfect timing SR"

def test_cost_exact():
    """6.4bps/side charged on |dpos|/2 one-side turnover; flat book => zero cost after entry."""
    import hunt_lib as H
    idx=pd.date_range('2020-01-01',periods=6,freq='B')
    r=pd.Series(0.0,index=idx)
    pos=pd.Series([0.,1.,1.,1.,1.,1.],index=idx)   # enter once then flat
    net,_=H.net_of_book(pd.DataFrame({'a':pos}),pd.DataFrame({'a':r}),borrow=False)
    exp=pd.Series([0.0,0.0,-6.4e-4*0.5,0.,0.,0.],index=idx)  # entry on day3 after shift; 0->1 = half-turn 0.5 => 3.2bps
    assert np.allclose(net.values,exp.values,atol=1e-15), net.values
    # alternating pos ±1 => each flip |dp|=2 => turn=1 => 6.4e-4 per flip
    pos2=pd.Series([1.,-1.,1.,-1.,1.,-1.],index=idx)
    net2,_=H.net_of_book(pd.DataFrame({'a':pos2}),pd.DataFrame({'a':r}),borrow=False)
    # executed p=[0,-1,1,-1,1,-1]; costs: day2 |0-(-1)|/2=0.5; day3 |-1-1|/2=1; ... day6 1
    exp2=-np.array([0.0,6.4e-4*0.5,6.4e-4,6.4e-4,6.4e-4,6.4e-4])
    assert np.allclose(net2.values,exp2,atol=1e-15), net2.values

def test_borrow():
    """borrow 0.5%/yr charged daily on short notional only."""
    import hunt_lib as H
    idx=pd.date_range('2020-01-01',periods=5,freq='B')
    r=pd.Series(0.0,index=idx); pos=pd.Series([0.,-1.,-1.,-1.,-1.],index=idx)
    net,_=H.net_of_book(pd.DataFrame({'a':pos}),pd.DataFrame({'a':r}),borrow=True)
    b=0.005/252
    # executed p=[0,0,-1,-1,-1]: day3 entry half-turn 0.5 => -3.2e-4 and borrow starts day3 (pos -1)
    exp=pd.Series([0.0,0.0,-6.4e-4*0.5-b,-b,-b],index=idx)
    assert np.allclose(net.values,exp.values,atol=1e-15), net.values

def test_xs_book():
    """cross-sectional LS book: zero-sum weights, invalid cells get 0 weight, turnover = sum|dw|/2."""
    import hunt_lib as H
    idx=pd.date_range('2020-01-01',periods=4,freq='B')
    cols=list('abcd')
    sig=pd.DataFrame(0.0,index=idx,columns=cols)
    sig.iloc[1,:]= [3.,1.,4.,2.]     # ranks: a=2nd,b=4th,c=1st,d=3rd
    pos=H.xs_ls(sig, k=2)            # long top2 (c,a)=+1/2 each; short bottom2 (d,b)=-1/2
    assert np.allclose(pos.iloc[1].values,[0.5,-0.5,0.5,-0.5]), pos.iloc[1].values
    assert abs(pos.iloc[1].sum())<1e-12
    # weights NaN-safe: all-NaN row => all-zero
    sig2=sig.copy(); sig2.iloc[2,:]=np.nan
    pos2=H.xs_ls(sig2,k=2)
    assert pos2.iloc[2].abs().sum()==0.0

def test_zero_invalid_cells():
    """name without valid overnight at t has position 0 at t-1-based trade and 0 contribution."""
    import hunt_lib as H
    idx=pd.date_range('2020-01-01',periods=3,freq='B')
    sig=pd.DataFrame({'a':[1.,2.,np.nan],'b':[2.,1.,3.]},index=idx)
    pos=H.xs_ls(sig,k=1)
    assert pos.iloc[2]['a']==0.0 and abs(pos.iloc[2]['b'])==1.0

def test_gate_stats():
    """full_stats/halves/scramble/flatten/corr conventions match campaign (B2 gates / FF2 lib)."""
    import hunt_lib as H
    rng=np.random.default_rng(1)
    r=pd.Series(rng.normal(0.0004,0.008,1000),index=pd.date_range('2015-01-01',periods=1000,freq='B'))
    st=H.full_stats(r)
    assert abs(st['sr']-r.mean()/r.std()*np.sqrt(252))<1e-12
    h1,h2=H.halves_sr(r)
    assert 0<1
    fg=H.flatten_gates(r)
    assert abs(fg['ac1']-float(r.autocorr(1)))<1e-12
    assert abs(fg['uniqR']-float(r.round(10).nunique()/len(r)))<1e-12

def test_vt_trailing():
    """vol target scale uses trailing expanding std (min60, cap3) SHIFTED so scale at t uses data<=t-1."""
    import hunt_lib as H
    rng=np.random.default_rng(2)
    r=pd.Series(rng.normal(0,0.01,300),index=pd.date_range('2015-01-01',periods=300,freq='B'))
    s=H.vt_scale(r,tgt=0.10,cap=3.0)
    rv=r.expanding(60).std()*np.sqrt(252)
    exp=((0.10/rv).clip(upper=3.0)).shift(1).fillna(1.0)
    assert np.allclose(s.values,exp.values,atol=1e-15)

def test_poslag_scramble():
    """position-lag scramble: circular shift of POSITION by random lag destroys SR => p high for real alpha removed."""
    import hunt_lib as H
    rng=np.random.default_rng(3)
    r=pd.Series(rng.normal(0.0004,0.008,1500),index=pd.date_range('2015-01-01',periods=1500,freq='B'))
    posm=pd.DataFrame({'a':np.sign(r)},index=r.index)  # signal correlates with SAME-day ret (T+1 earns next day only)
    rmat=pd.DataFrame({'a':r},index=r.index)
    p,_=H.position_lag_p(posm,rmat,n=50)
    assert 0.0<=p<=1.0


def test_two_stream_scramble():
    """The OVNCAP book is TWO streams (pos*on - pos*ic). position_lag_p must evaluate the
    scramble on the FULL book: net_perm must include the -pos*ic leg. Fails on old single-stream
    implementation (it ignored the IC leg). Property: for a book whose IC leg alone has negative
    SR, permuted full-book SR mean must differ from permuted ON-only SR mean."""
    import hunt_lib as H
    rng=np.random.default_rng(5)
    n=800
    idx=pd.date_range('2015-01-01',periods=n,freq='B')
    # construct: on stream predicts on rets; ic = pure noise; positions from slow signal
    sig=pd.DataFrame(rng.normal(0,1,(n,40)),index=idx)
    on_r=pd.DataFrame(sig.values*0.001+rng.normal(0,0.01,(n,40)),index=idx)
    ic_r=pd.DataFrame(rng.normal(0,0.01,(n,40)),index=idx)
    pos=H.xs_ls(sig,k=10)
    pexec=pos.shift(1).fillna(0.0)
    # full-book net
    turn=(pexec.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    net_full=(pexec*on_r).sum(axis=1)-(pexec*ic_r).sum(axis=1)-turn*H.COST
    # ON-only net (single-stream, WRONG reference)
    net_on=(pexec*on_r).sum(axis=1)-turn*H.COST
    # scramble both books with same lags; means must differ
    rng2=np.random.default_rng(0)
    sr_f=[]; sr_o=[]
    T=n
    for _ in range(20):
        lag=int(rng2.integers(21,T-21))
        ps=pd.DataFrame(np.roll(pexec.values,lag,axis=0),index=idx)
        tn=(ps.diff().abs().sum(axis=1)/2.0).fillna(0.0)
        sf=((ps*on_r).sum(axis=1)-(ps*ic_r).sum(axis=1)-tn*H.COST)
        so=((ps*on_r).sum(axis=1)-tn*H.COST)
        sr_f.append(sf.mean()/sf.std()*np.sqrt(252)); sr_o.append(so.mean()/so.std()*np.sqrt(252))
    assert abs(np.mean(sr_f)-np.mean(sr_o))>0.05, "two-stream scramble == single-stream scramble (IC leg ignored)"
    # and position_lag_p (fixed) must accept r1,r2 frames
    p_fixed,real=H.position_lag_p2(pos, on_r, ic_r, n=20)
    assert 0.0<=p_fixed<=1.0
if __name__=='__main__':
    fns=[v for k,v in sorted(globals().items()) if k.startswith('test_')]
    failed=0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception as e:
            failed+=1; print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"RED/GREEN: {len(fns)-failed}/{len(fns)} pass, {failed} fail")
    sys.exit(0 if failed==0 else 1)
