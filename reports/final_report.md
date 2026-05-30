# Final Report

## Project Summary

This project builds a structured dataset of gas adsorption measurements for metal-organic frameworks (MOFs). The dataset links adsorption capacity points with gas type, pressure, temperature, source provenance, and available MOF material descriptors.

## Dataset Goal

The dataset supports exploratory analysis of how MOF composition and structure relate to gas adsorption capacity under defined measurement conditions.

## Sources

Current parsed sources include:

- three scientific PDF sources for UiO-66-NH2, Cu-BTC/GO composites, and NPF-200;
- MOFX-DB JSON records for a small hMOF batch;
- NIST ISODB GitHub API mirror records for Zr-fum hydrogen adsorption.

Full source metadata are documented in `specs/source_map.json`.

## Extraction Summary

PDF extraction produced 212 measurement records and 6 material records. Web/API extraction produced 329 measurement records and 13 material records. The final processed dataset contains 541 measurement records and 19 MOF material records.

## Cleaning And Normalization

The final dataset is built by joining parsed measurement rows with material descriptor rows. Units are preserved as reported and stored in explicit unit columns. Duplicate `record_id` values are removed during cleaning.

Final normalized outputs:

- `data/processed/adsorption_measurements.csv`
- `data/processed/mof_materials.csv`
- `data/processed/dataset.csv`

The normalized two-table layout is the main publication format. `dataset.csv` is retained as a flat compatibility export for validators and quick preview.

## Validation

`scripts/validate_project.py` passes. The validation checks required files, schema alignment, unique identifiers, valid source identifiers, material-measurement links, and numeric capacity values.

## Limitations

- Some PDF values come from figure digitization.
- Some material descriptors are incomplete, especially for NIST ISODB records.
- No automatic unit conversion is applied.
- Upstream source licenses should be checked before reuse outside the course project.

## Final Artifacts

| Artifact | Path |
|---|---|
| Measurement table | `data/processed/adsorption_measurements.csv` |
| Material table | `data/processed/mof_materials.csv` |
| Flat compatibility dataset | `data/processed/dataset.csv` |
| Measurement schema | `specs/adsorption_measurements_schema.json` |
| Material schema | `specs/mof_materials_schema.json` |
| Source map | `specs/source_map.json` |
| Dataset card | `dataset_card.md` |
| Citation | `CITATION.cff` |
| License | `LICENSE` |
