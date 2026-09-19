from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
from tfcg_charcoal.core import Parameters,annual_growth,parameter_draws,simulate
from tfcg_charcoal.landscape import INPUT_FILES,prepare,slope_degrees

def test_growth_matches_frost_equivalent_age_below_K():
    k=5.625;q=.75;c=np.exp(3.35898553285285)
    age=np.array([1,5,15,30],dtype=float)
    b=(k/(1+c*q**age)).astype(np.float32)
    age_from_b=np.log((k/b.astype(float)-1)/c)/np.log(q)
    expected=k/(1+c*q**(age_from_b+1))
    np.testing.assert_allclose(annual_growth(b,k,q),expected,rtol=1e-7)

def test_growth_domain_and_upper_stock_rule():
    b=np.array([0,.1,1,4.9,5,6,7],dtype=np.float32)
    out=annual_growth(b,5,.82)
    assert out[0]==0
    assert np.all(out[1:4]>b[1:4]) and np.all(out[1:4]<5)
    np.testing.assert_array_equal(out[4:],b[4:])
    for q in [-.1,0,1,1.1,np.nan]:
        with pytest.raises(ValueError):annual_growth(b,5,q)

def test_skipped_cell_waits_until_next_rotation_and_mass_balance():
    p=replace(Parameters(),realizations=1,rotations=2,k_mean=80)
    captured=[]
    totals,diag=simulate(np.array([.03],np.float32),np.array([True]),np.array([2015]),np.array([True]),p,parameter_draws(p,7),capture=lambda j,t,b,post,h:captured.append((b.copy(),post.copy(),h.copy())),compact=False)
    assert totals[0,:24,1].sum()==0
    assert totals[0,24,1]>0
    before=np.array([.03],np.float32)
    for after,post,harvest in captured:
        np.testing.assert_allclose(post+harvest,before,rtol=1e-7,atol=1e-7)
        assert np.all(after>=post)
        before=after
    assert np.all(totals[:,:,2]<=totals[:,:,1])
    assert not diag[:,:,:2].any()

def test_threshold_equality_and_exclusion():
    p=replace(Parameters(),realizations=1,rotations=1,yield_mean_pct=20,yield_sd_pct=0)
    r,d=simulate(np.array([.0625,.0625],np.float32),np.array([True,True]),np.array([2015,2015]),np.array([True,False]),p,parameter_draws(p,7))
    assert r[0,0,1]==pytest.approx(.05625,abs=1e-7)
    assert r[0,0,2]==pytest.approx(.01125,abs=1e-7)

def test_harvest_threshold_is_a_density_not_a_fixed_cell_mass():
    p=replace(Parameters(),realizations=1,rotations=1,rotation_years=1,k_sd=0,q_sd=0,yield_sd_pct=0)
    draws=parameter_draws(p,7)
    inputs=(np.array([.08],np.float32),np.array([True]),np.array([2015]),np.array([True]),p,draws)
    small,_=simulate(*inputs,cell_area_ha=.0625)
    large,_=simulate(*inputs,cell_area_ha=.1)
    assert small[0,0,1]==pytest.approx(.072,abs=1e-7)
    assert large[0,0,1]==0

def test_compaction_preserves_simulation():
    p=replace(Parameters(),realizations=4,k_mean=80,k_sd=8,q_sd=.082)
    b=np.array([3,4,1,1,2,7,7,7],np.float32);mask=np.array([1,1,0,0,0,0,0,0],bool)
    years=np.array([2015,2020,0,0,0,0,0,0]);eligible=np.ones(8,bool)
    draws=parameter_draws(p,10)
    a,da=simulate(b,mask,years,eligible,p,draws,compact=True)
    z,dz=simulate(b,mask,years,eligible,p,draws,compact=False)
    np.testing.assert_array_equal(a,z);np.testing.assert_array_equal(da,dz)

def test_draws_are_reproducible_and_bounded():
    p=replace(Parameters(),realizations=100,q_mean=.95,q_sd=.095,yield_sd_pct=8,k_sd=9)
    a=parameter_draws(p,8);b=parameter_draws(p,8)
    for key in a:np.testing.assert_array_equal(a[key],b[key])
    assert np.all((a['q']>0)&(a['q']<1))
    assert np.all(a['k_ha']>0)
    assert np.all((a['yield_pct']>0)&(a['yield_pct']<100))

def test_slope_uses_steepest_eight_neighbour_gradient():
    flat=np.zeros((3,3));flat[1,2]=25
    assert slope_degrees(flat)[1,1]==pytest.approx(45)
    assert slope_degrees(np.zeros((3,3)))[1,1]==0

def test_invalid_ensemble_configuration_is_rejected():
    for p in [replace(Parameters(),realizations=0),replace(Parameters(),rotations=0),replace(Parameters(),q_mean=np.nan),replace(Parameters(),q_mean=1.2),replace(Parameters(),water_buffer_m=-1)]:
        with pytest.raises(ValueError):parameter_draws(p,1)


def test_five_inputs_and_supplied_calendar_are_loaded():
    source=Path(__file__).resolve().parents[1]/'data'
    assert len(INPUT_FILES)==5
    land,metadata=prepare(source)
    assert metadata['reporting_cells']==4214
    assert metadata['initial_reporting_biomass_mg']==pytest.approx(17420.8125)
    assert int(np.count_nonzero(land['scheduled_year']>=2015))==3548
    import rasterio
    with rasterio.open(source/INPUT_FILES['calendar']) as ds:
        calendar=ds.read(1,masked=True).filled(0)
    np.testing.assert_array_equal(land['scheduled_year'],calendar[land['reserve_mask']])


def test_growth_uses_supplied_cell_area():
    p=replace(Parameters(),realizations=1,rotations=1,rotation_years=1,k_sd=0,q_sd=0,yield_sd_pct=0)
    draws=parameter_draws(p,7)
    args=(np.array([1],np.float32),np.array([True]),np.array([0]),np.array([True]),p,draws)
    small,_=simulate(*args,cell_area_ha=.0625)
    large,_=simulate(*args,cell_area_ha=.1)
    assert small[0,0,0]!=large[0,0,0]
