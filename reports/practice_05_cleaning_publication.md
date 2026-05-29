# Practice 5 - Cleaning, Normalization and Publication

> Pipeline: `specs/cleaning_pipeline.json`  
> Scripts: `scripts/build_dataset.py`, `scripts/clean_dataset.py`, `scripts/validate_project.py`

## Input Files

| File | Rows | Role |
|---|---:|---|
| `data/extracted/pdf_extracted_records.csv` | 0 | accepted PDF records, header-only for now |
| `data/extracted/web_extracted_records.csv` | 0 | accepted web records, header-only for now |
| `data/extracted/pdf_parsed_records.csv` | 212 | parsed PDF measurement records |
| `data/extracted/pdf_parsed_materials.csv` | 6 | parsed PDF material descriptors |
| `data/extracted/web_parsed_records.csv` | 329 | parsed web measurement records |
| `data/extracted/web_parsed_materials.csv` | 13 | parsed web material descriptors |
| `data/interim/merged_records.csv` | 541 | merged final records |

The final build uses the parsed PDF and web tables as the current accepted dataset release.

## Final Table Design

| Table | One row means | Main content |
|---|---|---|
| `data/processed/adsorption_measurements.csv` | one adsorption measurement point | gas, temperature, pressure, capacity, units, DOI/source |
| `data/processed/mof_materials.csv` | one MOF material identity | name, formula, pore descriptors, surface area, identifiers |
| `data/processed/dataset.csv` | flat compatibility export | wide schema used by the repository |

The normalized two-table design is preferred because one MOF can have many measurements. Material descriptors should not be repeated in every pressure point.

## Cleaning Steps

| Step | Action |
|---|---|
| 1 | Join parsed measurement records with MOF material descriptors |
| 2 | Keep every numeric value paired with a unit column |
| 3 | Normalize MOF identity using name, formula, pore descriptors, source identifiers, MOFid/MOFkey when available |
| 4 | Collapse source-specific locators into `source_location` and `extraction_method` |
| 5 | Standardize missing values: empty string, `NA`, `N/A`, `null`, `nan`, `-` |
| 6 | Deduplicate accepted records |
| 7 | Export flat and normalized processed tables |
| 8 | Validate schema and source references |

## Normalization Rules

| Rule | Decision |
|---|---|
| Units | no implicit units; preserve reported units |
| Unit conversion | not applied yet; needs reviewed conversion table |
| Capacity | use `capacity_value` + `capacity_unit` |
| Pressure | use `pressure` + `pressure_unit` |
| Temperature | use `temperature` + `temperature_unit` |
| MOF descriptors | store in `mof_materials.csv`, not in measurement records |
| NIST ISODB | use mainly for isotherm points and DOI provenance; structural enrichment is future work |

## Deduplication Strategy

Primary key:

- `record_id`

Secondary review key:

- `MOF_name`
- `gas_type`
- `temperature`
- `temperature_unit`
- `pressure`
- `pressure_unit`
- `capacity_value`
- `capacity_unit`
- `source_id`
- `source_url`

If the same measurement appears in multiple sources, keep the version with clearer units, DOI, and source location.

## Validation Results

Command:

```bash
py -3 scripts/validate_project.py
```

Result: validation passed.

Current final dataset is built from parsed PDF and web records.

## Final Dataset Description

| File | Rows | Status |
|---|---:|---|
| `data/processed/dataset.csv` | 541 | valid flat export |
| `data/processed/mof_materials.csv` | 19 | valid normalized material table |
| `data/processed/adsorption_measurements.csv` | 541 | valid normalized measurement table |

Candidate data available for review:

| File | Rows |
|---|---:|
| `data/extracted/pdf_parsed_records.csv` | 212 |
| `data/extracted/pdf_parsed_materials.csv` | 6 |
| `data/extracted/web_parsed_records.csv` | 329 |
| `data/extracted/web_parsed_materials.csv` | 13 |

## Publication Readiness Checklist

- [x] `dataset.csv` matches `specs/dataset_schema.json`
- [x] `mof_materials.csv` schema exists
- [x] `adsorption_measurements.csv` schema exists
- [x] PDF and web parsed outputs are separated
- [x] Validation script passes
- [x] parsed PDF records promoted into processed dataset
- [x] parsed web records promoted into processed dataset
- [ ] unit conversion policy finalized
- [ ] source licenses checked before publication
- [ ] `dataset_card.md` updated
- [ ] final report completed
