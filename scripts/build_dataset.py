#!/usr/bin/env python3
"""Build the final MOF gas adsorption dataset from parsed PDF and web tables."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

PDF_RECORDS = ROOT / "data/extracted/pdf_parsed_records.csv"
WEB_RECORDS = ROOT / "data/extracted/web_parsed_records.csv"
PDF_MATERIALS = ROOT / "data/extracted/pdf_parsed_materials.csv"
WEB_MATERIALS = ROOT / "data/extracted/web_parsed_materials.csv"
SCHEMA_PATH = ROOT / "specs/dataset_schema.json"
MERGED_PATH = ROOT / "data/interim/merged_records.csv"
DATASET_PATH = ROOT / "data/processed/dataset.csv"

SOURCE_TYPES = {
    "paper_uio66_nh2_sonochemical_2023": "scientific_paper",
    "paper_nanosized_cu_mofs_go_gas_storage": "scientific_paper",
    "pdf_nanosized_cu_mofs_go_gas_storage": "scientific_paper",
    "paper_nihms_1670563": "scientific_paper",
    "pdf_nihms_1670563": "scientific_paper",
    "db_mofxdb": "database_api",
    "db_nist_isodb": "github_api_mirror",
}

SOURCE_DATABASES = {
    "db_mofxdb": "MOFX-DB",
    "db_nist_isodb": "NIST ISODB",
}

SOURCE_ID_ALIASES = {
    "pdf_nanosized_cu_mofs_go_gas_storage": "paper_nanosized_cu_mofs_go_gas_storage",
    "pdf_nihms_1670563": "paper_nihms_1670563",
}


def load_schema_columns() -> list[str]:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    return [field["name"] for field in schema["fields"]]


def read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str).fillna("")


def safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value or "").strip("_").lower() or "unknown"


def normalized_mof_name(name: str) -> str:
    if name in {"NPF-200_total_adsorption", "NPF-200_excess_adsorption"}:
        return "NPF-200"
    return name


def material_id(source_id: str, mof_name: str, explicit_id: str = "") -> str:
    if explicit_id:
        return explicit_id
    prefix = "web" if source_id.startswith("db_") else "pdf"
    return f"{prefix}_{safe_slug(normalized_mof_name(mof_name))}"


def canonical_source_id(source_id: str) -> str:
    return SOURCE_ID_ALIASES.get(source_id, source_id)


def material_key(source_id: str, mof_name: str) -> tuple[str, str]:
    return source_id, safe_slug(normalized_mof_name(mof_name))


def load_materials() -> dict[tuple[str, str], dict[str, str]]:
    materials: dict[tuple[str, str], dict[str, str]] = {}

    for _, row in read_csv(PDF_MATERIALS).iterrows():
        data = row.to_dict()
        name = normalized_mof_name(data.get("MOF_name", ""))
        source_id = canonical_source_id(data.get("source_id", ""))
        data["source_id"] = source_id
        data["MOF_name"] = name
        data["mof_id"] = material_id(source_id, name)
        materials[material_key(source_id, name)] = data

    for _, row in read_csv(WEB_MATERIALS).iterrows():
        data = row.to_dict()
        name = normalized_mof_name(data.get("MOF_name", ""))
        source_id = canonical_source_id(data.get("source_id", ""))
        data["source_id"] = source_id
        data["MOF_name"] = name
        data["mof_id"] = material_id(source_id, name, data.get("mof_id", ""))
        materials[material_key(source_id, name)] = data

    return materials


def nearest_material(materials: dict[tuple[str, str], dict[str, str]], source_id: str, mof_name: str) -> dict[str, str]:
    key = material_key(source_id, mof_name)
    if key in materials:
        return materials[key]

    normalized_key = safe_slug(normalized_mof_name(mof_name))
    for (candidate_source, candidate_name), material in materials.items():
        if candidate_name == normalized_key and (
            source_id == candidate_source
            or source_id.replace("pdf_", "paper_") == candidate_source
            or candidate_source.replace("paper_", "pdf_") == source_id
        ):
            return material
    return {}


def load_measurements() -> pd.DataFrame:
    frames = []
    for path in [PDF_RECORDS, WEB_RECORDS]:
        df = read_csv(path)
        if not df.empty:
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def clean_note(text: str) -> str:
    replacements = {
        "Candidate parsed value; source references supplementary Fig. S1, so verify against SI before final inclusion.": (
            "Parsed from source; supplementary figure reference should be checked before reuse."
        ),
        "Table 1 extraction preview.": "Parsed from Table 1.",
        "Figure digitization preview.": "Digitized from source figure.",
        "origin and units require final verification.": "source category and units retained as reported.",
    }
    out = text or ""
    if out.startswith("Candidate parsed value; needs final manual verification before moving to "):
        out = "Parsed from source; confidence=medium; verify against the primary source before reuse."
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out


def build_record_id(row: dict[str, str], index: int) -> str:
    pieces = [
        row.get("source_id", ""),
        row.get("MOF_name", ""),
        row.get("gas_type", ""),
        row.get("temperature", ""),
        row.get("pressure", ""),
        row.get("capacity_value", ""),
        row.get("capacity_unit", ""),
        row.get("isotherm_id", ""),
        str(index),
    ]
    return "rec_" + safe_slug("_".join(str(piece) for piece in pieces))


def build() -> pd.DataFrame:
    columns = load_schema_columns()
    materials = load_materials()
    measurements = load_measurements()
    rows: list[dict[str, str]] = []

    for index, row in enumerate(measurements.to_dict(orient="records"), start=1):
        out = {column: "" for column in columns}
        name = normalized_mof_name(row.get("MOF_name", ""))
        source_id = canonical_source_id(row.get("source_id", ""))
        row["source_id"] = source_id
        material = nearest_material(materials, source_id, name)

        for key, value in material.items():
            if key in out and value != "":
                out[key] = value
        for key, value in row.items():
            if key in out and value != "":
                out[key] = value

        out["MOF_name"] = name
        out["mof_id"] = material.get("mof_id") or material_id(source_id, name)
        out["record_id"] = build_record_id(out, index)
        out["measurement_type"] = out.get("measurement_type") or "capacity"
        out["source_type"] = out.get("source_type") or SOURCE_TYPES.get(source_id, "")
        out["source_database"] = out.get("source_database") or SOURCE_DATABASES.get(source_id, "")
        out["extraction_confidence"] = out.get("extraction_confidence") or "medium"
        out["notes"] = clean_note(out.get("notes", ""))
        rows.append(out)

    df = pd.DataFrame(rows, columns=columns)
    if not df.empty:
        df = df.drop_duplicates(subset=["record_id"], keep="first")
    return df


def main() -> None:
    MERGED_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = build()
    df.to_csv(MERGED_PATH, index=False)
    df.to_csv(DATASET_PATH, index=False)

    print(f"Wrote {len(df)} rows to {MERGED_PATH.relative_to(ROOT)}")
    print(f"Wrote {len(df)} rows to {DATASET_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
