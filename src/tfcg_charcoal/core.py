"""Explicit legacy equations and separately identified corrected experiments.

Legacy is a transcription of supplied.egoml, not a recommended growth model.
Cell states are float32 as in DINAMICA. Calculations use float64 before storage.
"""
from dataclasses import dataclass, asdict
import numpy as np

@dataclass(frozen=True)
class Parameters:
    name: str = "supplied"
    k_mean: float = 86
    k_sd: float = 0
    q_mean: float = .82
    q_sd: float = 0
    yield_mean_pct: float = 20
    yield_sd_pct: float = 0
    water_buffer_m: float = 50
    max_slope_deg: float = 15
    min_biomass_mg_cell: float = 1
    retained_pct: float = 10
    start_year: int = 2015
    rotation_years: int = 24
    rotations: int = 2
    realizations: int = 2

SCENARIOS = {
    "supplied": Parameters(),
    "reference": Parameters(name="reference",k_mean=90,k_sd=9,q_mean=.82,q_sd=.082,yield_mean_pct=19.4,yield_sd_pct=4.52,rotations=3,realizations=100),
    "conservative": Parameters(name="conservative",k_mean=100,k_sd=10,q_mean=.75,q_sd=.075,yield_mean_pct=23,yield_sd_pct=2.66,water_buffer_m=100,max_slope_deg=10,min_biomass_mg_cell=3,retained_pct=20,rotations=3,realizations=100),
    "intensive": Parameters(name="intensive",k_mean=80,k_sd=8,q_mean=.95,q_sd=.095,yield_mean_pct=18.2,yield_sd_pct=5.18,water_buffer_m=0,max_slope_deg=90,min_biomass_mg_cell=0,retained_pct=1,rotations=3,realizations=100),
}

def legacy_growth(stock, k_cell, q):
    """Exact supplied expressions v91 (age) and v90 (growth), including defects."""
    b=np.asarray(stock,dtype=np.float64)
    maximum=np.nanmax(b)
    c=np.exp(3.35898553285285)
    with np.errstate(all='ignore'):
        age=np.where(b>=k_cell,np.log((maximum+.1/b-1)/c)/np.log(.82),np.log((k_cell/b-1)/c)/np.log(.82)).astype(np.float32)
        denom=1+c*np.power(q,age.astype(np.float64)+1)
        result=np.where(b>=k_cell,maximum+.1/denom,k_cell/denom).astype(np.float32)
    # DINAMICA uses its null sentinel for nonfinite/out-of-range map results.
    result[~np.isfinite(result)]=np.nan
    return result

def corrected_growth(stock, k_cell, q):
    """One-year logistic state update, with an explicit no-decline rule above K.

    This is a proposed revision, not the supplied implementation. Zero stock
    remains zero: no undocumented recruitment floor is introduced.
    """
    if not np.isfinite(k_cell) or k_cell<=0 or not np.isfinite(q) or not 0<q<1:
        raise ValueError('Corrected growth requires K > 0 and 0 < q < 1.')
    b=np.asarray(stock,dtype=np.float64)
    if np.any(b[np.isfinite(b)]<0):raise ValueError('Negative biomass.')
    result=b.copy();m=(b>0)&(b<k_cell)
    result[m]=k_cell*b[m]/(q*k_cell+(1-q)*b[m])
    return result.astype(np.float32)

def parameter_draws(p, seed, bounded=False):
    """Independent PCG64 streams; draws are exported, never represented as old seeds."""
    if p.realizations<1 or p.rotations<1 or p.rotation_years<1:
        raise ValueError('Realizations, rotations and rotation years must be positive.')
    if not all(np.isfinite(x) for x in [p.k_mean,p.k_sd,p.q_mean,p.q_sd,p.yield_mean_pct,p.yield_sd_pct]):
        raise ValueError('Distribution parameters must be finite.')
    streams=np.random.SeedSequence(seed).spawn(3)
    rngs=[np.random.Generator(np.random.PCG64(s)) for s in streams]
    n=p.realizations;ny=p.rotation_years*p.rotations
    def normal(rng,mu,sd,shape,low=-np.inf,high=np.inf):
        if sd<0:raise ValueError('Negative standard deviation')
        if sd==0:
            if bounded and not low<mu<high:raise ValueError('Constant outside admissible domain')
            return np.full(shape,mu,dtype=float)
        x=rng.normal(mu,sd,shape)
        if bounded:
            bad=(x<=low)|(x>=high)
            while bad.any():
                x[bad]=rng.normal(mu,sd,int(bad.sum()));bad=(x<=low)|(x>=high)
        return x
    return {'k_ha':normal(rngs[0],p.k_mean,p.k_sd,n,0,np.inf),
            'q':normal(rngs[1],p.q_mean,p.q_sd,n,0,1),
            'yield_pct':normal(rngs[2],p.yield_mean_pct,p.yield_sd_pct,(n,ny),0,100)}

def simulate(initial, reporting_mask, scheduled_year, eligible, p, draws, mode='legacy', capture=None, compact=True):
    """Simulate each realization. Stocks reported AFTER harvest and growth.

    Arrays cover the reserve, including non-FMU cells needed to reproduce the
    legacy global-maximum branch. Initial-stock Monte Carlo is deliberately off,
    matching the supplied configuration. Calendar uses 24-year recurrences.
    """
    if p.rotation_years!=24 and mode=='legacy':raise ValueError('Legacy schedule fixes 24-year shifts.')
    if mode=='legacy' and p.rotations>7:raise ValueError('Legacy recurrence is verified only through seven 24-year rotations; supplied eighth shift is irregular.')
    if mode not in ['legacy','corrected']:raise ValueError(mode)
    if np.asarray(initial).ndim!=1:raise ValueError('Supply flat reserve-cell vectors.')
    if not 0<=p.retained_pct<=100 or p.min_biomass_mg_cell<0:raise ValueError('Invalid harvest rule.')
    growth=legacy_growth if mode=='legacy' else corrected_growth
    ny=p.rotation_years*p.rotations;n=p.realizations
    totals=np.empty((n,ny,3));diagnostics=np.empty((n,ny,3))
    initial=np.asarray(initial,dtype=np.float32)
    if compact:
        # Outside the reporting FMU, cells are never harvested and enter the
        # legacy calculation only through the maximum. Equal initial values
        # therefore remain equal. Retaining one of each preserves that maximum
        # exactly while avoiding repeated identical cell calculations.
        extra=~reporting_mask
        if np.any(extra & eligible & (scheduled_year>=p.start_year)):
            raise ValueError('Cannot compact harvestable cells outside reporting FMU.')
        representative=np.unique(initial[extra])
        nreport=int(reporting_mask.sum())
        initial=np.concatenate([initial[reporting_mask],representative])
        scheduled_year=np.concatenate([scheduled_year[reporting_mask],np.zeros(len(representative),dtype=np.int16)])
        eligible=np.concatenate([eligible[reporting_mask],np.zeros(len(representative),dtype=bool)])
        reporting_mask=np.arange(len(initial))<nreport
    for j in range(n):
        stock=initial.copy();k=draws['k_ha'][j]/16;q=draws['q'][j]
        for t in range(ny):
            year=p.start_year+t
            schedule=scheduled_year+(t//p.rotation_years)*p.rotation_years
            # Zero-valued unscheduled/excluded cells cannot become harvestable.
            harvestable=eligible&(scheduled_year>=p.start_year)&(schedule==year)&(stock>=p.min_biomass_mg_cell)
            b=stock.astype(np.float64)
            h=np.where(harvestable,b-b*p.retained_pct/100,0).astype(np.float32)
            post=np.where(harvestable,b*p.retained_pct/100,b).astype(np.float32)
            stock=growth(post,k,q)
            totals[j,t]=[np.nansum(stock[reporting_mask],dtype=np.float64),np.sum(h,dtype=np.float64),np.sum(h,dtype=np.float64)*draws['yield_pct'][j,t]/100]
            diagnostics[j,t]=[np.count_nonzero(~np.isfinite(stock[reporting_mask])),np.count_nonzero(stock[reporting_mask]<0),np.nansum((stock-post)[reporting_mask],dtype=np.float64)]
            if capture is not None:capture(j,t,stock,post,h)
    return totals,diagnostics
