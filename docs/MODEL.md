# Python model specification

## Spatial inputs and domain

The six rasters in `data/tfcg_case_data_v0.2.0.zip` share a 557 × 696 grid in EPSG:32737 at 25 m cell size. One cell is 0.0625 ha. The reserve is the valid footprint of `TempRaster/foresst_reserve_c.tif`. The reporting domain is the intersection of that reserve with valid cells in `InRaster/cosecha24.tif`: 4,214 cells or 263.375 ha. The reserve contains 52,789 cells or 3,299.3125 ha. The reporting domain begins with 17,420.8125 Mg of mapped biomass. The larger valid calendar footprint includes 70 cells outside the reserve and must not be used as the reporting area.

The calendar is adjusted by adding a binary indicator for valid cells in `TempRaster/charcoalharvB_c.tif`. Stored plot identifiers are not used as numeric increments. Zero or one calendar values are unscheduled. The adjusted first-rotation calendar schedules 3,548 reporting cells, or 221.75 ha. Water and slope rules leave 178.6875, 118.25 and 221.75 ha statically eligible under reference, conservative and intensive rules, respectively; an annual biomass threshold can further reduce harvest.

`TempRaster/DEM_c.tif` supplies elevation in metres. Slope is the maximum absolute gradient to the eight adjacent cells, converted to degrees. `TempRaster/rivers_c.tif` supplies valid water cells; Euclidean distance to them is rounded down to integer metres before comparing it with the buffer. The 25 m grid is computational and does not establish the original observational resolution. Source acquisition and raster preparation remain to be documented by the authors.

## Annual update

The six configurations in `config/main_1000.json` simulate 2015–2086 in three 24-year rotations. Each year a cell is harvested only when its calendar year matches the year within that rotation, its water distance meets the buffer, its slope is at most the ceiling, and its pre-harvest biomass meets the minimum threshold. Equality is allowed at the thresholds. A cell below the biomass threshold waits until its next scheduled rotation.

Let B be pre-harvest biomass in Mg per cell and ρ the retained proportion. In an eligible cell, wood harvest is `(1−ρ)B` and post-harvest stock is `ρB`; otherwise harvest is zero and stock remains B. The model divides biomass density and carrying biomass K by 16 to express both in Mg per 25 m cell. Annual growth is then applied to the post-harvest stock b using k = K/16:

```
0 < b < k:     B_next = k*b / (q*k + (1−q)*b)
b = 0 or b≥k: B_next = b
```

This is the one-year state update derived from the logistic biomass–age relation `b(a)=k/(1+c q^a)` with `0<q<1`; c cancels from the update. Smaller q implies faster growth. Zero biomass does not recruit, and stock above the sampled k is neither grown nor forcibly reduced. These boundary conditions require ecological evaluation. The model does not explicitly represent species, coppice, fire, grazing or stand structure.

Post-growth stock is summed over the reporting domain. Annual potential charcoal is wood harvest multiplied by the sampled kiln mass yield. There is no moisture conversion or feedstock-loss factor in the computation; consistent biomass and kiln-yield mass bases remain an author query.

## Sampling and outputs

Each scenario has 1,000 realizations. K and q are drawn once per realization, shared by all cells and years; kiln yield is drawn independently each year. Independent NumPy PCG64 child streams use seed 20260917. Normal draws are rejected unless K>0, 0<q<1 and 0<yield<100%. Configured means and SDs describe normals before rejection. In the intensive scenario the accepted q mean is approximately 0.904, below its nominal 0.95. Initial-map uncertainty and correlations are not sampled.

Three combined scenarios vary both harvest rules and biological/kiln assumptions. Two management-only scenarios vary harvest rules while reusing the reference parameter draws. A no-harvest control retains all stock under reference biology. This paired structure isolates management-rule effects within the model.

`results.npz` stores yearly post-growth standing biomass, harvested wood and potential charcoal, plus diagnostics and every parameter draw. Stocks are in Mg; the other quantities are annual Mg flows. Rotation summaries average each realization's 24 yearly values and then summarize across realizations. The 2.5th and 97.5th percentiles are conditional simulation ranges, not confidence intervals for measured production. Raster inputs, configurations, source code, unit tests, numerical results and figure scripts support computational reproduction from the analytical rasters. Independent field validation and upstream raster reconstruction remain outside this release.
