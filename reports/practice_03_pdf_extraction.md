# Practice 3 - PDF Extraction

> PDF-only parsed output: `data/extracted/pdf_parsed_records.csv`  
> PDF-only material output: `data/extracted/pdf_parsed_materials.csv`

## Selected PDF Sources

| source_id | Title | Year | DOI | Access |
|---|---|---:|---|---|
| `paper_uio66_nh2_sonochemical_2023` | Enhanced CO2 capture potential of UiO-66-NH2 synthesized by sonochemical method | 2023 | `10.1038/s41598-023-47221-6` | open access |
| `paper_nanosized_cu_mofs_go_gas_storage` | Nanosized Cu-MOFs induced by graphene oxide and enhanced gas storage capacity | 2013 | `10.1039/c3ee23421e` | local PDF |
| `paper_nihms_1670563` | Optimization of the Pore Structures of MOFs for Record High Hydrogen Volumetric Working Capacity | 2020 | `10.1002/adma.201907995` | local PDF |

## Why These PDFs Were Selected

These papers contain experimental gas adsorption data for MOF materials and include the key fields needed for the dataset: MOF name, gas type, temperature, pressure, capacity value, capacity unit, and source location. The selected PDFs also provide material descriptors such as metal node, linker, pore size, BET surface area, and pore volume.

## Pages Used

**paper_uio66_nh2_sonochemical_2023**

- Page 6: Figure 6 and nearby text - CO2 capacity for UiO-66-NH2 at 25 C and 1 bar.
- Page 6: text paragraph - high-pressure CO2 capacity at 20 bar, referring to supplementary Fig. S1.
- Page 6: Figure 6 plot - digitized CO2/N2 isotherm points at 25 C and 50 C.
- Page 7: table with Langmuir/Freundlich model parameters - inspected as context, not used as direct capacity points.
- Page 8: kinetic model table - inspected as context, not used as direct capacity points.

**paper_nanosized_cu_mofs_go_gas_storage**

- Page 4: Table 1 - H2 capacity at 77 K and 42 atm; CO2 capacity at 273 K and 1 atm for Cu-BTC, CG-3, CG-9, and CG-15.
- Figure 6 (`Cu-MOF_GO_Fig6_CO2_273K`) - digitized CO2 isotherm points at 273 K.
- Figure 7 (`Cu-MOF_GO_Fig7_H2_77K`) - digitized H2 isotherm points at 77 K.
- Figure 8 (`Cu-MOF_GO_Fig8_CG9_273K`) - digitized CG-9 points for CO2, CH4, and N2 at 273 K.

**paper_nihms_1670563**

- Page 6: text paragraph - NPF-200 H2 total adsorption at 77 K and 100 bar.
- Page 6: text paragraph - NPF-200 H2 working capacities between 100 and 5 bar.
- Figure 3b (`NPF-200_Fig3b_H2_77K`) - digitized total and excess H2 isotherm points at 77 K.

## Extraction Method

Tools used: **pdfplumber/PyMuPDF-style text extraction**, manual table transcription, and manual/visual figure digitization.

Current parsing logic:

- Text paragraphs are used when the paper explicitly states a capacity value with pressure, temperature, and units.
- Tables are used when rows contain material names and numeric adsorption capacities.
- Figures are digitized only when the isotherm data are shown as plots without machine-readable tables.
- Each extracted row keeps a `source_location` value such as `page=4; table_or_figure=Table 1` or `figure=Cu-MOF_GO_Fig6_CO2_273K`.

## Extracted Fields Mapping

**`data/extracted/pdf_parsed_records.csv`**

| Column | Source in PDF |
|---|---|
| `MOF_name` | sample name in text, table, or figure label |
| `gas_type` | table heading, figure legend, or paragraph text |
| `temperature`, `temperature_unit` | table heading, figure caption, paragraph text |
| `pressure`, `pressure_unit` | table heading, x-axis, or paragraph text |
| `capacity_value`, `capacity_unit` | table cell, paragraph text, or digitized y-axis value |
| `DOI`, `publication_year` | paper first page or article metadata |
| `source_id`, `source_url` | source manifest |
| `source_location` | page number, table number, figure number, or plot series |
| `extraction_method` | `pdf_table`, `digitized_figure`, or `pdf_preview` |
| `notes` | caveats about digitization, supplementary figures, or manual verification |

**`data/extracted/pdf_parsed_materials.csv`**

| Column | Source in PDF |
|---|---|
| `MOF_name` | sample name in text, table, or figure label |
| `chemical_formula` | article text, table, or manually verified candidate extraction |
| `metal_node` | article text, known MOF chemistry, or manually verified candidate extraction |
| `organic_linker` | article text, known MOF chemistry, or manually verified candidate extraction |
| `pore_size`, `pore_size_unit` | characterization table/text |
| `surface_area_BET`, `surface_area_BET_unit` | characterization table/text |
| `pore_volume`, `pore_volume_unit` | characterization table/text |
| `source_id`, `source_url` | source manifest |
| `notes` | material identity caveats |

## Extraction Problems

| Problem | Affected records | Resolution |
|---|---:|---|
| Figure digitization is approximate | 203 records | Keep `extraction_method = digitized_figure`; require manual verification before final promotion |
| Some digitized Figure 6 N2 points have empty `capacity_value` | 5 records | Keep in preview; inspect graph/digitizer before final promotion |
| PDF figure points may not contain full gas/material metadata in the source row | figure-derived rows | Reconstruct `MOF_name`, `source_id`, and `source_location` during preview table building |
| NPF-200 working capacity uses a pressure range (`100 to 5 bar`) | 2 records | Keep pressure as text range; do not mix with single-point isotherm records |
| GO appears as a control/support material in the Cu-MOF/GO figure | 11 records | Exclude GO from the PDF-only MOF dataset because it is not a MOF material |
| Model/kinetic tables are not direct adsorption capacity records | UiO-66 pages 7-8 | Mention as inspected context, but do not promote as measurement rows |

## Output Files

| File | Records | Notes |
|---|---:|---|
| `data/extracted/pdf_parsed_records.csv` | 212 | PDF-only parsed measurement records |
| `data/extracted/pdf_parsed_materials.csv` | 6 | PDF-only parsed material records |
| `data/raw/pdf/uio66_nh2_sonochemical_2023.pdf` | - | source PDF |
| `data/raw/pdf/nanosized_cu_mofs_go_gas_storage.pdf` | - | source PDF |
| `data/raw/pdf/nihms_1670563.pdf` | - | source PDF |
