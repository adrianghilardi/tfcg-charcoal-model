# Reproducing release v0.3.0

Release v0.3.0 is the computational package used for the manuscript results. It starts from five supplied, aligned analytical rasters in `data/InRaster`; it does not reconstruct or independently validate the upstream maps.

## Full run

Use CPython 3.12 and run these commands from a fresh clone or the Zenodo source archive:

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

On Linux or macOS, replace `.venv/Scripts/python` with `.venv/bin/python`. The default configuration fixes seed 20260917 and runs 1,000 realizations for each of the reference, conservative and intensive scenarios over 2015–2086. The exact locked Windows output hashes are in `config/expected_results_v0.3.0.json`. `scripts/check_repeatability.py FIRST_RUN SECOND_RUN` also compares every stored numerical array exactly.

## What is recorded

Each run records the configuration, input hashes, package versions, parameter draws, annual realization-level stocks and flows, diagnostics, summary tables and output hashes. The driver refuses to write into a nonempty directory. All figures are regenerated from the included inputs or numerical output.

The Zenodo archive at <https://doi.org/10.5281/zenodo.22847506> contains the tagged source, the complete 1,000-realization output, regenerated figures and SHA-256 checksums. The GitHub tag is `v0.3.0`.

## Scope of reproducibility

This release provides computational reproduction from the five distributed analytical rasters. The origin, acquisition date and preprocessing of some upstream spatial products remain under coauthor review. The model results are conditional scenarios and have not been independently validated against observed charcoal production.
