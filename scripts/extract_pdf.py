#!/usr/bin/env python3
"""PDF extraction driver for MOF adsorption sources.

The official accepted PDF table remains header-only until records are manually
promoted. Parser previews are collected separately by build_preview_tables.py.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specs/pdf_extraction_manifest.json"
LOG_PATH = ROOT / "data/extracted/extraction_log.jsonl"
SCHEMA_PATH = ROOT / "specs/dataset_schema.json"
OUTPUT_PATH = ROOT / "data/extracted/pdf_extracted_records.csv"
PDF_EXTRA_COLUMNS = ["pdf_id", "page", "table_or_figure", "extraction_notes"]


def append_log(entry: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def schema_columns() -> list[str]:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    return [field["name"] for field in schema["fields"]]


def ensure_output_header() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    columns = schema_columns() + PDF_EXTRA_COLUMNS
    OUTPUT_PATH.write_text(",".join(columns) + "\n", encoding="utf-8")


def main() -> None:
    with MANIFEST.open(encoding="utf-8") as f:
        manifest = json.load(f)

    print(manifest.get("pdf_extraction_process", "PDF extraction"))
    print(f"Output: {manifest.get('output_records_file')}")
    print(f"Parsed measurement preview: {manifest.get('parsed_measurement_preview_file')}")
    print(f"Parsed material preview: {manifest.get('parsed_material_preview_file')}")
    ensure_output_header()
    print("Created schema-aligned header-only PDF extraction CSV.")
    print("\nPDFs to process:")

    for src in manifest.get("input_sources", []):
        print(
            f"  - {src['pdf_id']}: {src['pdf_path']} "
            f"(source_id={src['source_id']}, status={src.get('extraction_status')})"
        )
        if not (ROOT / src["pdf_path"]).is_file():
            print("    raw PDF missing; extraction pending")

    append_log(
        {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "step": "pdf_extraction",
            "source_id": "pdf_manifest",
            "status": "planned_no_rows_extracted",
            "tool": "extract_pdf.py",
            "output": str(manifest.get("output_records_file")),
            "issue": "Official accepted PDF CSV is header-only; parser preview rows are stored in PDF-only preview files",
        }
    )
    print(f"\nAppended planning event to {LOG_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
