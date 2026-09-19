# Ulaya Mbuyuni charcoal planning model

This free Python model estimates standing woodland biomass, annual wood harvest and potential charcoal production under mapped community-forest harvesting rules. The Ulaya Mbuyuni case study uses five aligned analytical rasters and compares reference, conservative and intensive scenarios. Each scenario has 1,000 realizations over three 24-year rotations (2015–2086). These are conditional simulations, not measured production or an operational forecast.

Release **v0.3.0** is archived at [Zenodo](https://doi.org/10.5281/zenodo.22847506). The archive contains the tagged source, five analytical rasters, complete 1,000-realization outputs, regenerated figures and SHA-256 checksums. The corresponding source tag is [v0.3.0 on GitHub](https://github.com/adrianghilardi/tfcg-charcoal-model/releases/tag/v0.3.0). The version-independent Zenodo concept DOI is [10.5281/zenodo.22822182](https://doi.org/10.5281/zenodo.22822182).

## Run locally

Use Python 3.12. From the repository root:

```shell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-lock.txt
.venv/Scripts/python -m pip install --no-deps -e .
.venv/Scripts/python -m pytest -q
.venv/Scripts/python scripts/verify_inputs.py
.venv/Scripts/python scripts/run_experiments.py --output runs/main_1000
.venv/Scripts/python scripts/summarize_results.py --main runs/main_1000 --output runs/figures
.venv/Scripts/python scripts/plot_inputs.py --output runs/figures
.venv/Scripts/python scripts/plot_workflow.py --output runs/figures
.venv/Scripts/python scripts/verify_reference_results.py --run runs/main_1000
```

On Linux/macOS, replace `.venv/Scripts/python` with `.venv/bin/python`. A quick check can add `--realizations 8` to `run_experiments.py`, using a *different* empty output directory. The full run writes realization-level results, draws, annual and rotation summaries, input hashes, software versions and an output manifest. The final command checks the complete output against the hashes archived for the locked Windows reference environment. The run driver refuses a nonempty output directory and never changes the input TIFFs. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the computational boundary and verification details.

To try new parameter values, copy `config/main_1000.json`, edit the scenario values, and pass `--config PATH --output NEW_DIRECTORY`. The configuration controls K, q, kiln yield, water buffer, maximum slope, minimum harvestable biomass density (Mg/ha), retained fraction, start year, rotation length, rotations and realizations. Unknown configuration keys are rejected. Use the same time horizon across scenarios when creating a shared figure with `summarize_results.py`. A seed can be supplied with `--seed`.

The three scenarios use the author-supplied parameter values, transcribed in [the model specification](docs/MODEL.md).

## Input rasters

All five rasters are in `data/InRaster` and listed with SHA-256 hashes in `data/bundle_manifest.json`. The harvest-year values are used as supplied.

| Raster | Role in the calculation |
| --- | --- |
| `agb_airdriedMg_ha.tif` | Initial air-dried aboveground biomass density (Mg/ha). |
| `forest_reserve.tif` | Valid-cell footprint of the reserve. |
| `harvest_calendar_year.tif` | Scheduled harvest year; zero is unscheduled. |
| `dtem.tif` | Elevation used to derive slope. |
| `rivers.tif` | Water-feature cells used to derive distance and buffers. |

The current rasters define 4,214 reporting cells, approximately 263 ha. Input acquisition, upstream processing, the basis of K and kiln yields, and independent field validation remain under coauthor review. The Python package reproduces calculations **from these analytical rasters**; it does not reconstruct their upstream creation. See [the model specification](docs/MODEL.md) for equations and numerical conventions.

## Citation and licences

Cite the exact archived version using [CITATION.cff](CITATION.cff) or Zenodo DOI [10.5281/zenodo.22847506](https://doi.org/10.5281/zenodo.22847506). Code is licensed under MIT. The supplied case-study rasters, numerical outputs and figures are licensed under CC BY 4.0; see [data/LICENSE.md](data/LICENSE.md) for scope and attribution.
