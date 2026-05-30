# Dataset Card - MOF-based gas adsorption dataset

## Dataset title

MOF-based gas adsorption dataset.

## Dataset summary

This dataset contains parsed gas adsorption measurements for metal-organic framework materials. Records include gas identity, temperature, pressure, capacity value, capacity unit, source DOI/URL, and source location. Material descriptors are stored in a separate table where available.

## Scientific task

Support analysis of relationships between MOF structure or composition and gas adsorption capacity under defined conditions.

## Record unit

One row in `data/processed/adsorption_measurements.csv` is one gas adsorption measurement point for one MOF material.

## Dataset structure

| File | Rows | Description |
|---|---:|---|
| `data/processed/adsorption_measurements.csv` | 541 | measurement table |
| `data/processed/mof_materials.csv` | 19 | MOF material table |
| `data/processed/dataset.csv` | 541 | flat compatibility export |

## Data sources

Sources include scientific PDF articles, MOFX-DB, and the NIST ISODB GitHub API mirror. Source metadata and access notes are documented in `specs/source_map.json`.

## Extraction procedure

1. PDF parsing is documented by `scripts/extract_pdf.py` and `specs/pdf_extraction_manifest.json`.
2. Web/API parsing is documented by `scripts/extract_web.py` and `specs/web_extraction_manifest.json`.
3. Parsed source-specific CSV files are stored in `data/extracted/`.
4. Final processed tables are built by `scripts/build_dataset.py` and `scripts/clean_dataset.py`.
5. Validation is performed by `scripts/validate_project.py`.

## Cleaning and normalization

The pipeline preserves reported units instead of applying automatic unit conversion. Every numerical physical value has a paired unit column. Source-specific locators are stored in `source_location`; repeated MOF descriptors are stored in `mof_materials.csv`.

## Known limitations

- Some values come from figure digitization and should be checked against the primary source before quantitative reuse.
- NIST ISODB is useful for isotherm points and DOI provenance, but often lacks full MOF structural descriptors.
- MOFX-DB material identifiers are useful for structure linkage, but source category and reuse terms should be reviewed before larger-scale use.
- No automatic unit conversion is applied in the current release.

## Recommended use

Course project evaluation, reproducible data extraction practice, schema design, and exploratory analysis of MOF gas adsorption records.

## Not recommended use

High-stakes materials screening, publication-grade meta-analysis, or commercial reuse without rechecking source licenses and primary literature.

## License

Released under CC BY 4.0. Upstream source terms should be checked for any redistribution beyond this course project.

## Citation

See `CITATION.cff`.
