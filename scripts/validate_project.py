#!/usr/bin/env python3
"""Validate repository artifacts for the normalized MOF adsorption dataset."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "project.json",
    "specs/dataset_schema.json",
    "specs/source_map.json",
    "specs/pdf_extraction_manifest.json",
    "specs/web_extraction_manifest.json",
    "specs/cleaning_pipeline.json",
    "specs/validation_rules.json",
    "specs/mof_materials_schema.json",
    "specs/adsorption_measurements_schema.json",
    "data/extracted/pdf_parsed_materials.csv",
    "data/extracted/pdf_parsed_records.csv",
    "data/extracted/web_parsed_materials.csv",
    "data/extracted/web_parsed_records.csv",
    "data/processed/dataset.csv",
    "data/processed/mof_materials.csv",
    "data/processed/adsorption_measurements.csv",
    "scripts/build_dataset.py",
    "scripts/clean_dataset.py",
]

EXTRACTED_ALLOWED = {
    "pdf_parsed_materials.csv",
    "pdf_parsed_records.csv",
    "web_parsed_materials.csv",
    "web_parsed_records.csv",
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def schema_field_names(schema: dict) -> list[str]:
    return [field["name"] for field in schema["fields"]]


def source_ids_from_map(source_map: dict) -> set[str]:
    ids: set[str] = set()
    for group_sources in source_map.get("source_groups", {}).values():
        for entry in group_sources:
            sid = entry.get("source_id")
            if sid:
                ids.add(sid)
    return ids


def check_required_files(root: Path = ROOT) -> list[str]:
    issues = []
    for rel in REQUIRED_FILES:
        if not (root / rel).is_file():
            issues.append(f"Missing required file: {rel}")
    return issues


def check_extracted_directory(root: Path = ROOT) -> list[str]:
    issues = []
    extracted = root / "data/extracted"
    if not extracted.is_dir():
        return ["Missing required directory: data/extracted"]
    actual = {path.name for path in extracted.iterdir()}
    if actual != EXTRACTED_ALLOWED:
        issues.append(
            "data/extracted must contain only "
            f"{sorted(EXTRACTED_ALLOWED)}, got {sorted(actual)}"
        )
    return issues


def check_json_parseable(root: Path = ROOT) -> list[str]:
    issues = []
    for path in root.rglob("*.json"):
        if ".pytest_cache" in path.parts or "venv" in path.parts:
            continue
        try:
            load_json(path)
        except json.JSONDecodeError as exc:
            issues.append(f"Invalid JSON: {path.relative_to(root)} ({exc})")
    return issues


def load_materials(root: Path = ROOT) -> pd.DataFrame:
    return pd.read_csv(root / "data/processed/mof_materials.csv")


def load_measurements(root: Path = ROOT) -> pd.DataFrame:
    return pd.read_csv(root / "data/processed/adsorption_measurements.csv")


def load_dataset(root: Path = ROOT) -> pd.DataFrame:
    return pd.read_csv(root / "data/processed/dataset.csv")


def check_columns(df: pd.DataFrame, schema: dict, label: str) -> list[str]:
    expected = schema_field_names(schema)
    actual = list(df.columns)
    if actual != expected:
        return [f"{label} columns do not match schema. Expected {expected}, got {actual}"]
    return []


def check_unique_nonempty(df: pd.DataFrame, column: str, label: str) -> list[str]:
    issues = []
    if df[column].isna().any() or (df[column].astype(str).str.strip() == "").any():
        issues.append(f"{label}.{column} contains null or empty values")
    if df[column].duplicated().any():
        dupes = df.loc[df[column].duplicated(), column].astype(str).tolist()
        issues.append(f"Duplicate {label}.{column} values: {dupes}")
    return issues


def check_measurement_links(measurements: pd.DataFrame, materials: pd.DataFrame) -> list[str]:
    material_ids = set(materials["mof_id"].dropna().astype(str))
    measurement_ids = set(measurements["mof_id"].dropna().astype(str))
    missing = measurement_ids - material_ids
    if missing:
        return [f"measurement mof_id values missing from materials table: {sorted(missing)}"]
    return []


def check_source_id(df: pd.DataFrame, source_map: dict, label: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    valid_ids = source_ids_from_map(source_map)

    if df["source_id"].isna().any() or (df["source_id"].astype(str).str.strip() == "").any():
        errors.append(f"{label}.source_id contains null or empty values")

    unknown = set(df["source_id"].dropna().astype(str)) - valid_ids
    if unknown:
        warnings.append(f"{label}.source_id not in source map (warning): {sorted(unknown)}")
    return errors, warnings


def check_capacity_value(df: pd.DataFrame) -> list[str]:
    issues = []
    for idx, val in df["capacity_value"].items():
        if pd.isna(val) or val == "":
            continue
        try:
            float(val)
        except (TypeError, ValueError):
            issues.append(f"capacity_value not numeric at row {idx}: {val!r}")
    return issues


def validate(root: Path = ROOT) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_required_files(root))
    errors.extend(check_extracted_directory(root))
    errors.extend(check_json_parseable(root))
    if errors:
        return errors, warnings

    material_schema = load_json(root / "specs/mof_materials_schema.json")
    measurement_schema = load_json(root / "specs/adsorption_measurements_schema.json")
    dataset_schema = load_json(root / "specs/dataset_schema.json")
    source_map = load_json(root / "specs/source_map.json")
    dataset = load_dataset(root)
    materials = load_materials(root)
    measurements = load_measurements(root)

    errors.extend(check_columns(dataset, dataset_schema, "dataset"))
    errors.extend(check_columns(materials, material_schema, "mof_materials"))
    errors.extend(check_columns(measurements, measurement_schema, "adsorption_measurements"))
    errors.extend(check_unique_nonempty(dataset, "record_id", "dataset"))
    errors.extend(check_unique_nonempty(materials, "mof_id", "mof_materials"))
    errors.extend(check_unique_nonempty(measurements, "record_id", "adsorption_measurements"))
    errors.extend(check_measurement_links(measurements, materials))
    errors.extend(check_capacity_value(measurements))

    dataset_errors, dataset_warnings = check_source_id(dataset, source_map, "dataset")
    material_errors, material_warnings = check_source_id(materials, source_map, "mof_materials")
    measurement_errors, measurement_warnings = check_source_id(
        measurements, source_map, "adsorption_measurements"
    )
    errors.extend(dataset_errors)
    errors.extend(material_errors)
    errors.extend(measurement_errors)
    warnings.extend(dataset_warnings)
    warnings.extend(material_warnings)
    warnings.extend(measurement_warnings)

    return errors, warnings


def main() -> int:
    errors, warnings = validate()
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        print(f"\nValidation failed with {len(errors)} error(s).")
        return 1
    print("Validation passed.")
    if warnings:
        print(f"({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
