#!/usr/bin/env python3
"""Merge extracted CSVs and write interim and processed datasets."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

PDF_CSV = ROOT / "data/extracted/pdf_extracted_records.csv"
WEB_CSV = ROOT / "data/extracted/web_extracted_records.csv"
SCHEMA_PATH = ROOT / "specs/dataset_schema.json"
MERGED_PATH = ROOT / "data/interim/merged_records.csv"
DATASET_PATH = ROOT / "data/processed/dataset.csv"


def load_schema_columns() -> list[str]:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    return [field["name"] for field in schema["fields"]]


def read_extracted_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(path)
    if df.empty:
        return pd.DataFrame(columns=columns)
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df[columns]


def build() -> pd.DataFrame:
    columns = load_schema_columns()
    frames = [
        read_extracted_csv(PDF_CSV, columns),
        read_extracted_csv(WEB_CSV, columns),
    ]
    rows = [frame for frame in frames if not frame.empty]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.concat(rows, ignore_index=True)


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
