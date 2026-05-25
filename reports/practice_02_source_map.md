# Practice 2 - Source Map

## Source search strategy

LLMs were used to search for relevant databases. Scientific literature was searched in Google Scholar using the keyword `metal-organic frameworks (MOFs)`.

## Source groups

The machine-readable source map is maintained in `specs/source_map.json`. The current groups are:

- `scientific_papers`: primary articles reporting experimental adsorption measurements.
- `databases`: structured adsorption or crystallographic databases.
- `aggregators`: metadata and search services used to find papers, DOIs, or source metadata.

## Priority sources

| Priority | Source | Reason |
|----------|--------|--------|
| 1 | NIST ISODB | Highest expected yield for adsorption isotherm points; stores pressure, temperature, gas, capacity values, material identifiers, and DOI provenance |
| 2 | Primary scientific papers | Authoritative experimental context; useful for extracting capacity values, measurement conditions, and methodological details |
| 3 | CoRE MOF and CSD | Strong structural metadata, but adsorption capacity values must be linked from other sources |
| 4 | Aggregators | Useful for DOI metadata, literature discovery, and source cross-checking, but not direct adsorption records |

## Access conditions

## Expected data types

| Source type | Expected data |
|-------------|---------------|
| Adsorption databases | JSON/XML/CSV/API records, isotherm point tables, material registry identifiers, DOI references |
| Scientific papers | PDF text, tables, figure captions, methods sections, reported capacity/selectivity values |
| Structural databases | CIF files, CSD refcodes, topology, pore descriptors, surface area/pore volume metadata |
| Aggregators | DOI metadata, publication year, article titles, citation links, publisher landing pages |

## Expected conflicts and overlaps

The same measurement may appear in a primary paper and NIST ISODB. The initial conflict policy is:

- prefer primary papers for experimental values when exact conditions are available;
- prefer NIST ISODB for machine-readable isotherm points when it clearly cites the same DOI and extraction method;
- retain source-specific units and values until cleaning, then document conversions;
- normalize MOF aliases using registry IDs, CSD refcodes, or explicit notes.

Common expected conflicts include:

- unit mismatch: `mmol/g`, `cm3(STP)/g`, `wt%`, `mol/kg`;
- pressure basis mismatch: bar vs Pa vs atm; absolute vs relative pressure;
- MOF aliasing: HKUST-1, CuBTC, MOF-199, Basolite C300;
- rounded temperatures and pressures: 298 K vs 298.15 K; 1 bar vs 1 atm.

## Coverage gaps
