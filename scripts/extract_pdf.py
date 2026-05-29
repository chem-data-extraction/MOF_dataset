#!/usr/bin/env python3
"""PDF extraction driver for MOF adsorption sources.

The current release stores accepted PDF parser results directly in
data/extracted/pdf_parsed_records.csv and data/extracted/pdf_parsed_materials.csv.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specs/pdf_extraction_manifest.json"
LOG_PATH = ROOT / "data/interim/extraction_log.jsonl"
PDF_RECORDS = ROOT / "data/extracted/pdf_parsed_records.csv"
PDF_MATERIALS = ROOT / "data/extracted/pdf_parsed_materials.csv"


def append_log(entry: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    with MANIFEST.open(encoding="utf-8") as f:
        manifest = json.load(f)

    print(manifest.get("pdf_extraction_process", "PDF extraction"))
    print(f"Parsed measurement file: {PDF_RECORDS.relative_to(ROOT)}")
    print(f"Parsed material file: {PDF_MATERIALS.relative_to(ROOT)}")
    print(f"Measurement rows file exists: {PDF_RECORDS.is_file()}")
    print(f"Material rows file exists: {PDF_MATERIALS.is_file()}")
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
            "status": "parsed_files_checked",
            "tool": "extract_pdf.py",
            "output": [
                str(PDF_RECORDS.relative_to(ROOT)),
                str(PDF_MATERIALS.relative_to(ROOT)),
            ],
            "issue": "Current release uses the two PDF parsed CSV files directly.",
        }
    )
    print(f"\nAppended planning event to {LOG_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
