# Practice 5 - Cleaning, Normalization and Publication

Practice 5 defines how extracted PDF/article records, MOFX-DB records, and NIST ISODB records should be cleaned and published without creating one very wide table full of missing values.

The final publication layout should use two primary tables:

- `data/processed/mof_materials.csv` - one row per MOF material identity.
- `data/processed/adsorption_measurements.csv` - one row per adsorption measurement point.

The normalized layout is preferred scientifically because one MOF can have many adsorption measurements at different gases, temperatures, pressures, and sources. Keeping material descriptors in every measurement row would repeat the same formula, pore size, surface area, and linker many times.

The flat `data/processed/dataset.csv` remains only a compatibility/export table for the original repository template. It should not be treated as the main analytical format.

## Input Files

- `data/extracted/pdf_extracted_records.csv`
- `data/extracted/web_extracted_records.csv`
- `data/interim/merged_records.csv`
- `specs/dataset_schema.json`
- `specs/mof_materials_schema.json`
- `specs/adsorption_measurements_schema.json`
- `specs/source_map.json`

Preview files under `data/extracted/pdf_parse_preview/` are not automatically included in the final dataset. They contain candidate PDF/table/figure extraction results that still require manual verification.

Preview web files under `data/extracted/web_parse_preview/` are also not automatically included in the final dataset. They are used to design and test the schema before promoting records.

## Source Field Comparison

The preview parsers show that the three source families have different levels of material metadata:

| Field group | Articles/PDFs | MOFX-DB | NIST ISODB mirror | Final location |
|-------------|---------------|---------|-------------------|----------------|
| MOF name or material label | yes | yes | yes | both tables: `mof_id` link, name in material table |
| Gas identity | yes | yes | yes | `adsorption_measurements.csv` |
| Temperature and unit | yes | yes | yes | `adsorption_measurements.csv` |
| Pressure and unit | yes | yes | yes | `adsorption_measurements.csv` |
| Capacity value and unit | yes | yes | yes | `adsorption_measurements.csv` |
| DOI/source URL | yes | yes | yes | `adsorption_measurements.csv` |
| Figure/table/isotherm locator | yes | yes | yes | `adsorption_measurements.csv` as `source_location`/`isotherm_id` |
| Formula | often yes | derived from CIF | often missing | `mof_materials.csv` |
| Metal node/linker | often manually extractable | partially derivable | often missing | `mof_materials.csv` |
| Pore size/surface area/pore volume | sometimes yes | yes | often missing | `mof_materials.csv` |
| MOFid/MOFkey/topology/CSD refcode | rare | yes | usually missing | `mof_materials.csv` |

The robust intersection for a measurement record is therefore:

- `record_id`
- `mof_id`
- `gas_type`
- `temperature`
- `temperature_unit`
- `pressure`
- `pressure_unit`
- `capacity_value`
- `capacity_unit`
- `source_id`
- `extraction_confidence`

Optional but useful measurement fields are retained when available:

- `gas_name`
- `measurement_type`
- `isotherm_id`
- `DOI`
- `publication_year`
- `source_type`
- `source_database`
- `source_url`
- `source_location`
- `extraction_method`
- `notes`

## Final Dataset Organization

The final dataset should be treated as two related tables:

| Table | One row means | Key fields |
|-------|---------------|------------|
| `mof_materials.csv` | one MOF material identity | `mof_id`, `MOF_name`, `chemical_formula`, `metal_node`, `organic_linker`, `pore_size`, `surface_area_BET`, `MOFid`, `MOFkey`, `source_material_id` |
| `adsorption_measurements.csv` | one gas adsorption measurement | `record_id`, `mof_id`, `gas_type`, `temperature`, `pressure`, `capacity_value`, `capacity_unit`, `source_id`, `source_location` |

This avoids repeating formula, metal node, linker, pore size, surface area, and pore volume for every pressure point from the same isotherm. The flat `dataset.csv` remains useful for simple inspection and for compatibility with the course template.

## Measurement Table

The measurement table should contain only fields that describe a single adsorption result and the provenance of that result.

Core columns:

| Column | Reason |
|--------|--------|
| `record_id` | unique row identifier |
| `mof_id` | link to the MOF material table |
| `gas_type`, `gas_name` | adsorbate identity |
| `temperature`, `temperature_unit` | experimental condition |
| `pressure`, `pressure_unit` | experimental condition |
| `capacity_value`, `capacity_unit` | adsorption result |
| `measurement_type` | distinguishes capacity, working capacity, selectivity, etc. |
| `isotherm_id` | groups points from the same graph/isotherm |
| `DOI`, `publication_year` | publication provenance |
| `source_id`, `source_type`, `source_database`, `source_url` | source provenance |
| `source_location` | generic page/table/figure/API locator |
| `extraction_method`, `extraction_confidence`, `notes` | extraction audit trail |

Fields such as `chemical_formula`, `metal_node`, `organic_linker`, `pore_size`, `surface_area_BET`, and `pore_volume` do not belong in this table because they describe the MOF, not the measurement.

## MOF Materials Table

The material table should contain one row per distinct MOF identity. It should absorb all descriptors that would otherwise create repeated or sparse measurement columns.

Core columns:

| Column | Reason |
|--------|--------|
| `mof_id` | internal stable identifier |
| `MOF_name` | reported or normalized material name |
| `chemical_formula` | formula from article, database, or CIF |
| `metal_node` | required material descriptor for analysis when available |
| `organic_linker` | required material descriptor for analysis when available |
| `pore_size`, `pore_size_unit` | structural descriptor |
| `surface_area_BET`, `surface_area_BET_unit` | adsorption-relevant material descriptor |
| `pore_volume`, `pore_volume_unit` | adsorption-relevant material descriptor |
| `molecular_weight`, `molecular_weight_unit` | useful for unit conversion |
| `topology`, `CSD_refcode`, `MOFid`, `MOFkey` | identity-resolution fields |
| `source_material_id`, `source_id`, `source_url` | source-specific material provenance |
| `notes` | aliases or missing-descriptor caveats |

Some fields will be missing for NIST ISODB because the mirror often stores adsorbent names and hashkeys but not full structural descriptors. This is acceptable in the material table; it is better than creating repeated empty columns in every NIST measurement row.

## Cleaning Steps

The cleaning pipeline is defined in `specs/cleaning_pipeline.json` and implemented in `scripts/build_dataset.py` and `scripts/clean_dataset.py`.

1. **Merge sources:** concatenate PDF and web extraction tables into `data/interim/merged_records.csv`.
2. **Standardize units:** keep all numerical values paired with explicit unit columns, e.g. `capacity_value` + `capacity_unit`, `pressure` + `pressure_unit`, `pore_size` + `pore_size_unit`.
3. **Standardize MOF identity:** use `mof_id`, `MOF_name`, formula, metal node, linker, pore size, CSD refcode, topology, MOFid/MOFkey, and notes to distinguish materials.
4. **Normalize missing values:** map `NA`, `N/A`, `-`, empty strings, `null`, and `nan` to null-like values during cleaning.
5. **Deduplicate records:** remove duplicate `record_id` values and then inspect potential duplicates with identical MOF, gas, condition, capacity, and source metadata.
6. **Create generic source locators:** map PDF-specific `pdf_id`, `page`, `table_or_figure`, figure digitization metadata, and API-specific `articleSource` values into `source_location` and `extraction_method`.
7. **Export final tables:** write the flat compatibility table and the normalized material/measurement tables.
8. **Validate:** run `scripts/validate_project.py`.

## Normalization Rules

- **Units are never implicit.** Every numerical physical value has a unit column.
- **No automatic unit conversion is applied yet.** Raw reported units are preserved until a reviewed conversion table is added.
- **Temperature and pressure remain as reported.** For example, `25 C`, `273 K`, `1 atm`, and `1 bar` should not be silently merged.
- **Working capacity is not the same as a single adsorption point.** Pressure ranges such as `100 to 5 bar` should remain explicitly marked as working-capacity records or be excluded from point-isotherm analysis.
- **MOF identity requires more than a name.** A material record should include formula, metal node, organic linker, pore size, and, where possible, CSD refcode, MOFid/MOFkey, topology, or CIF-derived identifiers.
- **Source-specific columns should be collapsed.** Use `source_location` instead of separate `pdf_id`, `page`, `figure`, `table_or_figure`, and `articleSource` columns in the final measurement table.

## Deduplication Strategy

Primary duplicate key:

- `record_id`

Secondary review key:

- `mof_id`
- `gas_type`
- `temperature`
- `temperature_unit`
- `pressure`
- `pressure_unit`
- `capacity_value`
- `capacity_unit`
- `source_id`

If the same measurement appears in a PDF, NIST ISODB, MOFX-DB, or a public dataset, the source with clearer provenance, units, and page/table/API identifier should be retained as the primary record. Secondary copies should be documented in `notes` or excluded until conflict resolution is complete.

## Validation Results

Current local validation command:

```bash
py -3 scripts/validate_project.py
```

Current status: validation passes with the dataset still empty by design. The official extracted tables are header-only because candidate PDF and figure extraction results have not yet been manually promoted into the final extraction CSVs.

## Final Dataset Description

Current publication files:

- `data/processed/dataset.csv`: flat export, 0 accepted rows.
- `data/processed/mof_materials.csv`: normalized material table, 0 accepted rows.
- `data/processed/adsorption_measurements.csv`: normalized measurement table, 0 accepted rows.

Candidate data currently exist in preview files only:

- `data/extracted/pdf_parse_preview/uio66_candidate_records.csv`
- `data/extracted/pdf_parse_preview/uio66_figure6_digitized_points.csv`
- `data/extracted/pdf_parse_preview/new_pdf_candidate_records.csv`
- `data/extracted/pdf_parse_preview/manual_visual_digitized_isotherms.csv`
- `data/extracted/web_parse_preview/mofxdb_batch/materials_preview.csv`
- `data/extracted/web_parse_preview/mofxdb_batch/isotherm_points_preview.csv`
- `data/extracted/web_parse_preview/nist_isodb_mirror/materials_preview.csv`
- `data/extracted/web_parse_preview/nist_isodb_mirror/isotherm_points_preview.csv`

These should be reviewed before inclusion.

## Publication Readiness Checklist

- [x] `dataset.csv` matches `specs/dataset_schema.json`
- [x] normalized material and measurement table schemas exist
- [x] PDF and web extraction manifests are MOF-specific
- [x] source map contains current PDF and web candidate sources
- [ ] candidate PDF records reviewed and promoted to `pdf_extracted_records.csv`
- [ ] web source API endpoints and license terms verified
- [ ] unit conversion policy finalized
- [ ] `LICENSE` replaced or confirmed
- [ ] `CITATION.cff` completed
- [ ] `dataset_card.md` updated
- [ ] `reports/final_report.md` complete
