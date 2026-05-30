"""Tests for required MOF dataset artifacts and core validation checks."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_project import (  # noqa: E402
    EXTRACTED_ALLOWED,
    check_columns,
    check_extracted_directory,
    check_required_files,
    load_json,
    load_dataset,
    load_materials,
    load_measurements,
    schema_field_names,
    source_ids_from_map,
    validate,
)


@pytest.fixture
def root() -> Path:
    return ROOT


def test_required_files_exist(root: Path) -> None:
    issues = check_required_files(root)
    assert issues == [], "\n".join(issues)


def test_extracted_directory_contains_only_final_tables(root: Path) -> None:
    issues = check_extracted_directory(root)
    assert issues == [], "\n".join(issues)
    assert {path.name for path in (root / "data/extracted").iterdir()} == EXTRACTED_ALLOWED


def test_json_files_parse(root: Path) -> None:
    for path in [
        root / "project.json",
        root / "specs/dataset_schema.json",
        root / "specs/source_map.json",
        root / "specs/mof_materials_schema.json",
        root / "specs/adsorption_measurements_schema.json",
    ]:
        load_json(path)


def test_csv_files_parse(root: Path) -> None:
    for path in [
        root / "data/extracted/pdf_parsed_materials.csv",
        root / "data/extracted/pdf_parsed_records.csv",
        root / "data/extracted/web_parsed_materials.csv",
        root / "data/extracted/web_parsed_records.csv",
        root / "data/processed/dataset.csv",
        root / "data/processed/mof_materials.csv",
        root / "data/processed/adsorption_measurements.csv",
    ]:
        pd.read_csv(path)


def test_processed_columns_match_schemas(root: Path) -> None:
    material_schema = load_json(root / "specs/mof_materials_schema.json")
    measurement_schema = load_json(root / "specs/adsorption_measurements_schema.json")
    dataset_schema = load_json(root / "specs/dataset_schema.json")
    dataset_df = load_dataset(root)
    material_df = load_materials(root)
    measurement_df = load_measurements(root)

    assert check_columns(dataset_df, dataset_schema, "dataset") == []
    assert check_columns(material_df, material_schema, "mof_materials") == []
    assert check_columns(measurement_df, measurement_schema, "adsorption_measurements") == []
    assert list(dataset_df.columns) == schema_field_names(dataset_schema)
    assert list(material_df.columns) == schema_field_names(material_schema)
    assert list(measurement_df.columns) == schema_field_names(measurement_schema)


def test_processed_table_keys(root: Path) -> None:
    material_df = load_materials(root)
    measurement_df = load_measurements(root)

    assert material_df["mof_id"].is_unique
    assert measurement_df["record_id"].is_unique
    assert set(measurement_df["mof_id"].astype(str)).issubset(set(material_df["mof_id"].astype(str)))


def test_source_ids_in_source_map(root: Path) -> None:
    source_map = load_json(root / "specs/source_map.json")
    valid = source_ids_from_map(source_map)
    dataset_df = load_dataset(root)
    material_df = load_materials(root)
    measurement_df = load_measurements(root)

    assert set(dataset_df["source_id"].astype(str)).issubset(valid)
    assert set(material_df["source_id"].astype(str)).issubset(valid)
    assert set(measurement_df["source_id"].astype(str)).issubset(valid)


def test_validate_project_passes(root: Path) -> None:
    errors, _warnings = validate(root)
    assert errors == [], "\n".join(errors)
