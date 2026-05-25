# Practice 1 - Record Definition and Dataset Schema

## Topic

MOF-based gas adsorption materials.

## Scientific task

The dataset is designed to support analysis of relationships between metal-organic framework (MOF) structure/composition and gas adsorption performance. The main target variables are gas capacity and, where reported, selectivity under defined experimental conditions.

## One-record definition

One record = one gas adsorption measurement for one MOF material under one defined set of experimental conditions.

## Dataset fields

The initial schema is stored in `specs/dataset_schema.json`. Required fields define the minimum reproducible adsorption point:

| Field | Type | Required | Role |
|-------|------|----------|------|
| `record_id` | string | yes | Stable unique row identifier |
| `MOF_name` | string | yes | Reported or normalized MOF/material name |
| `gas_type` | string | yes | Gas formula, e.g. CO2, CH4, N2 |
| `temperature` | number | yes | Measurement temperature |
| `pressure` | number | yes | Measurement pressure |
| `capacity_value` | number | yes | Numeric adsorption capacity |
| `capacity_unit` | string | yes | Unit as normalized or reported |
| `source_id` | string | yes | Link to `specs/source_map.json` |

Optional material descriptors include metal node, organic linker, formula, CSD refcode, topology, BET surface area, pore volume, and pore size. Optional experimental/provenance fields capture activation, method, original source, extraction confidence, and notes.

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
