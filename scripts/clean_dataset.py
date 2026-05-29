#!/usr/bin/env python3
"""Clean and normalize merged or extracted records into the final dataset."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

MERGED_PATH = ROOT / "data/interim/merged_records.csv"
SCHEMA_PATH = ROOT / "specs/dataset_schema.json"
MOF_SCHEMA_PATH = ROOT / "specs/mof_materials_schema.json"
MEASUREMENT_SCHEMA_PATH = ROOT / "specs/adsorption_measurements_schema.json"
MOF_TABLE_PATH = ROOT / "data/processed/mof_materials.csv"
MEASUREMENT_TABLE_PATH = ROOT / "data/processed/adsorption_measurements.csv"

MISSING_TOKENS = {"", "na", "n/a", "none", "null", "-", "nan"}
NUMERIC_COLUMNS = {
    "pore_size",
    "surface_area_BET",
    "pore_volume",
    "temperature",
    "pressure",
    "capacity_value",
    "selectivity",
    "error_bar",
    "publication_year",
}


def normalize_missing_values(value: object):
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    if text in MISSING_TOKENS:
        return None
    return value


def normalize_numeric(value: object):
    value = normalize_missing_values(value)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col == "record_id":
            continue
        if col in NUMERIC_COLUMNS:
            out[col] = out[col].map(normalize_numeric)
        else:
            out[col] = out[col].map(normalize_missing_values)
    if "record_id" in out.columns:
        out = out.drop_duplicates(subset=["record_id"], keep="first")
    return out


def load_schema_columns() -> list[str]:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    return [field["name"] for field in schema["fields"]]


def load_schema_columns_from(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as f:
        schema = json.load(f)
    return [field["name"] for field in schema["fields"]]


def load_input_frame() -> pd.DataFrame:
    if MERGED_PATH.is_file():
        return pd.read_csv(MERGED_PATH)
    import importlib.util

    build_path = ROOT / "scripts" / "build_dataset.py"
    spec = importlib.util.spec_from_file_location("build_dataset", build_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {build_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build()


def main() -> None:
    df = load_input_frame()
    columns = load_schema_columns()
    for col in columns:
        if col not in df.columns:
            df[col] = None
    df = df[columns]
    cleaned = clean_dataframe(df)
    write_normalized_tables(cleaned)
    print(f"Cleaned {len(cleaned)} merged rows")


def write_normalized_tables(df: pd.DataFrame) -> None:
    material_columns = load_schema_columns_from(MOF_SCHEMA_PATH)
    measurement_columns = load_schema_columns_from(MEASUREMENT_SCHEMA_PATH)

    material_df = df.copy()
    for col in material_columns:
        if col not in material_df.columns:
            material_df[col] = None
    material_df = material_df[material_columns]
    if "mof_id" in material_df.columns:
        material_df = material_df.drop_duplicates(subset=["mof_id"], keep="first")

    measurement_df = df.copy()
    for col in measurement_columns:
        if col not in measurement_df.columns:
            measurement_df[col] = None
    measurement_df = measurement_df[measurement_columns]

    MOF_TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    material_df.to_csv(MOF_TABLE_PATH, index=False)
    measurement_df.to_csv(MEASUREMENT_TABLE_PATH, index=False)
    print(f"Wrote {len(material_df)} rows to {MOF_TABLE_PATH.relative_to(ROOT)}")
    print(f"Wrote {len(measurement_df)} rows to {MEASUREMENT_TABLE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
