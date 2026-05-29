# MOF-based gas adsorption dataset

This repository contains a reproducible course dataset project for metal-organic frameworks (MOFs) and gas adsorption capacity measurements.

## Scientific task

Collect adsorption measurements for MOF materials and relate gas capacity to material descriptors such as formula, pore size, surface area, and structural identifiers under defined experimental conditions.

## Record definition

One measurement record is one gas adsorption measurement for one MOF material under one defined set of conditions. Most records correspond to one pressure-capacity point from an isotherm.

## Dataset files

| Path | Description |
|---|---|
| `data/processed/mof_materials.csv` | final material table, one row per MOF identity |
| `data/processed/adsorption_measurements.csv` | final measurement table, one row per adsorption point |
| `data/extracted/pdf_parsed_records.csv` | parsed PDF measurement records |
| `data/extracted/pdf_parsed_materials.csv` | parsed PDF material descriptors |
| `data/extracted/web_parsed_records.csv` | parsed web/API measurement records |
| `data/extracted/web_parsed_materials.csv` | parsed web/API material descriptors |

The processed dataset currently contains 541 measurement records and 19 MOF material records. A single wide `dataset.csv` is not published because the normalized two-table design avoids repeated material descriptors and many empty columns.

## Repository structure

| Path | Role |
|---|---|
| `specs/` | schemas, source map, extraction manifests, cleaning pipeline, validation rules |
| `scripts/` | extraction, build, cleaning, and validation scripts |
| `data/raw/` | local PDFs and web/API snapshots used by parsers |
| `data/extracted/` | parsed source-specific outputs |
| `data/interim/` | merged dataset before final cleaning |
| `data/processed/` | final publication tables |
| `reports/` | practice reports and final report |
| `tests/` | regression tests for required artifacts |

## Reproduce the dataset

Install dependencies:

```bash
pip install -r requirements.txt
```

Build and validate the final publication tables:

```bash
py -3 scripts/build_dataset.py
py -3 scripts/clean_dataset.py
py -3 scripts/validate_project.py
py -3 -m pytest
```

Notes:

- `build_dataset.py` joins parsed PDF/web measurements with material descriptors and writes `data/interim/merged_records.csv`.
- `clean_dataset.py` normalizes missing values, deduplicates records, and writes the two processed tables.
- `validate_project.py` checks required files, schema alignment, unique identifiers, source identifiers, and numeric capacity values.
- `extract_pdf.py` and `extract_web.py` document the extraction approach and can be extended for future source expansion; the current release uses the four committed parsed CSV files in `data/extracted/`.

## Sources

Current parsed sources include:

- selected scientific PDFs for UiO-66-NH2, Cu-BTC/GO composites, and NPF-200;
- MOFX-DB JSON records for a small hMOF batch;
- NIST ISODB GitHub API mirror records for a Zr-fum hydrogen storage article.

Full source metadata are listed in `specs/source_map.json`.

## Reports

The five practice reports are in `reports/`:

1. `practice_01_record_and_schema.md`
2. `practice_02_source_map.md`
3. `practice_03_pdf_extraction.md`
4. `practice_04_web_extraction.md`
5. `practice_05_cleaning_publication.md`

The project summary is in `reports/final_report.md`.

## Authorship, license, and citation

Author: Topalova Yaroslavna Romanovna.

Dataset license: CC BY 4.0. See `LICENSE`.

Citation metadata are provided in `CITATION.cff`.
