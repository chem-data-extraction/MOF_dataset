# Practice 4 - Web Extraction

> Parsed measurement output: `data/extracted/web_parsed_records.csv`  
> Parsed material output: `data/extracted/web_parsed_materials.csv`  
> Manifest: `specs/web_extraction_manifest.json`

## Selected Web Sources

| source_id | page_id | URL | Records |
|---|---|---|---|
| `db_mofxdb` | `mofxdb_page1_first10_with_isotherms` | `https://mof.tech.northwestern.edu/mofs.json?page=1` | 210 measurement points, 10 materials |
| `db_nist_isodb` | `nist_zr_fum_hydrogen_storage_example` | `https://github.com/NIST-ISODB/isodb-library` | 119 measurement points, 3 materials |

## Why These Sources Were Selected

MOFX-DB was selected because individual MOF records expose material descriptors, MOF identifiers, and linked isotherm JSON files. It is useful for testing how web data can be separated into a material table and an adsorption measurement table.

NIST ISODB was selected because it is a domain-specific adsorption isotherm database with DOI-linked provenance. The website itself behaves as a web application, so the parser uses the official GitHub API mirror, which contains the same JSON output in a stable file structure. In this project, NIST ISODB is treated primarily as a source of isotherm points and source provenance, not as the main source of MOF structural descriptors.

The NIST strategy is still useful: isotherm JSON files are easy to parse and already contain pressure, temperature, adsorption capacity, units, adsorbate information, DOI, and figure/source location. However, MOF structure information is often limited to adsorbent names or hashkeys. A future project version should enrich NIST material rows by using the DOI to find the source paper or by linking the adsorbent to structural databases such as CoRE MOF or CSD.

## Page And API Structure

| Source | Parsed location | Relevant part |
|---|---|---|
| MOFX-DB | `/mofs.json?page=1` | Paginated MOF search results with `id`, `name`, pore descriptors, and isotherm links |
| MOFX-DB | `/mofs/{mofdb_id}.json` | MOF detail JSON with CIF text, `lcd`, `pld`, surface area, and elements |
| MOFX-DB | `/isotherms/{isotherm_id}.json` | Isotherm JSON with adsorbates, temperature, pressure points, capacity values, DOI |
| NIST ISODB | `Library/Bibliography/{doi_stub}.json` | Article metadata and linked adsorbent, adsorbate, and isotherm files |
| NIST ISODB | `Library/{doi_stub}/{isotherm_file}.json` | Isotherm JSON with pressure, temperature, adsorption values, units, category, DOI |
| NIST ISODB | `Library/Adsorbents/{hashkey}.json` | Material metadata such as adsorbent name, synonyms, formula when available |
| NIST ISODB | `Library/Adsorbates/{InChIKey}.json` | Gas metadata used to normalize gas formula/name |

## Extraction Methods

| Source | Tool | Method | Scope |
|---|---|---|---|
| MOFX-DB | `urllib.request` + `json` | Download first API page, parse first 10 MOFs with linked isotherms, write point-level rows | Preview batch |
| NIST ISODB | `urllib.request` + `json` | Download one DOI directory from the official GitHub mirror and parse linked JSON files | Preview batch |
| Both | `scripts/extract_web.py` | Inspect JSON sources and prepare source-specific parsed rows | Web-only parsed datasets |
| NIST DOI enrichment | Planned extension | Use DOI metadata to search for open PDFs or structural sources, then enrich material descriptors when reliable data are available | Future work |

## Extracted Field Mapping

Measurement table: `data/extracted/web_parsed_records.csv`

| Output field | MOFX-DB source | NIST ISODB source |
|---|---|---|
| `MOF_name` | MOF detail `name` | isotherm/adsorbent `name` |
| `gas_type` | `adsorbates[].formula` or species formula | adsorbate metadata `formula` |
| `temperature`, `temperature_unit` | isotherm `temperature`, fixed `K` | isotherm `temperature`, fixed `K` |
| `pressure`, `pressure_unit` | `isotherm_data[].pressure`, `pressureUnits` | `isotherm_data[].pressure`, `pressureUnits` |
| `capacity_value`, `capacity_unit` | species adsorption or total adsorption, `adsorptionUnits` | species adsorption or total adsorption, `adsorptionUnits` |
| `isotherm_id` | isotherm `id` | isotherm filename |
| `DOI`, `publication_year` | isotherm `DOI`; year not available in preview | bibliography `DOI`, `year` |
| `source_url`, `source_location` | isotherm JSON URL; source location usually absent | raw GitHub JSON URL; `articleSource` |
| `extraction_method`, `notes` | `web_api_json`; category/unit caveats | `github_mirror_json`; category/source notes |

Material table: `data/extracted/web_parsed_materials.csv`

| Output field | MOFX-DB source | NIST ISODB source |
|---|---|---|
| `mof_id`, `MOF_name` | internal `mofxdb_{name}`, MOF `name` | NIST hashkey, adsorbent `name` |
| `chemical_formula` | CIF-derived atom count preview | adsorbent `formula` when available |
| `pore_size`, `pore_size_unit` | `pld`, angstrom | not available in current preview |
| `surface_area_BET`, `surface_area_BET_unit` | `surface_area_m2g`, `m2/g` | not available in current preview |
| `source_material_id`, `source_url` | MOFX-DB id and material JSON URL | NIST hashkey and source JSON URL |

## Extraction Problems

| Problem | Source | Current resolution |
|---|---|---|
| Web application route does not directly expose NIST JSON | NIST ISODB website | Use the official GitHub API mirror |
| MOFX-DB includes source-category and force-field metadata that require origin review | MOFX-DB | Keep source notes and units for later review |
| NIST material JSON contains only adsorbent names/hashkeys for the sampled Zr-fum records | NIST ISODB | Store the DOI and use the source article for later material enrichment |
| DOI-linked PDFs are not guaranteed to be openly available | NIST DOI enrichment | Treat DOI-to-PDF lookup as an optional future enrichment step, not as a required parsing dependency |
| MOF identity is not guaranteed by display name alone | Both | Preserve source-specific identifiers such as MOFX-DB id and NIST hashkey in the material table |
| Units differ across sources | Both | Store unit columns next to every numeric measurement |

## Output Files

| File | Rows | Notes |
|---|---:|---|
| `data/extracted/web_parsed_records.csv` | 329 | Clean web measurement table; 210 MOFX-DB + 119 NIST rows |
| `data/extracted/web_parsed_materials.csv` | 13 | Clean web material table; 10 MOFX-DB + 3 NIST rows |

Observed gases in the web measurement preview: `CO2`, `N2`, `CH4`, `H2`, `Xe`, and `Kr`.
