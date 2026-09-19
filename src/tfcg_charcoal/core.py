"""Annual spatial biomass, harvest and charcoal simulation in Python."""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Parameters:
    name: str = "reference"
    k_mean: float = 90
    k_sd: float = 9
    q_mean: float = .82
    q_sd: float = .082
    yield_mean_pct: float = 19.4
    yield_sd_pct: float = 4.52
    water_buffer_m: float = 50
    max_slope_deg: float = 15
    min_biomass_mg_ha: float = 1
    retained_pct: float = 10
    start_year: int = 2015
    rotation_years: int = 24
    rotations: int = 3
    realizations: int = 1000

def annual_growth(stock, k_cell, q):
    """One-year logistic state update; zero and above-K stock remain unchanged."""
    if not np.isfinite(k_cell) or k_cell<=0 or not np.isfinite(q) or not 0<q<1:
        raise ValueError('Growth requires K > 0 and 0 < q < 1.')
    b=np.asarray(stock,dtype=np.float64)
    if np.any(b[np.isfinite(b)]<0):raise ValueError('Negative biomass.')
    result=b.copy();m=(b>0)&(b<k_cell)
    result[m]=k_cell*b[m]/(q*k_cell+(1-q)*b[m])
    return result.astype(np.float32)

def parameter_draws(p, seed):
    """Independent PCG64 streams and rejection at physically admissible bounds."""
    if any(not isinstance(x,int) or isinstance(x,bool) for x in (p.realizations,p.rotations,p.rotation_years,p.start_year)):
        raise ValueError('Years, rotations and realizations must be integers.')
    if p.realizations<1 or p.rotations<1 or p.rotation_years<1:
        raise ValueError('Realizations, rotations and rotation years must be positive.')
    if not all(np.isfinite(x) for x in [p.k_mean,p.k_sd,p.q_mean,p.q_sd,p.yield_mean_pct,p.yield_sd_pct]):
        raise ValueError('Distribution parameters must be finite.')
    if not (p.k_mean > 0 and 0 < p.q_mean < 1 and 0 < p.yield_mean_pct < 100):
        raise ValueError('Distribution means must lie in their physical domains.')
    if min(p.k_sd,p.q_sd,p.yield_sd_pct) < 0:
        raise ValueError('Distribution standard deviations cannot be negative.')
    if not all(np.isfinite(x) for x in (p.water_buffer_m,p.max_slope_deg,p.min_biomass_mg_ha,p.retained_pct)):
        raise ValueError('Harvest rules must be finite.')
    if not (p.water_buffer_m>=0 and 0<=p.max_slope_deg<=90 and p.min_biomass_mg_ha>=0 and 0<=p.retained_pct<=100):
        raise ValueError('Harvest rules are outside their admissible domains.')
    streams=np.random.SeedSequence(seed).spawn(3)
    rngs=[np.random.Generator(np.random.PCG64(s)) for s in streams]
    n=p.realizations;ny=p.rotation_years*p.rotations
    def bounded_normal(rng,mu,sd,shape,low,high):
        if sd<0:raise ValueError('Negative standard deviation')
        if sd==0:
            if not low<mu<high:raise ValueError('Constant outside admissible domain')
            return np.full(shape,mu,dtype=float)
        x=rng.normal(mu,sd,shape)
        bad=~np.isfinite(x)|(x<=low)|(x>=high)
        while bad.any():
            x[bad]=rng.normal(mu,sd,int(bad.sum()));bad=~np.isfinite(x)|(x<=low)|(x>=high)
        return x
    return {'k_ha':bounded_normal(rngs[0],p.k_mean,p.k_sd,n,0,np.inf),
            'q':bounded_normal(rngs[1],p.q_mean,p.q_sd,n,0,1),
            'yield_pct':bounded_normal(rngs[2],p.yield_mean_pct,p.yield_sd_pct,(n,ny),0,100)}

def simulate(initial, reporting_mask, scheduled_year, eligible, p, draws, capture=None, compact=True, cell_area_ha=.0625):
    """Return post-harvest/post-growth stock, wood harvest and charcoal by year."""
    if np.asarray(initial).ndim!=1:raise ValueError('Supply flat reserve-cell vectors.')
    if not 0<=p.retained_pct<=100 or p.min_biomass_mg_ha<0:raise ValueError('Invalid harvest rule.')
    if not np.isfinite(cell_area_ha) or cell_area_ha <= 0:raise ValueError('Cell area must be positive.')
    ny=p.rotation_years*p.rotations;n=p.realizations
    totals=np.empty((n,ny,3));diagnostics=np.empty((n,ny,3))
    initial=np.asarray(initial,dtype=np.float32)
    if compact:
        # Identical, never-harvested background cells have identical trajectories.
        extra=~reporting_mask
        if np.any(extra & eligible & (scheduled_year>=p.start_year)):
            raise ValueError('Cannot compact harvestable cells outside reporting FMU.')
        representative=np.unique(initial[extra])
        nreport=int(reporting_mask.sum())
        initial=np.concatenate([initial[reporting_mask],representative])
        scheduled_year=np.concatenate([scheduled_year[reporting_mask],np.zeros(len(representative),dtype=np.int16)])
        eligible=np.concatenate([eligible[reporting_mask],np.zeros(len(representative),dtype=bool)])
        reporting_mask=np.arange(len(initial))<nreport
    threshold_mg_cell=p.min_biomass_mg_ha*cell_area_ha
    for j in range(n):
        stock=initial.copy();k=draws['k_ha'][j]*cell_area_ha;q=draws['q'][j]
        for t in range(ny):
            year=p.start_year+t
            schedule=scheduled_year+(t//p.rotation_years)*p.rotation_years
            harvestable=eligible&(scheduled_year>=p.start_year)&(schedule==year)&(stock>=threshold_mg_cell)
            b=stock.astype(np.float64)
            h=np.where(harvestable,b-b*p.retained_pct/100,0).astype(np.float32)
            post=np.where(harvestable,b*p.retained_pct/100,b).astype(np.float32)
            stock=annual_growth(post,k,q)
            totals[j,t]=[np.nansum(stock[reporting_mask],dtype=np.float64),np.sum(h,dtype=np.float64),np.sum(h,dtype=np.float64)*draws['yield_pct'][j,t]/100]
            diagnostics[j,t]=[np.count_nonzero(~np.isfinite(stock[reporting_mask])),np.count_nonzero(stock[reporting_mask]<0),np.nansum((stock-post)[reporting_mask],dtype=np.float64)]
            if capture is not None:capture(j,t,stock,post,h)
    return totals,diagnostics
