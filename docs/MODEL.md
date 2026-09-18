# Model specification and revisions

## Domain and units

All used rasters have 557 rows × 696 columns, 25 m cells, and EPSG:32737 (UTM 37S). One cell is 0.0625 ha. The native code divides initial biomass density and K by 16 to obtain Mg/cell. The reporting mask is the non-null calendar footprint: 4,284 cells, 267.75 ha, including 736 zero-calendar cells. Initial reported biomass is 17,420.8125 Mg. The surrounding reserve has 52,789 cells, 3,299.3125 ha; its maximum biomass influences the original growth expression but its biomass is not included in FMU totals.

The effective calendar equals `cosecha24.tif` plus the binary presence of `charcoalharvB_c.tif`. This shifts some harvest dates by one year. Zero/one values remain unscheduled. Scheduled area is 221.75 ha. Static eligibility leaves 178.6875, 118.25 and 221.75 ha for reference, conservative and intensive rules before applying the changing biomass threshold. Reporting area is therefore not interchangeable with harvestable area or the older manuscript's 263 ha.

The 50 × 50 m management plots described in the historical plan differ from the model's 25 m computational cells. This grid adds no observational resolution to the source biomass data. Original acquisition and resampling provenance remain unresolved.

## One annual step

1. Select cells whose effective calendar year equals the current year, repeating every 24 years. A scheduled cell below the biomass threshold waits until the next rotation; it is neither deferred within the rotation nor replaced.
2. Exclude distance **less than** the water buffer and slope **greater than** the ceiling. Threshold equality is allowed. Slope is the steepest absolute gradient to the eight neighbours in degrees. Distance is Euclidean distance rounded down to integer metres. Native and Python exclusion masks agree for all tested scenario thresholds.
3. Harvest `H = (1 − retained_pct/100) B` in eligible cells with `B >= minimum`. Store retained biomass in float32.
4. Apply the chosen growth equation to post-harvest biomass. Report the sum of post-growth FMU stock.
5. Report wood harvest and `charcoal = harvest × yield_pct/100`. No green-to-dry factor or feedstock-loss factor is used.

The [DINAMICA slope specification](https://dinamicaego.com/dokuwiki/doku.php?id=calc_slope_map) and [map-calculation documentation](https://www.csr.ufmg.br/dokuwiki/doku.php?id=calculate_map) inform the equivalent preprocessing and storage semantics. The checked native outputs remain the numerical reference.

## Original growth equations

Let b be post-harvest Mg/cell, k = K/16, c = exp(3.35898553285285), and M the maximum b over the reserve. The delivered v91 age expression is:

```
b < k:  a = log((k/b − 1)/c) / log(0.82)
b >= k: a = log((M + 0.1/b − 1)/c) / log(0.82)
```

Age is stored in float32. The delivered v90 growth expression then uses the sampled q:

```
b < k:  next = k / (1 + c*q**(a+1))
b >= k: next = M + 0.1 / (1 + c*q**(a+1))
```

This transcription preserves the actual parentheses. The inverse fixes 0.82 while the forward equation uses q. It can therefore decrease biomass without disturbance when q differs from 0.82. The above-k branch can raise a cell to another cell's maximum; it is not an independent logistic update. Neither defect is silently repaired in `legacy` mode. Float32 intermediate states and float64 arithmetic reproduce the tested native totals.

## Corrected experiment

For `0 < b < k`, use `next = k*b / (q*k + (1−q)*b)`. This follows by advancing the same logistic curve one year using the same q in the inverse and forward equations. Zero remains zero. Cells at or above k retain their current biomass. This last rule explicitly assumes neither additional growth nor forced mortality above K; it is a proposed boundary condition requiring ecological review. The constant c cancels in this state update.

The corrected update requires K > 0 and 0 < q < 1. Smaller q gives faster recovery. q is dimensionless, not the continuous intrinsic growth rate. A continuous logistic parameter would be −ln(q) per year. The model treats current aggregate biomass as sufficient to determine recovery; it does not explicitly represent coppice, stand structure, species or disturbance.

## Sampling and experiment families

K and q are drawn once per realization, common to the landscape; kiln yield is drawn independently each year and is common to that year's harvest. The supplied baseline has zero SD for all three and two identical realizations. Its separate initial-biomass Monte Carlo flag is off. Python intentionally reproduces that setting; the optional initial-map perturbation branch is not ported.

The audit has three families: original equations with unbounded normals; original equations with bounded normals; corrected equations with bounded normals. Matched bounded experiments share exactly the same parameter arrays, isolating growth changes. The corrected management-only family additionally uses reference K, q and yield draws for every rule set. The no-harvest control retains 100% of biomass under reference biological draws.

Bounded normals use rejection sampling with K > 0, 0 < q < 1 and 0 < yield < 100%. Table parameters are the *pre-truncation* means and SDs, not the accepted distribution moments. Independence, spatial homogeneity and these priors are assumptions, not estimated relationships. The exported draws and sampled-distribution summaries make them inspectable.

PCG64 uses seed 20260917 and independent SeedSequence child streams for K, q and yield. Bulk rejection sampling means a 100-realization run is not necessarily the first 100 entries of a 1,000-realization run. Exact repeatability is tested for the same configuration; Monte Carlo standard errors describe simulation precision, not measurement uncertainty.

## Output definitions

`totals[n, year, quantity]` stores post-growth standing biomass, annual harvested wood and potential charcoal, all in Mg. `diagnostics` stores missing reporting cells, negative reporting cells and annual net growth. Rotation stock means average 24 post-growth stocks. Rotation flow means average 24 annual flows; their sum is the rotation total. Ensemble quantiles refer to realization-level rotation means or to annual ensembles as labelled. They are conditional model intervals, not confidence intervals for observed programme outcomes.

The current recurrence supports this fixed 24-year historical calendar. A longer-rotation test must explicitly regenerate/reallocate the calendar; changing a number without reconsidering scheduled areas is not a defensible sensitivity test. The supplied native eighth-rotation shift is irregular; Python legacy execution rejects more than seven rotations rather than implying general equivalence. All reported new experiments use three rotations.
