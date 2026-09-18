# Ulaya Mbuyuni charcoal planning model

Reproduce annual woodland biomass, wood harvest and potential charcoal production for a historical TFCG/MJUMITA case study in Tanzania. The repository preserves the supplied DINAMICA EGO model, provides a tested Python implementation, and separates the original equations from proposed corrections.

**Status: version 0.1.0 release candidate, 17 September 2026.** Repository: [adrianghilardi/tfcg-charcoal-model](https://github.com/adrianghilardi/tfcg-charcoal-model), a personal repository outside the MoFuSS organization. The [Zenodo archive](https://doi.org/10.5281/zenodo.22822183) contains exact source, inputs and complete numerical outputs in Adrian's personal account, with no community assignment. The archived source is tag `v0.1.0`, commit `2f89e809af639fad648fb244950e462d86341852`; subsequent main-branch changes document publication and post-release checks. Code: MIT. Contributed analytical data and numerical outputs: CC BY 4.0.

## What has been reproduced

- All 288 archived baseline annual values reproduce exactly in DINAMICA EGO 8.3.0.20250117. Python differs by less than 5 × 10⁻¹¹ Mg.
- Four cross-engine checks cover 1,368 values: the supplied baseline, intensive deterministic original/corrected growth, and three stochastic reference realizations. All pass at 10⁻⁵ Mg absolute tolerance.
- A clean Python environment, using only the minimal case-study bundle, reproduced 607,876 array elements exactly across all 13 baseline/audit experiments. The arrays include outputs, diagnostics and exported parameter draws.
- Main corrected experiments use 1,000 realizations over 72 years. A 100-realization audit isolates equation and distribution changes. Tests also cover mass balance, harvest timing, thresholds, growth behaviour, random sampling and an exact memory optimization.

A fresh public GitHub checkout also reproduced the complete 1,000-realization corrected suite exactly: 3,036,676 checked array elements.

These checks establish computational reproducibility from the **delivered analytical rasters**. They do not reconstruct the unpublished raw field/remote-sensing processing, independently validate woodland recovery, or recover the old manuscript's missing 100-realization ensemble. That ensemble's table is superseded by explicitly identified new experiments.

## Install

Use Python 3.12. The full local verification environment was CPython 3.12.14 on Windows x86-64. [GitHub Actions checks passed on Windows and Linux](https://github.com/adrianghilardi/tfcg-charcoal-model/actions/runs/35298362324), including nine unit tests, the archived baseline, an eight-realization audit and figure generation. The full 1,000-realization analysis was run locally on Windows.

```shell
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` on PowerShell, or `source .venv/bin/activate` on Linux/macOS. Then:

```shell
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python -m pytest -q
```

The pinned file records the tested dependencies. It is a version lock, not a wheel archive or a cryptographically locked supply-chain environment. Rasterio and SciPy wheels supply their required native components on the tested platform; the Python workflow does not need DINAMICA.

## Obtain and verify the case study

The repository includes `data/tfcg_case_data_v0.1.0.zip`; the identical archive is [available from Zenodo](https://zenodo.org/records/22822183/files/tfcg_case_data_v0.1.0.zip?download=1). Extract it into `data/external/ulaya`. Do not replace it with a similarly named calendar: the required raster is `InRaster/cosecha24.tif` supplied by the author.

```shell
python -m zipfile -e data/tfcg_case_data_v0.1.0.zip data/external/ulaya
python scripts/verify_bundle.py data/external/ulaya
```

The bundle contains 12 original files plus licence notices and a checksum manifest. It is about 0.6 MB. The full supplied archive exceeds 1 GB because it also contains old rasters, outputs and unused source data. These are not necessary to reproduce this analytical workflow.

## Rebuild the analysis and figures

Use fresh output folders. Existing nonempty run folders are refused; the supplied inputs are never overwritten.

```shell
python scripts/run_experiments.py --source data/external/ulaya --output runs/audit_100 --realizations 100 --seed 20260917
python scripts/run_experiments.py --source data/external/ulaya --output runs/corrected_1000 --realizations 1000 --seed 20260917 --corrected-only
python scripts/summarize_results.py --main runs/corrected_1000 --audit runs/audit_100 --output results/figures
python scripts/plot_inputs.py --source data/external/ulaya --output results/figures
```

The observed simulation times were approximately 43 seconds for the audit and two minutes for the corrected suite; hardware and file writing affect elapsed time. Reserve a few GB for the environment, outputs and release archives. Input preparation and simulations stay within a modest memory footprint by representing identical, unharvested background cells once; tests verify exact equivalence to full cell arrays.

Every run starts by checking the archived baseline. `annual_results.csv` contains individual annual outputs, diagnostics and parameter draws. `rotation_summary.csv` gives ensemble means and quantiles of realization-level 24-year means. Each experiment also has `configuration.json` and `results.npz`. The manifest records input/output hashes, software versions, seeds and checks. The summary script creates PDF/PNG figures, Monte Carlo standard errors and paired management differences. File hashes identify exact artifacts; elapsed times, absolute paths and ZIP timestamps are not expected to match between machines.

For a second independent run, repeat the first command with a fresh folder and compare:

```shell
python scripts/check_repeatability.py runs/audit_100 runs/audit_100_repeat
```

See [model equations](docs/MODEL.md), [the audit and author queries](docs/AUDIT.md), and [release instructions](docs/RELEASE.md). Numerical reference summaries and observed validation reports are in `results/reference/`. Larger per-realization results belong in the Zenodo results archive, not Git.

## Native DINAMICA check

Install DINAMICA separately under its own licence. The supplied model was saved with version 4.0.11.20181011. Verification used version 8.3.0.20250117. The console upgrades the file in memory; the original model remains unchanged.

```shell
python scripts/run_native.py --source data/external/ulaya --schedule data/external/ulaya/InRaster/cosecha24.tif --output runs/authoritative_native_baseline --console "C:\Program Files\Dinamica EGO 8\DinamicaConsole8.exe"
python scripts/run_native.py --source data/external/ulaya --schedule data/external/ulaya/InRaster/cosecha24.tif --output runs/native_intensive_legacy --scenario intensive --realizations 1 --constants config/native_zero_sd.json
python scripts/run_native.py --source data/external/ulaya --schedule data/external/ulaya/InRaster/cosecha24.tif --output runs/native_intensive_corrected --scenario intensive --realizations 1 --constants config/native_zero_sd.json --growth corrected
python scripts/run_native.py --source data/external/ulaya --schedule data/external/ulaya/InRaster/cosecha24.tif --output runs/native_reference_stochastic --scenario reference --realizations 3
python scripts/validate_native.py --source data/external/ulaya --runs runs --output results/native_validation.json
```

The runner rewrites paths in a new `prepared.egoml`, records every change, fixes the native random seed and uses one processor. Unless `--save-maps` is given, it removes map-saving side effects to avoid hundreds of unnecessary outputs. Native stochastic draws are recovered from its tables for the cross-engine comparison; NumPy and DINAMICA are not assumed to have the same random generator. Native `--growth corrected` changes the growth expression only; it does **not** implement truncated distributions. Use the Python suite for the main bounded experiments.

## Scientific interpretation

The calendar covers 2015–2086 scenario years and is not an updated 2026 production forecast. Annual biomass is reported after harvesting and regrowth. Wood and charcoal are annual flows; standing biomass is a stock. The code applies no moisture correction. The physical biomass/feedstock moisture basis still requires author confirmation.

The corrected model and bounded priors are proposals supported by rerun diagnostics, not field-calibrated replacements. In particular, truncating intensive-scenario growth draws changes their mean from a nominal 0.95 to about 0.904. Management-only experiments hold growth and kiln draws identical across scenarios. The manuscript reports both contrasts and their limitations. No conclusions about livelihoods, biodiversity, avoided deforestation or net emissions follow directly from these outputs.
