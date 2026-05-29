# Practice 1 - Record Definition and Dataset Schema

## Topic

MOF-based gas adsorption materials.

## Scientific task

The dataset is designed to support analysis of relationships between metal-organic framework (MOF) structure/composition and gas adsorption performance. The main target variables are gas capacity and, where reported, selectivity under defined experimental conditions.

## One-record definition

One record = one gas adsorption measurement for one MOF material under one defined set of experimental conditions.

## Dataset fields

The initial schema is stored in `specs/dataset_schema.json`. Required fields define both the adsorption measurement and the core MOF description needed for structure-property analysis:

| Field | Type | Required | Role |
|-------|------|----------|------|
| `record_id` | string | yes | Stable unique row identifier |
| `mof_id` | string | yes | Internal identifier for linking repeated measurements of the same MOF |
| `MOF_name` | string | yes | Reported or normalized MOF/material name |
| `chemical_formula` | string | yes | Reported chemical formula |
| `metal_node` | string | yes | Metal ion, metal cluster, or inorganic building unit |
| `organic_linker` | string | yes | Organic linker or ligand |
| `pore_size` | number | yes | Representative pore size |
| `pore_size_unit` | string | yes | Unit for `pore_size` |
| `gas_type` | string | yes | Gas formula, e.g. CO2, CH4, N2 |
| `temperature` | number | yes | Measurement temperature |
| `temperature_unit` | string | yes | Unit for `temperature` |
| `pressure` | number | yes | Measurement pressure |
| `pressure_unit` | string | yes | Unit for `pressure` |
| `capacity_value` | number | yes | Numeric adsorption capacity |
| `capacity_unit` | string | yes | Unit as normalized or reported |
| `source_id` | string | yes | Link to `specs/source_map.json` |

Optional material descriptors include BET surface area, pore volume, and source-specific material identifiers. Every numerical descriptor has a corresponding unit column, for example `surface_area_BET` + `surface_area_BET_unit` and `pore_volume` + `pore_volume_unit`. Optional experimental/provenance fields capture activation, method, original source, extraction confidence, and notes.

## MOF material table option

If many adsorption records refer to the same MOF at different temperatures and pressures, material descriptors can be normalized into a separate MOF materials table. In that design, the main adsorption table would keep `mof_id`, gas, conditions, capacity, and source fields, while a separate table such as `mof_materials.csv` would store one row per MOF with `mof_id`, `MOF_name`, `chemical_formula`, `metal_node`, `organic_linker`, `pore_size`, surface area, pore volume, and source identifiers.

For the current schema, the material descriptors remain in the main table because they are central to the scientific task and make the first extraction stage easier to validate.

## Valid record examples

| Example | Why it counts |
|---------|---------------|
| UiO-66, CO2, 298 K, 1 bar, capacity = 3.5 mmol/g, source DOI recorded | Single numeric adsorption point with material, gas, pressure, temperature, unit, and provenance |
| HKUST-1, CH4, 298 K, 65 bar, capacity = 180 cm3(STP)/g, source DOI recorded | Single reproducible experimental adsorption point with pressure, temperature, unit, and provenance |

## Non-record examples

| Example | Why it is not a record |
|---------|-------------------------|
| "UiO-66 showed excellent CO2 adsorption properties." | No numeric capacity/selectivity value |
| "High CO2 capacity was observed." | No pressure, temperature, unit, or reproducible measurement |
| A whole figure caption containing an adsorption isotherm | Must be split into one row per digitized pressure-capacity point |
| A CIF file from CoRE MOF or CSD with no adsorption data | Structural metadata only; can enrich records but is not itself an adsorption measurement |

## Ambiguous cases and decisions

- **Single point vs. entire isotherm:** each pressure-capacity point is one record. Points from the same curve share `isotherm_id`.
- **Multiple gases or mixtures:** pure-gas adsorption uses a single gas formula in `gas_type`; mixture/selectivity records should include the gas pair and composition details in `notes`.
- **Units:** store the reported or normalized unit in `capacity_unit`; conversions will be documented in the cleaning pipeline.
- **MOF identity:** a MOF name alone is not sufficient to define one material. A record should be linked to a material definition using at least a stable `mof_id`, reported `MOF_name`, chemical formula, metal node, organic linker, and pore size. When available, synthesis/activation context and source-specific identifiers should be used to distinguish materials with similar names.
