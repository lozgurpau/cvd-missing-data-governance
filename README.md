# Missing-data governance in routine hospital records — analysis code

This repository contains the analysis code, configuration, data dictionary and a synthetic example dataset for the article

> Gönül Kara, Leyla Özgür Polat. Missing-Data Governance in Real-World Cardiovascular Case Identification from Routine Hospital Records: Effects on Machine-Learning Performance and Interpretability. *BMC Medical Informatics and Decision Making* (volume, article number and DOI will be added on publication).

Repository: `https://github.com/lozgurpau/cvd-missing-data-governance` · License: MIT ([LICENSE](LICENSE)) · Citation metadata: [CITATION.cff](CITATION.cff) · Changes: [CHANGELOG.md](CHANGELOG.md)

The study data cannot be shared (see [Data availability](#data-availability)). The code runs end to end on the synthetic workbook in `synthetic_data/`; results obtained on it have no scientific meaning.

## Contents

1. [What the code does](#what-the-code-does)
2. [Repository layout](#repository-layout)
3. [Installation](#installation)
4. [Quick start with the synthetic data](#quick-start-with-the-synthetic-data)
5. [Running on the study data](#running-on-the-study-data)
6. [Column-name mapping](#column-name-mapping)
7. [Scales](#scales)
8. [Stages](#stages)
9. [Checkpoints and resuming](#checkpoints-and-resuming)
10. [Outputs and logs](#outputs-and-logs)
11. [Run times](#run-times)
12. [Privacy safeguards](#privacy-safeguards)
13. [Synthetic mode](#synthetic-mode)
14. [Tests](#tests)
15. [Publishing](#publishing)
16. [Data availability](#data-availability)

## What the code does

The pipeline builds the analysis set from a hospital cardiology records extract (records with six or more missing values among the 19 coded clinical variables, that is, the 20 coded columns without the outcome, are excluded), then compares seven missing-data strategies for identifying recorded cardiac cases:

| Code | Strategy |
|---|---|
| S1 | single-value imputation (numeric median, categorical mode) |
| S2 | native handling of missing values (ordinal codes with NaN; only the six algorithms that accept NaN) |
| S3 | "unknown" category for categorical variables, median for numeric variables |
| S4 | complete cases |
| S5 | multiple imputation by chained equations (MICE, m = 5, Rubin pooling) |
| S6 | iterative imputation with extra trees (MissForest type) |
| S7 | median/mode imputation plus a missingness indicator for every incomplete variable |

Twelve algorithms are used: logistic regression, support vector machine, Gaussian naive Bayes, k-nearest neighbors, decision tree, random forest, AdaBoost, gradient boosting, XGBoost, LightGBM and CatBoost in every strategy except S2, and HistGradientBoosting in S2 (S2 uses the six algorithms that handle missing values natively). All preprocessing is fitted inside the training folds. The full design uses 5 × 5 repeated stratified cross-validation, inner 3-fold tuning on AUROC, seed 20260101 and 1,000 bootstrap replicates. The code also runs the sensitivity analyses and writes the result tables (metrics, paired comparisons, calibration, thresholds, subgroups and sensitivity summaries).

Code comments, log messages and most output file names are in Turkish; this document, the data dictionary ([DATA_DICTIONARY.md](DATA_DICTIONARY.md)) and the output reference ([docs/OUTPUTS.md](docs/OUTPUTS.md)) are in English.

## Repository layout

```
config.yaml                 configuration for the study data (paths.data_dir: data)
config_synthetic.yaml       configuration for the synthetic example (data.synthetic: true)
columns.example.yaml        format of the local column-name mapping columns.local.yaml (generic names)
run.py                      single entry point (all stages)
run_all.ps1                 Windows launcher (creates the conda environment, keeps the machine awake, logs the console)
bench_workers.py            worker-count benchmark -> out/isci_kiyasi.json
environment.yml             conda environment (pinned versions)
environment_gevsek.yml      fallback conda environment (only model libraries pinned)
requirements.txt            pip fallback (Python 3.11)
cvdrev/                     analysis package: one module per stage (data, cohort, main analysis, sensitivity, report, privacy audit)
testler/                    regression comparison, independent privacy scan
tools/make_synthetic.py     synthetic data generator
tools/synthetic_marginals.json   aggregate statistics read by the generator (no record-level values)
synthetic_data/             synthetic example workbook raw_export.xlsx (layout of the study workbook)
docs/OUTPUTS.md             every output file and its columns
DATA_DICTIONARY.md          input files, variables and coding
```

`data/` (study data), `columns.local.yaml` (local column and file names), `config.local.yaml` and all output folders are excluded by `.gitignore`.

## Installation

Python 3.11 is required. The `kontrol` stage stops the run unless these exact versions are installed: scikit-learn 1.9.1, LightGBM 4.7.0, XGBoost 3.4.2, CatBoost 1.2.7 and SHAP 0.48.0.

With conda (Windows PowerShell or a POSIX shell):

```
conda env create -f environment.yml          # creates the environment "cvdrev"
conda activate cvdrev
```

If the solver fails, use `environment_gevsek.yml` (only the model libraries are pinned). Without conda:

```powershell
# Windows PowerShell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```sh
# POSIX shell
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

The code is CPU-only. It was developed and tested on Windows 10; the commands below are given for both shells.

## Quick start with the synthetic data

The synthetic workbook is included. Regenerating it is optional: with the same seed and library versions it is reproduced byte for byte (the script prints the SHA-256 prefix of the file; the value for this release is listed in `synthetic_data/README.md`).

```powershell
# Windows PowerShell, from the repository folder
python tools\make_synthetic.py                                  # optional: rewrites synthetic_data\
python run.py --config config_synthetic.yaml --scale mini --stage all
```

```sh
# POSIX shell
python tools/make_synthetic.py                                  # optional: rewrites synthetic_data/
python run.py --config config_synthetic.yaml --scale mini --stage all
```

Outputs go to `out_synthetic_mini/`; the results archive is written next to the configuration file (`sonuclar_mini_<date>_<time>.zip`). The run takes about 9 minutes with one worker (see [Run times](#run-times)). Add `--n-jobs 4` to use four worker processes.

## Running on the study data

Place the raw workbook `raw_export.xlsx` in `data/` (not part of this repository). If the raw workbook has another local file name, give that name as `raw_file` in `columns.local.yaml` instead of renaming the file. The `kontrol` stage verifies the SHA-256 checksum of the workbook against the value in `cvdrev/checks.py` (listed under the generic file name). Create `columns.local.yaml` next to `config.yaml` first (see [Column-name mapping](#column-name-mapping)).

```powershell
# Windows PowerShell (if script execution is disabled: Set-ExecutionPolicy -Scope Process Bypass)
.\run_all.ps1 -Scale deneme                    # all stages at the short scale
.\run_all.ps1 -Scale tam -NJobs 8              # full run with 8 workers
.\run_all.ps1 -Scale tam -Stage veri,rapor     # selected stages
# equivalent without the launcher:
python run.py --scale tam --stage all --n-jobs 8
```

```sh
# POSIX shell
python run.py --scale deneme --stage all
python run.py --scale tam --stage all --n-jobs 8
python run.py --scale tam --stage veri,rapor
```

`--stage` takes `all` or a comma-separated list of stage names; `--scale` overrides `scale` in the configuration; `--n-jobs` overrides `compute.n_jobs` and may not exceed the number of logical cores. `python bench_workers.py --workers 4 8 12` measures the wall time of a fixed task set for several worker counts and suggests a value (`out/isci_kiyasi.json`).

`run_all.ps1` changes Windows power settings: it sets the sleep and hibernation timeouts on AC power to "never" and switches a Balanced or Power saver plan to High performance. These settings remain after the run. Use `python run.py` directly to avoid them.

## Column-name mapping

The repository uses generic names for the identifier column and the five free-text columns of the raw workbook: `id_column`, `text_history`, `text_past_history`, `text_physical_treatment`, `text_treatment` and `text_diagnosis` (see [DATA_DICTIONARY.md](DATA_DICTIONARY.md)). The column names of the local data export are not part of the repository. To run the code on a local export, copy `columns.example.yaml` to `columns.local.yaml` in the folder of the configuration file and replace each value with the column name used in the export (`paths.columns_local` in the configuration can point to another file).

* `cvdrev/data.py` renames these six columns to the generic names immediately after reading the workbook; all later code uses the generic names. If a sheet still lacks a generic name after renaming, the `veri` stage stops with a message that lists the missing generic names.
* The privacy audit (`cvdrev/gizlilik.py`) and the independent scanner (`testler/gizlilik_taramasi.py`, option `--eslem`) add the local names to their lists of forbidden column names. Without `columns.local.yaml` they check the generic names only and write a warning.
* `columns.local.yaml` may also hold `raw_file`, the local file name of the raw workbook; the repository uses only the generic name `raw_export.xlsx` (`paths.raw_xlsx`).
* `columns.local.yaml` is listed in `.gitignore` and is never written to the output folder or the results archive. See [Publishing](#publishing) before uploading files through the GitHub web interface.
* The synthetic files use the generic names; `config_synthetic.yaml` points to `columns.example.yaml`, in which every name maps to itself.

## Scales

| Scale | Outer cross-validation | Inner folds | Grid | MICE m | Bootstrap | SHAP rows | Output folder |
|---|---|---|---|---|---|---|---|
| `tam` (full) | 5 repeats × 5 folds | 3 | full | 5 | 1,000 | all | `out/` |
| `deneme` (trial) | 1 × 5 folds | 2 | ≤ 4 combinations per model | 2 | 50 | 400 | `out_deneme/` |
| `mini` | 1 × 2 folds | 2 | ≤ 2 combinations per model | 2 | 20 | 200 | `out_mini/` |

`mini` only tests the pipeline. The output folder is `paths.out_dir` plus `_<scale>` for scales other than `tam`.

## Stages

| Stage | Content | Main outputs (in the output folder) |
|---|---|---|
| `kontrol` | Python and library versions, input files and checksums, worker count | `kontrol_raporu.json` |
| `veri` | raw workbook → analysis table; exclusion rule; known-count checks; cohort flow, excluded vs kept records, Table 1, label noise, missingness patterns, models of missingness, Little's MCAR test | `veri/analytic.parquet`, `veri/veri_denetimi.json`, `veri/kohort/*` |
| `ana` | S1–S7 × algorithms; repeated stratified outer cross-validation, inner tuning on AUROC; out-of-fold probabilities | `ana/tahminler.parquet`, `ana/sabit_hiperparametreler.json` |
| `duyarlilik` | sensitivity analyses (blood-pressure coding, label noise, leakage sets, repeat-visit proxy groups, exclusion thresholds, δ-adjusted MNAR, learning curve, fixed hyperparameters, clinical baseline, winsorization, continuous BP/EF, age ≥ 18, SHAP and indicator ablation, controlled missingness simulation) | `duyarlilik/<arm>/` |
| `rapor` | metrics with bootstrap confidence intervals, paired comparisons (DeLong, McNemar, Nadeau–Bengio corrected t, Holm), calibration, thresholds and operating points, decision curves, subgroups, selective prediction, compute cost, Rubin pooling for S5; manifest, privacy self-audit and results archive | `rapor/**`, `manifest.json`, `../sonuclar_<scale>_<date>_<time>.zip` |

`--stage all` runs the five stages in this order. `duyarlilik` needs the hyperparameters written by `ana`; `rapor` reports only the stages whose outputs exist. The arms of `duyarlilik` and the optional reports are switched in `config.yaml` (`sensitivity.*`, `optional.*`); [docs/OUTPUTS.md](docs/OUTPUTS.md) lists the files each switch controls.

## Checkpoints and resuming

Every unit of work (strategy × repeat × fold, with one file per algorithm) is stored under `<output folder>/checkpoints/` as soon as it finishes. If a run stops, give the same command again: finished units are read back and only the missing ones are computed. Checkpoint keys contain only the task name, not a hash of the data or the configuration. After changing the input data or a design setting, use a new output folder or delete `checkpoints/`. To recompute one stage, delete its output folder and the matching `checkpoints/<arm>/` folders.

## Outputs and logs

```
<output folder>/
  kontrol_raporu.json        environment and input checks
  run_status.json            per-stage status and duration of the latest invocation
  cvdrev.log                 Python log (appended across invocations)
  manifest.json              file list with SHA-256, configuration, library versions, privacy audit result
  veri/                      analysis table, data dictionary, cohort tables (veri/kohort/)
  ana/                       out-of-fold predictions, selected hyperparameters, timings
  duyarlilik/<arm>/          predictions and summaries of each sensitivity arm
  rapor/                     report tables (rapor/ana/ for the main analysis, rapor/<arm>/ for the arms)
  checkpoints/               resumable units (not included in the results archive)
<configuration folder>/sonuclar_<scale>_<date>_<time>.zip   results archive (all outputs except checkpoints)
```

`run_all.ps1` also writes the console output to `out\run_<date>_<time>.log` (always in `out\`, whatever the scale). [docs/OUTPUTS.md](docs/OUTPUTS.md) describes every file and its columns.

## Run times

Measured with one worker (`--n-jobs 1`, one thread per model) on a Windows workstation with an Intel Xeon W-2145 processor (8 cores, 32 GB RAM). Seconds per stage:

| Run | kontrol | veri | ana | duyarlilik | rapor | Total |
|---|---|---|---|---|---|---|
| synthetic data, `mini` (this repository) | 3.3 | 3.5 | 146.7 | 270.1 | 71.0 | 494.6 |
| study data, `mini` | 4 | 23 | 392 | 894 | 181 | 1,494 |
| study data, `deneme` | 3.4 | 23.1 | 2,354.6 | 3,877.6 | 311.0 | 6,570 |
| study data, `tam` | – | – | 36,894.0 | 22,348.0 | 2,912.6 | 62,154.6 |

On the study data the stages were timed in separate runs: `duyarlilik` in two parts (15,974.9 s for all arms except the continuous blood pressure and ejection fraction arm, the exclusion of patients younger than 18 years, `shap_v2` and the missingness simulation; 6,373.1 s for these four arms, with the other arms read from their checkpoints) and `rapor` with all arms. A full run on the study data with one worker therefore takes about 17 hours. More workers shorten the `ana` and `duyarlilik` stages; the speed-up depends on the machine (`bench_workers.py`). Durations of every unit are written to `ana/parametreler_sureler.csv`, `duyarlilik/<arm>/parametreler_sureler.csv` and `rapor/ana/hesap_maliyeti.csv`.

## Privacy safeguards

The identifier column and the five free-text columns of the raw workbook are read into memory only, and the repository contains only their generic names (see [Column-name mapping](#column-name-mapping)). The `veri` stage writes derived variables (for example the systolic value found in the text, or diagnosis-family flags) and never the text or the identifier; records are tracked by `rec_id`, the row number in sheet `7680`.

Before the results archive is written, the `rapor` stage audits every parquet, CSV and JSON file that goes into it (`cvdrev/gizlilik.py`): a column or key named like the identifier or a free-text column (generic names and, when `columns.local.yaml` exists, the local names), or any text value longer than 80 characters, stops the stage and no archive is kept. Two narrow exceptions are recorded in `manifest.json` → `gizlilik_denetimi`: strings that parse as numeric lists or parameter dictionaries, and package documentation strings listed in `gizlilik.ALLOW_LONG`.

`testler/gizlilik_taramasi.py` is an independent scanner for a folder and the archives in it. It reports column or key names that contain the identifier or free-text names (generic names and the names in `columns.local.yaml`) as substrings, long text values and, when the raw workbook is given with `--ham`, every 25-character aligned fragment of the raw free text and every identifier value of five or more digits found in the scanned files.

The results archive of a run on the study data contains record-level coded values and predictions. It must not be published.

## Synthetic mode

`config_synthetic.yaml` differs from `config.yaml` only in `paths.data_dir` (`synthetic_data`), `paths.out_dir` (`out_synthetic`), `paths.columns_local` (`columns.example.yaml`), `scale` (`mini`), `compute.n_jobs` (1) and `data.synthetic: true`. With `data.synthetic: true`:

* `cvdrev/data.py` skips the checks that only hold for the study data — sheet row counts, analysis-set size, exclusion-threshold counts, row order and value equality between sheets `11706` and `7680`, and the known cohort counts — and writes one warning per skipped check to the log; `veri/veri_denetimi.json` gets `"sentetik_veri": true` and the list of skipped checks;
* the `kontrol` stage reports checksum differences of the input files as warnings (`kontrol_raporu.json` → `uyarilar`) instead of stopping; version checks still apply.

With `data.synthetic: false` (the default in `config.yaml`) and a `columns.local.yaml` for the study export, the outputs are those of the analysis package used for the article (checked on the study data at scale `mini`: identical out-of-fold predictions and report columns; apart from timing values, only two text entries differ, because this repository uses generic column and file names: the repeat-visit proxy note in `veri/veri_sozlugu.csv` and the file name of the raw workbook in `kontrol_raporu.json`).

`tools/make_synthetic.py` writes the input workbook (`raw_export.xlsx`) with the sheets, columns, column order and cell types of the study workbook, except that the identifier and free-text columns carry their generic names and identifiers are text. It reads only `tools/synthetic_marginals.json`: the Table 1 marginals of the analysis set by outcome, cohort-level counts and missing-cell counts. Each variable is drawn independently given the outcome; the coding rules of the data dictionary are then imposed (blood-pressure band rule, 0 = unknown, exclusion rule). Identifiers are `SYN00001`, `SYN00002`, …; free-text cells contain fixed template phrases that start with `Sentetik`. Relations between variables other than these rules are not reproduced. Options: `--n` (records, default 1000), `--seed` (default 20260101), `--out` (default `synthetic_data`). The design choices that are not taken from the study data are listed at the top of the script.

## Tests

* `python testler/regresyon.py --eski <folder A> --yeni <folder B> --cikti comparison.csv` compares two output folders file by file and column by column (predictions to the last digit; timing columns and time-stamped files are reported as expected differences).
* `python testler/gizlilik_taramasi.py --klasor <folder> [--ham <raw workbook>] [--eslem columns.local.yaml] [--cikti scan.json]` is the independent privacy scan described above.

## Publishing

Publish the repository with git (`git add`, `git commit`, `git push`); git applies `.gitignore`, which excludes `data/`, `columns.local.yaml`, `config.local.yaml`, output folders, results archives and Python caches. `.gitignore` applies to git only. When files are uploaded through the GitHub web interface, nothing is filtered: do not select `columns.local.yaml` (or `config.local.yaml`, if present), the `data/` folder, output folders or results archives.

## Data availability

The patient-level data analyzed in the article are not publicly available: they were obtained from the hospital solely for the purposes of the study, and authorization for their public release or redistribution was not granted. This repository contains no study data. The synthetic workbook in `synthetic_data/` has the same layout and was generated from aggregate statistics only.
