# Model audit and manuscript query resolutions

Audit date: 17 September 2026. Results refer to the newly supplied model and calendar, not an inferred historical ensemble. Native and Python validation evidence is in `results/reference/`; larger native traces are in the results release archive.

## Findings with direct consequences for reruns

1. The supplied two-realization, 48-year deterministic configuration reproduces the archived baseline exactly in DINAMICA. It is not the manuscript's three-scenario, 100-realization configuration. Preserve that distinction and replace the unverified manuscript table with explicitly new results.
2. The inverse growth expression fixes q = 0.82 while the forward expression samples q. The above-K branch depends on the reserve-wide maximum. The corrected state update and its boundary assumptions were rerun as separate experiments; matched bounded draws isolate their effects.
3. The intensive unbounded q distribution yields inadmissible values: 32 of 100 diagnostic draws were at least one; three annual yields were invalid. Bounded rejection was rerun, and its altered distribution moments are exported. The intensive accepted mean q is about 0.904 in the 1,000-run suite. A future empirical reparameterization must be rerun rather than substituted only in prose.
4. Management contrasts also change biology and kiln efficiency in the historical scenarios. New paired management-only experiments keep those draws common. Conservative rules then increase mean stock but reduce mean charcoal relative to reference rules; 10.9% of sampled realizations nevertheless have more third-rotation conservative charcoal.
5. New no-harvest runs provide an internal recovery control. They are not a no-programme counterfactual.
6. Initial-stock uncertainty is off. Future uncertainty in the initial map, fitted bounded growth distributions, measured kiln mass conversions or altered scheduling would require new code/configuration, explicit evidence and reruns. No unexecuted improvement is presented as a result.

## Query map from the earlier manuscript

| Query | Status from executable evidence | Remaining author input |
| --- | --- | --- |
| Q01 | Author order retained | Affiliations, names, ORCIDs, correspondence |
| Q02 | Resolved: harvest and charcoal are annual flows; rotation means average years and realizations | None for new results; old aggregation cannot be reconstructed without its ensemble |
| Q03 | Reporting mask 267.75 ha; scheduled area 221.75 ha; reserve 3,299.3125 ha | Reconcile historical map/plan boundaries and dates |
| Q04 | Implemented thresholds and retention identified | Prescribed versus assumed rules; current practice; intended one-year calendar shift |
| Q05 | CRS, resolution, numerical units, NoData and hashes documented | Original data acquisition/preprocessing and physical biomass basis |
| Q06 | Not inferable from software | Participatory methods and applicable permissions |
| Q07 | Resolved: equality allowed; low stock waits until next rotation; cell-scale exclusion | Confirm operational relevance under Q04 |
| Q08 | Exact original equations and order recovered; revised growth tested | Biological acceptance of corrected boundary conditions and evaluation |
| Q09 | Resolved computationally: charcoal = harvest × yield; no moisture factor | Empirical yields, feedstock/moisture bases, sample sizes |
| Q10 | Supplied settings and new scenarios exported; old table not reproduced | Historical ensemble/configuration, rationale for scenario K and q |
| Q11 | Frequencies and distributions recovered; invalid draws diagnosed; new seed/draws exported | Historical seed/ensemble and empirical priors |
| Q12 | Initial pre-harvest stock 17,420.8125 Mg; output is post-harvest/post-growth | Provenance of conflicting old first-year values |
| Q13 | Software verification complete; no field validation claimed | Independent plot data and harvest histories |
| Q14 | Quantitative scenario contrasts and annual outputs now available | Current decision, target, actual harvest records and site status |
| Q15–17 | Not inferable from software | Funding, contributions, competing interests |
| Q18 | Code, inputs, outputs, tests, figures and release metadata prepared; licences selected | Public records, version DOIs and upstream attribution |

## Scope of numerical evidence

All 1,819 initially inventoried source files are unchanged. The author later supplied `InRaster/cosecha24.tif`; it remains in the original folder and is checksummed separately. It matches the earlier diagnostic reconstruction in grid, mask and values, so the final analysis uses the supplied raster directly. `plost24anios.tif` is not silently used as its replacement.

The 100-run audit and 1,000-run corrected suites answer implementation and scenario questions. They are not evidence that the inherited priors are accurate. The intensive third-rotation charcoal Monte Carlo SE is about 6.6% of its 1,000-run mean. Quantile ranges and paired differences are preserved rather than reporting only rounded averages. No formal convergence claim is made.

## Observed verification environment

Windows x86-64; CPython 3.12.14; NumPy 2.5.3, Pandas 3.0.1, Rasterio 1.5.1, SciPy 1.18.1, Matplotlib 3.11.2. The complete dependency versions are in `requirements-lock.txt`. DINAMICA EGO 8.3.0.20250117, one processor, predefined native seed, no parallel steps. The native software is not redistributed. GitHub Actions run 35298026545 passed on Windows and Linux: nine tests, baseline reproduction, an eight-realization audit and figure generation. Full native and 1,000-realization experiments were verified locally on Windows.
