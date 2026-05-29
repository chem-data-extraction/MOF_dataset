# Practice 4 - Web Extraction

Practice 4 documents the first web/API extraction probe for two MOF-relevant databases:

- MOFX-DB: `https://mof.tech.northwestern.edu/`
- NIST ISODB: `https://adsorption.nist.gov/isodb/index.php#home`

The goal of this practice is not to mass-download records yet, but to determine whether these web sources can support the schema and what parsing strategy is needed. Web parsing outputs are kept as a web-only dataset in `data/extracted/web_parsed_records.csv` and `data/extracted/web_parsed_materials.csv`; they are not merged with PDF outputs in Practice 4.

## Selected Web Sources

| source_id | page_id | URL | Probe result |
|-----------|---------|-----|--------------|
| `db_mofxdb` | `mofxdb_home` | `https://mof.tech.northwestern.edu/` | JSON API probe works through `/mofs.json?page=1` |
| `db_nist_isodb` | `nist_isodb_home` | `https://adsorption.nist.gov/isodb/index.php#home` | Web snapshot works; official GitHub API mirror provides parseable JSON |

## Why These Sites Were Selected

MOFX-DB was selected because it exposes MOF structures, pore descriptors, MOF identifiers, and isotherm metadata through a JSON endpoint. It is useful for testing the material table design and for discovering how MOF identifiers, pore descriptors, gases, pressure, temperature, and capacity values may appear in structured web data.

NIST ISODB was selected because it is the most relevant target for experimental adsorption isotherms. It is expected to provide adsorbent names, adsorbates, pressure, temperature, capacity values, units, and literature provenance. The current probe downloaded the web app shell; additional endpoint mapping is needed before reliable record extraction.

NIST also provides an official GitHub mirror of the API output at `https://github.com/NIST-ISODB/isodb-library`. This mirror is organized as static JSON files for adsorbates, adsorbents, bibliography records, and isotherms. It is therefore a practical extraction route when the web application endpoint itself returns only the app shell.

## Page Structure

MOFX-DB has an API-like structure. The probe request `GET https://mof.tech.northwestern.edu/mofs.json?page=1` returned JSON with pagination metadata and MOF result objects. A result object may include MOF name, CIF text, `lcd`, `pld`, MOFid/MOFkey, database name, elements, isotherm links, isotherm data, pressure units, adsorption units, adsorbate metadata, temperature, DOI, and force-field metadata.

NIST ISODB behaves as a web application. The requested `/isodb/api` route returned an HTML page with the NIST disclaimer and app shell rather than direct JSON records. The GitHub API mirror solves this for parsing because it exposes the same API JSON as repository files under `Library/`.

## Extraction Methods

The current parser in `scripts/extract_web.py` performs small source probes only:

1. Read source definitions from `specs/web_extraction_manifest.json`.
2. Download web snapshots into `data/raw/web/`.
3. Download API probe responses when `api_probe_url` is available.
4. Download selected MOFX-DB detail JSON records and linked isotherm JSON files for preview extraction.
5. Download selected NIST GitHub mirror bibliography, adsorbent, adsorbate, and isotherm JSON files.
6. Write a compact probe summary to `data/extracted/web_probe_summary.json`.
7. Collect parser outputs into the web-only preview dataset `data/extracted/web_parsed_records.csv` and `data/extracted/web_parsed_materials.csv`.
8. Keep `data/extracted/web_extracted_records.csv` header-only until record-level extraction is verified.

This conservative design avoids mixing unverified simulated/computational records with the experimental PDF-derived records.

## MOFX-DB Detail Preview

A small MOFX-DB batch preview was implemented for the first 10 MOF records with linked isotherms on page 1 of the API response. The parser downloads each MOF detail JSON, follows its `isotherm_url` links, and converts the plotted isotherm points into a tabular preview.

Preview output:

- `data/extracted/web_parse_preview/mofxdb_batch/materials_preview.csv` - 10 MOF material rows.
- `data/extracted/web_parse_preview/mofxdb_batch/isotherm_points_preview.csv` - 210 isotherm point rows.

The parsed preview includes `hMOF-6`, `hMOF-0`, `hMOF-7`, `hMOF-5`, `hMOF-3`, `hMOF-4`, `hMOF-1`, `hMOF-2`, `hMOF-8`, and `hMOF-9`. Gases observed in this preview are `CO2`, `N2`, `CH4`, `H2`, `Xe`, and `Kr`. Units observed include `mol/kg`, `g/l`, and `cm3(STP)/cm3`.

These rows are not promoted to the final dataset yet because MOFX-DB source terms and experimental/computational origin still need final review.

## NIST ISODB GitHub Mirror Preview

A first NIST mirror preview was implemented using the official repository `https://github.com/NIST-ISODB/isodb-library`. The parser downloads one DOI directory from the mirror, plus the linked bibliography, adsorbent, and adsorbate metadata files.

Preview DOI:

- `10.1016/j.ijhydene.2015.06.109` - "Hydrogen storage in Zr-fumarate MOF"

Preview output:

- `data/extracted/web_parse_preview/nist_isodb_mirror/materials_preview.csv` - 3 adsorbent material rows.
- `data/extracted/web_parse_preview/nist_isodb_mirror/isotherm_points_preview.csv` - 119 isotherm point rows from 5 isotherm JSON files.

The parsed rows contain hydrogen adsorption data for Zr-fum MOF variants at 77 K. Units observed in this preview are `cm3(STP)/g` and `wt%`, with pressure in `bar`. The NIST JSON explicitly marks the sampled records as `category=exp`, which makes this source especially useful for the experimental-only dataset design.

## Extracted Fields

No accepted web records were written yet. Candidate fields observed in the MOFX-DB JSON include:

| Web field | Candidate dataset field |
|-----------|-------------------------|
| `name`, `mofid`, `mofkey` | `mof_id`, `MOF_name`, `notes` |
| `lcd`, `pld` | `pore_size`, `pore_size_unit` |
| `elements`, `cif` | `chemical_formula`, `metal_node`, `organic_linker` after additional parsing |
| `adsorbates[].formula` | `gas_type` |
| `temperature` | `temperature`, `temperature_unit` |
| `isotherm_data[].pressure` | `pressure`, `pressure_unit` |
| `isotherm_data[].total_adsorption` | `capacity_value`, `capacity_unit` |
| `DOI`, `doi_url` | `DOI`, `source_url` |

## Extraction Problems

- MOFX-DB contains structured records, but many entries include simulation metadata and force-field information; experimental-only filtering must be explicit.
- Some MOFX-DB fields have ambiguous units or unexpected unit labels, so unit verification is required before accepting rows.
- NIST ISODB did not expose direct JSON records through the first probed web URL, but the official GitHub mirror provides parseable JSON files.
- NIST adsorbent metadata may have missing chemical formula or structural descriptors, so it should be joined with external material information before final publication.
- MOF identity cannot rely only on a display name. MOFid, MOFkey, CIF-derived formula, pore descriptors, and source metadata should be used for identity resolution.
- Bulk downloads should wait until license, source terms, and accepted-use constraints are reviewed.

## Output Files

- `specs/web_extraction_manifest.json`
- `data/extracted/web_extracted_records.csv` - header-only, no accepted web records yet.
- `data/extracted/web_parsed_records.csv` - web-only parsed measurement preview dataset.
- `data/extracted/web_parsed_materials.csv` - web-only parsed material preview dataset.
- `data/extracted/web_probe_summary.json`
- `data/extracted/web_parse_preview/mofxdb_batch/materials_preview.csv`
- `data/extracted/web_parse_preview/mofxdb_batch/isotherm_points_preview.csv`
- `data/extracted/web_parse_preview/nist_isodb_mirror/materials_preview.csv`
- `data/extracted/web_parse_preview/nist_isodb_mirror/isotherm_points_preview.csv`
- `data/raw/web/mofxdb_home.html`
- `data/raw/web/mofxdb_mofs_page1.json`
- `data/raw/web/mofxdb_batch/`
- `data/raw/web/nist_isodb_mirror/`
- `data/raw/web/nist_isodb_home.html`
- `data/raw/web/nist_isodb_api_probe.html`
- `data/extracted/extraction_log.jsonl`
