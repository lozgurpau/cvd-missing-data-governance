# Data dictionary

This file describes the input files read by the pipeline, the variables of the analysis table and their coding. The coding was defined together with the study cardiologist and is documented, not changed, by the code (`cvdrev/data.py`, `write_data_dictionary`; the same content is written to `veri/veri_sozlugu.csv` and `veri/veri_sozlugu_ek.csv` by the `veri` stage).

The study files are not part of this repository. `synthetic_data/` holds a synthetic workbook with the same name and layout (see the last section).

## 1. Input files

| File | Content | Read by |
|---|---|---|
| `raw_export.xlsx` | sheet `11706`: all records of the extract; sheet `7680`: records kept by the exclusion rule, in the same order and with recoded categories | stages `kontrol`, `veri`; a different local file name is set in `columns.local.yaml` (`raw_file`) |

Exclusion rule: a record enters the analysis set when fewer than six of the 20 coded columns of sheet `11706` (all columns except the identifier and the five free-text columns) are empty. The outcome column is never empty, so the rule counts 19 clinical columns.

## 2. Workbook columns

Both sheets have the same 26 columns (in a different order). "Raw" refers to sheet `11706`; "analysis" to sheet `7680` and to `veri/analytic.parquet`.

The identifier column and the five free-text columns are listed under generic names. The repository never contains the column names of the local data export for these six columns: a local file `columns.local.yaml` (not part of the repository; listed in `.gitignore`) maps each generic name to the local name, and `cvdrev/data.py` renames the columns to the generic names immediately after reading the workbook. `columns.example.yaml` shows the format; the synthetic files use the generic names directly. All five free-text columns are searched, in memory, for blood-pressure and ejection-fraction values.

| Column | Short name | Meaning | Type and coding |
|---|---|---|---|
| `id_column` | – | record identifier | integer. Read in memory only to check the row order of the two sheets; never written to any output. |
| `CİNSİYET_KOD` | `cins` | sex | 1 male, 0 female |
| `YAŞ` | `age` | age (years) | integer; 14–97 in the study data |
| `Total_kolesterol` | `kol` | total cholesterol (mg/dL) | integer; empty = missing |
| `LDL_Kolesterol_Sonuç` | `ldl` | LDL cholesterol (mg/dL) | decimal (1 digit); empty = missing; text with a decimal comma in sheet `7680` |
| `HDL_kolesterol` | `hdl` | HDL cholesterol (mg/dL) | decimal (1 digit); empty = missing |
| `Trigliserid` | `trig` | triglycerides (mg/dL) | integer; empty = missing; values above the assay limit are stored as text `> <limit>` and analyzed as the limit value with the flag `trig_censored` |
| `HGB` | `hgb` | hemoglobin (g/dL) | decimal (1 digit); empty = missing; text with a decimal comma in sheet `7680` |
| `teşhis_kod` | `target` | outcome: recorded cardiac diagnosis | 1 recorded cardiac diagnosis (ischemic heart disease, valve disease, atrial fibrillation or other arrhythmia, heart failure, atherosclerotic heart disease), 0 none; coded with the study cardiologist |
| `Kreatinin` | `kre` | creatinine (mg/dL) | decimal (2 digits); empty = missing; text with a decimal comma in sheet `7680` |
| `Eko_ef_kod` | `eko` | ejection fraction band (%) | raw 0–2, empty = unknown; analysis 0 unknown, 1 >50 (normal), 2 31–50 (mild dysfunction; EF = 50 included), 3 ≤30 (severe dysfunction); study-specific bands |
| `Ekg_kod` | `ekg` | ECG category | raw 0–5, empty = unknown; analysis 0 unknown, 1 normal rhythm, 2 rhythm disorder, 3 conduction disorder, 4 ischemic findings, 5 implanted device, 6 previous myocardial infarction |
| `Glikoz_Kod` | `glikoz` | fasting glucose band (mg/dL) | raw 0–2, empty = unknown; analysis 0 unknown, 1 <100, 2 100–125 (impaired fasting glucose range), 3 ≥126 (diabetes range); ADA thresholds |
| `Efor_kod` | `efor` | exercise-test code | raw 0–4, empty = missing (79.5% empty in the raw data); not a predictor; counted only by the exclusion rule. Sheet `7680` of the study file uses a different, non-monotonic recoding of this column (see the comment in `cvdrev/data.py`). |
| `Dm_kod` | `dm` | diabetes | 1 documented, 0 not documented |
| `Sigara_kod` | `sgr` | smoking | 1 documented, 0 not documented |
| `Göğüs_ağrısı_kod` | `gogus` | chest pain | 1 documented, 0 not documented |
| `Çarpıntı_kod` | `carpinti` | palpitations | 1 documented, 0 not documented |
| `Aö_kod` | `ao` | family history | 1 present, 0 absent, 2 no background record |
| `Ht_kod` | `ht` | hypertension history | 1 documented, 0 not documented |
| `tansiyon_kod` | `tans` | systolic blood-pressure band (mmHg) | raw 0–3, empty = unknown; analysis 0 unknown (neither a measurement nor a hypertension history recorded), 1 <90, 2 90–120, 3 121–140, 4 hypertensive range (measured systolic >140 mmHg, or documented hypertension without a recorded measurement). In the analysis set 3,260 records have a measurement; 1,722 records without a usable measurement were coded by rule, 1,679 of them from documented hypertension (highest band) and 43 from other entries; 2,698 records are unknown. The highest band contains 2,407 records, 1,682 of them coded by rule |
| `text_history` | – | free text: history (repeat-visit proxy; follow-up mentions) | text; read in memory only; never written to any output |
| `text_past_history` | – | free text: past history (repeat-visit proxy) | text; read in memory only; never written to any output |
| `text_physical_treatment` | – | free text: notes | text; read in memory only; never written to any output |
| `text_treatment` | – | free text: treatment notes | text; read in memory only; never written to any output |
| `text_diagnosis` | – | free text: diagnosis (label-noise measures, diagnosis-family flags) | text; read in memory only; never written to any output |

Binary codes: 0 means "not documented", not "confirmed absent".

## 3. Analysis table (`veri/analytic.parquet`)

One row per record of the analysis set, in the row order of sheet `7680`.

| Column | Meaning |
|---|---|
| `rec_id` | record number in the analysis set (0, 1, …), the only record key used in outputs |
| `age`, `cins`, `kol`, `trig`, `hgb`, `kre`, `hdl`, `ldl`, `dm`, `sgr`, `gogus`, `carpinti`, `ao`, `glikoz`, `eko`, `ht`, `ekg`, `tans` | the 18 predictors (coding as in section 2, analysis coding) |
| `target` | outcome |
| `efor` | exercise-test code (raw + 1, 0 = missing; not a predictor) |
| `trig_censored` | triglyceride value was censored at the assay limit |
| `tans_A` | systolic band from measurements only (sensitivity arm A): same bands as `tans`, 0 for every record without a measurement in the text |
| `bp_measured` | a systolic measurement in the standard `TA: x/y` form was found in the free text |
| `bp_sys_strict`, `bp_sys_ext` | systolic value from the standard pattern, and from the standard plus extended patterns |
| `ef_text` | ejection fraction (%) found in the free text |
| `bp_source` | origin of `tans`: `measured`, `rule_ht` (top band from hypertension history without a measurement), `coded_other`, `unknown` |
| `dx_empty` | the diagnosis text is empty |
| `dx_group_size`, `label_majority`, `label_deviates` | label-noise measures: size of the group of records with an identical diagnosis text, majority outcome of that group (ties → 1), record deviates from it |
| `proxy_group`, `proxy_group_120` | repeat-visit proxy: records with identical history and background text (longer than 40 or 120 characters), the same sex and an age range of at most 6 years share a group label `g####`; other records get `r<row>` |
| `dx_aile_iskemik`, `dx_aile_kapak`, `dx_aile_atriyal_fibrilasyon`, `dx_aile_kalp_yetmezligi`, `dx_aile_aterosklerotik` | diagnosis-family flags (ischemic, valve, atrial fibrillation, heart failure, atherosclerotic) from patterns in the case-folded diagnosis text; a record can belong to several families |

All text-derived columns are computed in memory; the text itself is not stored. `veri/raw_coded.parquet` holds the 20 coded columns of all records of sheet `11706` (analysis coding, short names) with `n_missing` and `kept`, for the exclusion-threshold sensitivity analysis.

## 4. Synthetic workbook

`synthetic_data/` contains a workbook with the name, sheets, columns, column order and cell types described above, written by `tools/make_synthetic.py` from aggregate statistics only (`tools/synthetic_marginals.json`). Differences from the study workbook:

* identifiers are text (`SYN00001`, `SYN00002`, …); the identifier and free-text columns carry the generic names;
* the five free-text columns contain fixed template phrases that start with `Sentetik`; blood-pressure and ejection-fraction values appear in the forms `TA: x/y mmHg`, `KB: x-y` and `EF %x` so that the text-derived columns can be computed;
* sheet `7680` stores the exercise-test code as raw + 1 (0 = missing);
* every record keeps at least one laboratory value, so the excluded part has no record with the whole laboratory panel missing;
* values are drawn independently given the outcome, so relations between variables are not those of the study data.

See `synthetic_data/README.md` for the checksum.
