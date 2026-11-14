# Lung cancer deaths relative to the volume of lung cancer care in Korean districts, 2011-2024

Analysis code for the manuscript

> Kim S. *Where do lung cancer deaths exceed the volume of lung cancer care in Korea?* Manuscript under review.

Archived version: Zenodo, https://doi.org/10.5281/zenodo.24235623.

## Contents

This repository contains code only. The processed district-year data (analytic panel, expected counts, result tables, adjacency graph and boundary file) are not included; they are available from the author on reasonable request. All source statistics are public (see Data sources).

| Path | What it is |
|---|---|
| `01_스크립트/` | Analysis scripts (below) |
| `04_분석/LCAD/sets_LCAD_std3.json`, `sets_LCAD_smr.json`, `sets_LCAD_ma3.json`, `sets_LCAD_s577.json`, `sets_LCAD_s2.json`, `sets_LCAD_s8.json`, `config_LCAD_std3.json`, `run_std3_chain.sh` | Covariates with expected directions, forced controls, negative controls, comparison outcomes and model settings (principal model `std3`; sensitivity versions without the treatment adjustment `smr`, with a 3-year treatment ratio `ma3`, with the queen contiguity graph `s577`, without the share aged 80 or older `s2`, and with expected deaths from ten age groups `s8`) |
| `04_분석/LCAD/MS/` | Scripts that read the result tables and write every number, table and figure in the manuscript and Supplemental Data 1, including `content_lcad.py`, which generates the Methods and Results text (the draft source of the Introduction and Discussion is not included) |

Folder and some column names are in Korean because the source tables are Korean; each script has a header comment describing its inputs and outputs.

## Data sources

All inputs are public, aggregated statistics. No individual-level data are included.

- Deaths with lung cancer (ICD-10 C33-C34) as the underlying cause by district of residence: Statistics Korea, cause-of-death statistics (KOSIS DT_1B34E13), 2011-2024; national deaths by cause, sex and 5-year age group (KOSIS DT_1B34E01). Comparison outcomes: deaths from transport accidents and falls.
- Persons treated for lung cancer (C33-C34) by district of residence and age group: National Health Insurance Service, regional medical care utilization statistics, 2011-2024.
- Population by sex and 5-year age group: Ministry of the Interior and Safety, resident registration statistics. The 2023 age block of Changwon duplicated the 2022 block and was corrected (`population_override` in the sets files).
- District covariates: Community Health Survey (smoking, walking, moderate-to-vigorous physical activity), National Health Insurance Service screening statistics (previous pulmonary tuberculosis), regional medical care statistics (out-of-district outpatients) and cancer screening program statistics (uptake), Korea Power Exchange generator capacity (coal-fired plants), national land-use statistics (factory land), register-based census (detached-house households), the public sports facility register, Korean Statistical Information Service local indicators, and a harmonized public district panel (general hospitals, basic livelihood security recipients, tertiary education).

## Pipeline

Run from the repository root (set `ST_DATA_ROOT` and `ST_FBDZIP_CORRECTED` to the local copies of the public source files). All R scripts run single-threaded through `01_스크립트/rslot.sh`.

| Step | Script | Output |
|---|---|---|
| 1 | `99R_next5b_extract_E13.py`, `99R_next5b_mort_counts.py`, `99R_next5b_mort_E.py` | District deaths by cause (code-table join) |
| 2 | `39_build_Estd_fine.py`, `99b_extra_canonical_pool.py`, `99c_covariates_exposure.py`, `99c_covariates_care_ses.py`, `99c_extra_canonical_pool_lcad.py` | Treatment ratio and covariates joined by district code, with correction of implausible recipient-share values |
| 3 | `39m_lcad.py`, `39ms_lcad.py` (wrapping `39m_build_Estd_mort.py`, `39ms_build_Esex_mort.py`), `99E_build_Emtr_lcad.py` | Sex- and age-standardized expected deaths and the offset file (expected deaths × treatment ratio) |
| 4 | `80_build_disease_panel_v.py` | Analytic panel (3,206 district-years) |
| 5 | `81_fit_inla.R` | Likelihood choice, principal model, 200 covariate subsets, window models, residual spatial effects |
| 6 | `85_window_maps.R`, `86_yearly_maps_ehsa.py`, `86b_ehsa_modified_mk.py`, `87_window_grid.py` | Window maps and emerging hot spot analysis |
| 7 | `88g_sens_prep.py`, `88g_sens_suite.R`, `88h_ppc_varpart.R`, `88k_struct_kh.R`, `kh_constraints.R`, `89g_sens_combine.py` | Alternative specifications, comparison outcomes, Knorr-Held interactions, checks and summaries |
| 8 | `04_분석/LCAD/MS/build/run_all_jto.sh` | Manuscript numbers, tables, figures and Supplemental Data 1 |

The full chain is `04_분석/LCAD/run_std3_chain.sh`.

## Software

R 4.6.0 with R-INLA; Python 3.9 (pandas, numpy, scipy, geopandas, matplotlib, python-docx).

## License

MIT (see `LICENSE`).
