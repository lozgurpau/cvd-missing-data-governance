# Changelog

## 1.0.0 (2026-10-21)

First public release of the analysis code for the article. It contains:

* the pipeline (`run.py`, `cvdrev/`) with the stages `kontrol`, `veri`, `ana`, `duyarlilik` and `rapor` and the scales `mini`, `deneme` and `tam`;
* the configuration for the study data (`config.yaml`) and for the synthetic example (`config_synthetic.yaml`), and the format of the local column-name mapping (`columns.example.yaml`);
* the data dictionary (`DATA_DICTIONARY.md`) and the reference of every output file (`docs/OUTPUTS.md`);
* a synthetic example workbook generated from aggregate statistics only (`synthetic_data/`, `tools/make_synthetic.py`, `tools/synthetic_marginals.json`);
* the regression comparison and the independent privacy scan (`testler/`);
* the software environment (`environment.yml`, `environment_gevsek.yml`, `requirements.txt`), the Windows launcher (`run_all.ps1`) and the worker-count benchmark (`bench_workers.py`).
