# Ulaya Mbuyuni charcoal planning model

This Python model simulates standing woodland biomass, annual wood harvest and potential charcoal production under mapped community-forest harvesting rules in Ulaya Mbuyuni, Tanzania. It uses six analytical rasters and compares three combined management/productivity scenarios, two paired management-rule scenarios and a no-harvest control. Each reported scenario has 1,000 realizations over 2015–2086. The years define a case-study simulation, not measured production or a forecast from current conditions.

The [Zenodo v0.2.0 archive](https://doi.org/10.5281/zenodo.22836156) contains the versioned source, six-raster input bundle and complete numerical outputs. This is Adrian Ghilardi's personal repository, outside the MoFuSS organization. Code is MIT licensed; contributed analytical inputs, outputs and figures are CC BY 4.0. See [the model specification](docs/MODEL.md) for equations, units, masks and sampling.

## Reproduce the analysis

Use Python 3.12. From a new checkout:

```shell
python -m venv .venv
```

Activate `.venv` (`.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` on Linux/macOS), then run:

```shell
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python -m pytest -q
python -m zipfile -e data/tfcg_case_data_v0.2.0.zip data/external/ulaya
python scripts/verify_bundle.py data/external/ulaya
python scripts/run_experiments.py --source data/external/ulaya --output runs/main_1000
python scripts/summarize_results.py --main runs/main_1000 --output results/figures
python scripts/plot_inputs.py --source data/external/ulaya --output results/figures
```

The default seed is `20260917`. `config/main_1000.json` contains the six scenario configurations. The driver refuses a nonempty output folder and does not modify the input rasters. An eight-realization smoke run can use `--realizations 8` with a separate output folder; it is not a substitute for the 1,000-realization results.

Each experiment has `results.npz` with annual outputs, diagnostics and parameter draws. The run folder also contains `annual_results.csv`, `rotation_summary.csv`, the input hashes and a manifest of output hashes and software versions. `scripts/summarize_results.py` rebuilds the scenario figures, rotation precision table and paired contrasts. `scripts/plot_inputs.py` rebuilds the two-panel map of biomass and calendar inputs. To compare two same-configuration runs, use `python scripts/check_repeatability.py FIRST_RUN SECOND_RUN`.

## Interpretation

The reporting domain is 263.375 ha, calculated as the intersection of the reserve and valid calendar masks. The simulation starts with 17,420.8125 Mg of biomass in that domain. A different 267.75 ha number describes the full valid calendar footprint, including 4.375 ha outside the reserve; it is not the model reporting area. Statistically sampled K, q and kiln yield are inherited scenario assumptions, not fitted to local recovery observations. The biomass map's original field/remote-sensing processing and the physical moisture basis of biomass versus kiln yields have not yet been supplied. Intervals therefore describe conditional simulation variation; they are not empirical uncertainty in actual programme output.

The six analytical raster files are preserved byte for byte in the input bundle. The source code and data release reproduce the numerical analysis from these rasters, but do not reconstruct upstream raw imagery or field measurements. Current management rules, forest recovery and charcoal yields need programme and field review before using the model to set production targets.
