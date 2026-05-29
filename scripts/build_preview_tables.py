#!/usr/bin/env python3
"""Build normalized preview tables from candidate PDF and web parser outputs."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEASUREMENT_SCHEMA = ROOT / "specs/adsorption_measurements_schema.json"
MATERIAL_SCHEMA = ROOT / "specs/mof_materials_schema.json"
PREVIEW_DIR = ROOT / "data/extracted/normalized_preview"
MEASUREMENT_OUTPUT = PREVIEW_DIR / "adsorption_measurements_preview.csv"
MATERIAL_OUTPUT = PREVIEW_DIR / "mof_materials_preview.csv"
PDF_MEASUREMENT_OUTPUT = ROOT / "data/extracted/pdf_parsed_records.csv"
PDF_MATERIAL_OUTPUT = ROOT / "data/extracted/pdf_parsed_materials.csv"
WEB_MEASUREMENT_OUTPUT = ROOT / "data/extracted/web_parsed_records.csv"
WEB_MATERIAL_OUTPUT = ROOT / "data/extracted/web_parsed_materials.csv"
PDF_MATERIAL_EXCLUDED_COLUMNS = {
    "mof_id",
    "molecular_weight",
    "molecular_weight_unit",
    "topology",
    "CSD_refcode",
    "MOFid",
    "MOFkey",
    "source_material_id",
}
PDF_MEASUREMENT_COLUMNS = [
    "MOF_name",
    "gas_type",
    "temperature",
    "temperature_unit",
    "pressure",
    "pressure_unit",
    "capacity_value",
    "capacity_unit",
    "DOI",
    "publication_year",
    "source_id",
    "source_url",
    "source_location",
    "extraction_method",
    "notes",
]

MEASUREMENT_INPUTS = [
    ROOT / "data/extracted/pdf_parse_preview/uio66_candidate_records.csv",
    ROOT / "data/extracted/pdf_parse_preview/uio66_figure6_digitized_points.csv",
    ROOT / "data/extracted/pdf_parse_preview/new_pdf_candidate_records.csv",
    ROOT / "data/extracted/pdf_parse_preview/manual_visual_digitized_isotherms.csv",
    ROOT / "data/extracted/web_parse_preview/mofxdb_batch/isotherm_points_preview.csv",
    ROOT / "data/extracted/web_parse_preview/nist_isodb_mirror/isotherm_points_preview.csv",
]

MATERIAL_INPUTS = [
    ROOT / "data/extracted/web_parse_preview/mofxdb_batch/materials_preview.csv",
    ROOT / "data/extracted/web_parse_preview/nist_isodb_mirror/materials_preview.csv",
]

PDF_SOURCE_METADATA = {
    "paper_uio66_nh2_sonochemical_2023": {
        "DOI": "10.1038/s41598-023-47221-6",
        "publication_year": "2023",
        "source_url": "https://www.nature.com/articles/s41598-023-47221-6",
    },
    "paper_nanosized_cu_mofs_go_gas_storage": {
        "DOI": "10.1039/c3ee23421e",
        "publication_year": "2013",
        "source_url": "local PDF: Nanosized-Cu-MOFs-induced-by-graphene-oxide-and-enhanced-gas-storage-capacity.pdf",
    },
    "pdf_nanosized_cu_mofs_go_gas_storage": {
        "DOI": "10.1039/c3ee23421e",
        "publication_year": "2013",
        "source_url": "local PDF: Nanosized-Cu-MOFs-induced-by-graphene-oxide-and-enhanced-gas-storage-capacity.pdf",
    },
    "paper_nihms_1670563": {
        "DOI": "10.1002/adma.201907995",
        "publication_year": "2020",
        "source_url": "local PDF: nihms-1670563.pdf",
    },
    "pdf_nihms_1670563": {
        "DOI": "10.1002/adma.201907995",
        "publication_year": "2020",
        "source_url": "local PDF: nihms-1670563.pdf",
    },
}


def schema_columns(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as f:
        return [field["name"] for field in json.load(f)["fields"]]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value or "").strip("_")
    return slug.lower() or "unknown"


def first_value(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = (row.get(name) or "").strip()
        if value:
            return value
    return ""


def infer_mof_name(row: dict[str, str], path: Path) -> str:
    name = first_value(row, "MOF_name", "name")
    if name:
        return name
    if path.name == "uio66_figure6_digitized_points.csv":
        return "UiO-66-NH2"
    return ""


def infer_source_id(row: dict[str, str], path: Path) -> str:
    source_id = first_value(row, "source_id")
    if source_id:
        return source_id
    if path.name == "uio66_figure6_digitized_points.csv":
        return "paper_uio66_nh2_sonochemical_2023"
    pdf_id = first_value(row, "pdf_id")
    if pdf_id:
        return f"pdf_{safe_slug(pdf_id)}"
    if "web_parse_preview" in path.parts:
        return "web_preview"
    return "pdf_preview"


def infer_mof_id(row: dict[str, str], path: Path) -> str:
    mof_id = first_value(row, "mof_id")
    if mof_id:
        return mof_id
    if path.name == "uio66_figure6_digitized_points.csv":
        return "mof_uio66_nh2_sonochemical"
    source_prefix = "nist" if "nist_isodb_mirror" in str(path) else "pdf"
    return f"{source_prefix}_{safe_slug(infer_mof_name(row, path))}"


def infer_record_id(row: dict[str, str], path: Path, index: int) -> str:
    record_id = first_value(row, "record_id")
    if record_id:
        return record_id
    base = "_".join(
        [
            safe_slug(path.stem),
            safe_slug(infer_mof_name(row, path)),
            safe_slug(first_value(row, "gas_type")),
            safe_slug(first_value(row, "temperature")),
            safe_slug(first_value(row, "pressure")),
            str(index),
        ]
    )
    return f"preview_{base}"


def infer_source_location(row: dict[str, str]) -> str:
    explicit = first_value(row, "source_location")
    if explicit:
        return explicit
    if first_value(row, "series") and first_value(row, "synthesis_method"):
        return f"Figure 6; series={first_value(row, 'series')}; synthesis_method={first_value(row, 'synthesis_method')}"
    pieces = []
    for label, field in [
        ("pdf", "pdf_id"),
        ("page", "page"),
        ("figure", "figure"),
        ("table_or_figure", "table_or_figure"),
    ]:
        value = first_value(row, field)
        if value:
            pieces.append(f"{label}={value}")
    return "; ".join(pieces)


def infer_extraction_method(row: dict[str, str]) -> str:
    explicit = first_value(row, "extraction_method")
    if explicit:
        return explicit
    if first_value(row, "digitization_note"):
        return "digitized_figure"
    method = first_value(row, "digitization_method")
    if method:
        return "digitized_figure"
    locator = first_value(row, "figure", "table_or_figure").lower()
    if "figure" in locator or "fig" in locator:
        return "digitized_figure"
    if "table" in locator:
        return "pdf_table"
    return "pdf_preview"


def measurement_from_row(row: dict[str, str], path: Path, index: int) -> dict[str, str]:
    out = {col: first_value(row, col) for col in schema_columns(MEASUREMENT_SCHEMA)}
    for col in PDF_MEASUREMENT_COLUMNS:
        if col not in out:
            out[col] = first_value(row, col)
    out["MOF_name"] = infer_mof_name(row, path)
    out["record_id"] = infer_record_id(row, path, index)
    out["mof_id"] = infer_mof_id(row, path)
    out["source_id"] = infer_source_id(row, path)
    out["source_location"] = infer_source_location(row)
    out["extraction_method"] = infer_extraction_method(row)
    if not out["measurement_type"] and out["capacity_value"]:
        out["measurement_type"] = "capacity"
    source_metadata = PDF_SOURCE_METADATA.get(out["source_id"], {})
    for key, value in source_metadata.items():
        out[key] = value
    if not out["source_type"]:
        out["source_type"] = "scientific_paper" if "pdf_parse_preview" in path.parts else "database_api"
    return out


def material_from_measurement_row(row: dict[str, str], path: Path) -> dict[str, str]:
    out = {col: first_value(row, col) for col in schema_columns(MATERIAL_SCHEMA)}
    out["mof_id"] = infer_mof_id(row, path)
    out["MOF_name"] = infer_mof_name(row, path)
    out["source_id"] = infer_source_id(row, path)
    return out


def is_non_mof_control(row: dict[str, str], path: Path) -> bool:
    return "pdf_parse_preview" in path.parts and infer_mof_name(row, path).strip().upper() == "GO"


def normalize_pdf_material_name(name: str) -> str:
    if name in {"NPF-200_total_adsorption", "NPF-200_excess_adsorption"}:
        return "NPF-200"
    return name


def pdf_material_key(material: dict[str, str]) -> str:
    return safe_slug(normalize_pdf_material_name(material.get("MOF_name", "")))


def merge_material(existing: dict[str, str], incoming: dict[str, str], columns: list[str]) -> dict[str, str]:
    merged = existing.copy()
    for key in columns:
        current = (merged.get(key) or "").strip()
        new = (incoming.get(key) or "").strip()
        if not current and new:
            merged[key] = new
    if existing.get("notes") and incoming.get("notes") and incoming["notes"] not in existing["notes"]:
        merged["notes"] = f"{existing['notes']} | {incoming['notes']}"
    return {col: merged.get(col, "") for col in columns}


def collapse_pdf_materials(materials: dict[str, dict[str, str]], columns: list[str]) -> list[dict[str, str]]:
    collapsed: dict[str, dict[str, str]] = {}
    for material in materials.values():
        material = material.copy()
        material["MOF_name"] = normalize_pdf_material_name(material.get("MOF_name", ""))
        key = pdf_material_key(material)
        if key not in collapsed:
            collapsed[key] = {col: material.get(col, "") for col in columns}
        else:
            collapsed[key] = merge_material(collapsed[key], material, columns)
    return list(collapsed.values())


def enrich_pdf_measurements_from_materials(
    rows: list[dict[str, str]],
    materials: list[dict[str, str]],
) -> list[dict[str, str]]:
    material_by_name = {safe_slug(row.get("MOF_name", "")): row for row in materials}
    descriptor_columns = [
        "chemical_formula",
        "metal_node",
        "organic_linker",
        "pore_size",
        "pore_size_unit",
        "surface_area_BET",
        "surface_area_BET_unit",
        "pore_volume",
        "pore_volume_unit",
    ]
    enriched = []
    for row in rows:
        out = row.copy()
        key = safe_slug(normalize_pdf_material_name(out.get("MOF_name", "")))
        material = material_by_name.get(key, {})
        for col in descriptor_columns:
            if not (out.get(col) or "").strip() and material.get(col):
                out[col] = material[col]
        enriched.append(out)
    return enriched


def material_from_material_preview(row: dict[str, str], path: Path) -> dict[str, str]:
    out = {col: "" for col in schema_columns(MATERIAL_SCHEMA)}
    if "mofxdb_batch" in str(path):
        name = first_value(row, "name")
        out.update(
            {
                "mof_id": f"mofxdb_{safe_slug(name)}",
                "MOF_name": name,
                "chemical_formula": first_value(row, "cif_atom_count_formula_preview"),
                "metal_node": first_value(row, "metal_node_preview"),
                "pore_size": first_value(row, "pld"),
                "pore_size_unit": "A" if first_value(row, "pld") else "",
                "surface_area_BET": first_value(row, "surface_area_m2g"),
                "surface_area_BET_unit": "m2/g" if first_value(row, "surface_area_m2g") else "",
                "MOFid": first_value(row, "mofid"),
                "MOFkey": first_value(row, "mofkey"),
                "source_material_id": first_value(row, "mofdb_id"),
                "source_id": "db_mofxdb",
                "source_url": first_value(row, "url"),
                "notes": f"database={first_value(row, 'database')}; elements={first_value(row, 'elements')}",
            }
        )
    elif "nist_isodb_mirror" in str(path):
        name = first_value(row, "name")
        out.update(
            {
                "mof_id": first_value(row, "hashkey") or f"nist_{safe_slug(name)}",
                "MOF_name": name,
                "chemical_formula": first_value(row, "formula"),
                "source_material_id": first_value(row, "hashkey"),
                "source_id": "db_nist_isodb",
                "notes": f"synonyms={first_value(row, 'synonyms')}; doi={first_value(row, 'doi')}",
            }
        )
    return out


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    measurement_columns = schema_columns(MEASUREMENT_SCHEMA)
    material_columns = schema_columns(MATERIAL_SCHEMA)
    pdf_material_columns = [col for col in material_columns if col not in PDF_MATERIAL_EXCLUDED_COLUMNS]

    measurement_rows = []
    pdf_measurement_rows = []
    web_measurement_rows = []
    material_by_id: dict[str, dict[str, str]] = {}
    pdf_material_by_id: dict[str, dict[str, str]] = {}
    web_material_by_id: dict[str, dict[str, str]] = {}

    for path in MEASUREMENT_INPUTS:
        is_web = "web_parse_preview" in path.parts
        for index, row in enumerate(read_csv(path), start=1):
            if is_non_mof_control(row, path):
                continue
            measurement = measurement_from_row(row, path, index)
            measurement_rows.append(measurement)
            if is_web:
                web_measurement_rows.append(measurement)
            else:
                pdf_measurement_rows.append(measurement)
            material = material_from_measurement_row(row, path)
            material_id = material["mof_id"]
            if material_id and material_id not in material_by_id:
                material_by_id[material_id] = material
            target_materials = web_material_by_id if is_web else pdf_material_by_id
            if material_id and material_id not in target_materials:
                target_materials[material_id] = material

    for path in MATERIAL_INPUTS:
        is_web = "web_parse_preview" in path.parts
        for row in read_csv(path):
            material = material_from_material_preview(row, path)
            material_id = material["mof_id"]
            if material_id:
                existing = material_by_id.get(material_id, {})
                merged = existing.copy()
                for key, value in material.items():
                    if value:
                        merged[key] = value
                material_by_id[material_id] = {col: merged.get(col, "") for col in material_columns}
                target_materials = web_material_by_id if is_web else pdf_material_by_id
                existing_source = target_materials.get(material_id, {})
                merged_source = existing_source.copy()
                for key, value in material.items():
                    if value:
                        merged_source[key] = value
                target_materials[material_id] = {col: merged_source.get(col, "") for col in material_columns}

    pdf_material_rows = collapse_pdf_materials(pdf_material_by_id, pdf_material_columns)
    pdf_measurement_rows = enrich_pdf_measurements_from_materials(pdf_measurement_rows, pdf_material_rows)
    write_csv(MEASUREMENT_OUTPUT, measurement_rows, measurement_columns)
    write_csv(MATERIAL_OUTPUT, list(material_by_id.values()), material_columns)
    write_csv(PDF_MEASUREMENT_OUTPUT, pdf_measurement_rows, PDF_MEASUREMENT_COLUMNS)
    write_csv(PDF_MATERIAL_OUTPUT, pdf_material_rows, pdf_material_columns)
    write_csv(WEB_MEASUREMENT_OUTPUT, web_measurement_rows, measurement_columns)
    write_csv(WEB_MATERIAL_OUTPUT, list(web_material_by_id.values()), material_columns)

    print(f"Wrote {len(measurement_rows)} rows to {MEASUREMENT_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {len(material_by_id)} rows to {MATERIAL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {len(pdf_measurement_rows)} PDF rows to {PDF_MEASUREMENT_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {len(pdf_material_rows)} PDF materials to {PDF_MATERIAL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {len(web_measurement_rows)} web rows to {WEB_MEASUREMENT_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {len(web_material_by_id)} web materials to {WEB_MATERIAL_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
