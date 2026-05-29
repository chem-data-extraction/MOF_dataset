# Practice 5 - Cleaning, Normalization and Publication

> Pipeline: `specs/cleaning_pipeline.json`  
> Scripts: `scripts/build_dataset.py`, `scripts/clean_dataset.py`, `scripts/validate_project.py`

## Input Files

| File | Rows | Role |
|---|---:|---|
| `data/extracted/pdf_parsed_records.csv` | 212 | parsed PDF measurement records |
| `data/extracted/pdf_parsed_materials.csv` | 6 | parsed PDF material descriptors |
| `data/extracted/web_parsed_records.csv` | 329 | parsed web measurement records |
| `data/extracted/web_parsed_materials.csv` | 13 | parsed web material descriptors |
| `data/interim/merged_records.csv` | 541 | merged intermediate records |

## Final Table Design

| Table | One row means | Main content |
|---|---|---|
| `data/processed/adsorption_measurements.csv` | one adsorption measurement point | gas, temperature, pressure, capacity, units, DOI/source |
| `data/processed/mof_materials.csv` | one MOF material identity | name, formula, metal/linker, pore descriptors, surface area |

The normalized two-table design is preferred because one MOF can have many measurements. A wide `dataset.csv` is not published because it would repeat material descriptors and introduce many empty columns.

## Cleaning Steps

| Step | Action |
|---|---|
| 1 | Join parsed measurement records with MOF material descriptors |
| 2 | Keep every numeric value paired with a unit column |
| 3 | Normalize MOF identity using name, formula, metal/linker, pore descriptors, and source identifiers |
| 4 | Collapse source-specific locators into `source_location` and `extraction_method` |
| 5 | Standardize missing values: empty string, `NA`, `N/A`, `null`, `nan`, `-` |
| 6 | Deduplicate records by `record_id` |
| 7 | Export normalized processed tables |
| 8 | Validate schemas and source references |

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

Primary key: `record_id`.

Secondary review key: `MOF_name`, `gas_type`, `temperature`, `pressure`, `capacity_value`, `capacity_unit`, `source_id`, and `source_url`.

If the same measurement appears in multiple sources, keep the version with clearer units, DOI, and source location.

## Validation Results

Command:

```bash
py -3 scripts/validate_project.py
```

Result: validation passed.

## Final Dataset Description

| File | Rows | Status |
|---|---:|---|
| `data/processed/mof_materials.csv` | 19 | valid normalized material table |
| `data/processed/adsorption_measurements.csv` | 541 | valid normalized measurement table |

## Publication Readiness Checklist

- [x] `mof_materials.csv` matches `specs/mof_materials_schema.json`
- [x] `adsorption_measurements.csv` matches `specs/adsorption_measurements_schema.json`
- [x] PDF and web parsed outputs are separated
- [x] Validation script passes
- [x] Dataset card updated
- [x] Final report completed
- [ ] unit conversion policy finalized
- [ ] source licenses checked before reuse outside the course project
