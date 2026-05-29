#!/usr/bin/env python3
"""Web/API probe driver for MOF database sources.

Practice 4 uses conservative probes: download source snapshots, inspect whether
an API response is available, and keep record extraction disabled until source
terms, experimental/computational origin, and units are verified.
"""

from __future__ import annotations

import json
import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specs/web_extraction_manifest.json"
LOG_PATH = ROOT / "data/extracted/extraction_log.jsonl"
WEB_CSV = ROOT / "data/extracted/web_extracted_records.csv"
PROBE_SUMMARY = ROOT / "data/extracted/web_probe_summary.json"
NIST_RAW_BASE = "https://raw.githubusercontent.com/NIST-ISODB/isodb-library/master/Library"
WEB_MEASUREMENT_COLUMNS = [
    "MOF_name",
    "gas_type",
    "temperature",
    "temperature_unit",
    "pressure",
    "pressure_unit",
    "capacity_value",
    "capacity_unit",
    "isotherm_id",
    "DOI",
    "publication_year",
    "source_id",
    "source_url",
    "source_location",
    "extraction_method",
    "notes",
]


def append_log(entry: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def ensure_output_header() -> None:
    WEB_CSV.parent.mkdir(parents=True, exist_ok=True)
    WEB_CSV.write_text(",".join(WEB_MEASUREMENT_COLUMNS) + "\n", encoding="utf-8")


def fetch_url(url: str, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "MOF-dataset-course-project/0.1"})
    with urlopen(req, timeout=60) as response:
        content = response.read()
        content_type = response.headers.get("content-type", "")
    path.write_bytes(content)
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": len(content),
        "content_type": content_type,
    }


def fetch_json(url: str, path: Path) -> dict:
    fetch_url(url, path)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def atom_counts_from_cif(cif: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for line in cif.splitlines():
        parts = line.split()
        if len(parts) >= 5 and re.match(r"^[A-Z][a-z]?\d+$", parts[0]):
            symbol = parts[1]
            if re.match(r"^[A-Z][a-z]?$", symbol):
                counts[symbol] += 1
    return dict(sorted(counts.items()))


def metal_symbols(elements: list[dict]) -> str:
    metals = {
        "Li", "Be", "Na", "Mg", "Al", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn",
        "Fe", "Co", "Ni", "Cu", "Zn", "Zr", "Cd", "Y", "Hf", "La", "Ce", "Nd", "U",
    }
    return ", ".join(e["symbol"] for e in elements if e.get("symbol") in metals)


def safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")


def detail_targets_from_api(batch: dict) -> list[dict]:
    api_path = ROOT / batch["raw_api_probe_path"]
    with api_path.open(encoding="utf-8") as f:
        data = json.load(f)

    targets = []
    for result in data.get("results", []):
        if batch.get("require_isotherms", True) and not result.get("isotherms"):
            continue
        name = result.get("name")
        mof_id = result.get("id")
        if not name or not mof_id:
            continue
        slug = safe_slug(name)
        targets.append(
            {
                "source_id": "db_mofxdb",
                "mof_name": name,
                "mofdb_id": mof_id,
                "mof_url": f"https://mof.tech.northwestern.edu/mofs/{mof_id}.json",
                "raw_mof_path": f"data/raw/web/mofxdb_batch/{slug}.json",
                "raw_isotherm_directory": f"data/raw/web/mofxdb_batch/{slug}_isotherms",
                "material_summary_output": f"data/extracted/web_parse_preview/mofxdb_batch/materials/{slug}.json",
                "isotherm_points_output": f"data/extracted/web_parse_preview/mofxdb_batch/isotherms/{slug}_isotherm_points.csv",
            }
        )
        if len(targets) >= int(batch.get("limit", 10)):
            break
    return targets


def write_batch_preview(batch: dict, details: list[dict]) -> dict:
    material_rows = []
    point_rows = []

    for detail in details:
        material_path = ROOT / detail["material_summary_output"]
        if material_path.is_file():
            with material_path.open(encoding="utf-8") as f:
                material_rows.append(json.load(f))

        points_path = ROOT / detail["isotherm_points_output"]
        if points_path.is_file() and points_path.stat().st_size > 0:
            with points_path.open(newline="", encoding="utf-8") as f:
                point_rows.extend(csv.DictReader(f))

    combined_materials_path = ROOT / batch["combined_materials_output"]
    combined_points_path = ROOT / batch["combined_isotherm_points_output"]
    combined_materials_path.parent.mkdir(parents=True, exist_ok=True)
    combined_points_path.parent.mkdir(parents=True, exist_ok=True)

    material_fields = [
        "source_id",
        "mofdb_id",
        "name",
        "url",
        "lcd",
        "pld",
        "surface_area_m2g",
        "surface_area_m2cm3",
        "void_fraction",
        "mofid",
        "mofkey",
        "database",
        "elements",
        "cif_atom_count_formula_preview",
        "metal_node_preview",
        "isotherm_count",
    ]
    with combined_materials_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=material_fields)
        writer.writeheader()
        for row in material_rows:
            clean_row = {key: row.get(key, "") for key in material_fields}
            if isinstance(clean_row["elements"], list):
                clean_row["elements"] = ";".join(clean_row["elements"])
            writer.writerow(clean_row)

    if point_rows:
        with combined_points_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(point_rows[0].keys()))
            writer.writeheader()
            writer.writerows(point_rows)
    else:
        combined_points_path.write_text("", encoding="utf-8")

    return {
        "combined_materials_output": str(combined_materials_path.relative_to(ROOT)),
        "combined_isotherm_points_output": str(combined_points_path.relative_to(ROOT)),
        "material_rows": len(material_rows),
        "isotherm_point_rows": len(point_rows),
    }


def nist_raw_url(path: str) -> str:
    return f"{NIST_RAW_BASE}/{path}"


def fetch_nist_json(path: str, output_path: Path) -> dict:
    return fetch_json(nist_raw_url(path), output_path)


def parse_nist_mirror_batch(batch: dict) -> dict:
    raw_root = ROOT / batch["raw_directory"]
    preview_root = (ROOT / batch["isotherm_points_output"]).parent
    raw_root.mkdir(parents=True, exist_ok=True)
    preview_root.mkdir(parents=True, exist_ok=True)

    doi_stub = batch["doi_stub"]
    bibliography = fetch_nist_json(
        f"Bibliography/{doi_stub}.json",
        raw_root / "Bibliography" / f"{doi_stub}.json",
    )
    isotherm_refs = bibliography.get("isotherms", [])[: int(batch.get("isotherm_limit", 5))]

    adsorbents_by_hash = {}
    for adsorbent_ref in bibliography.get("adsorbents", []):
        hashkey = adsorbent_ref.get("hashkey")
        if not hashkey:
            continue
        try:
            adsorbents_by_hash[hashkey] = fetch_nist_json(
                f"Adsorbents/{hashkey}.json",
                raw_root / "Adsorbents" / f"{hashkey}.json",
            )
        except Exception:  # noqa: BLE001 - keep preview robust if a linked metadata file is missing
            adsorbents_by_hash[hashkey] = adsorbent_ref

    adsorbates_by_key = {}
    for adsorbate_ref in bibliography.get("adsorbates", []):
        inchikey = adsorbate_ref.get("InChIKey")
        if not inchikey:
            continue
        try:
            adsorbates_by_key[inchikey] = fetch_nist_json(
                f"Adsorbates/{inchikey}.json",
                raw_root / "Adsorbates" / f"{inchikey}.json",
            )
        except Exception:  # noqa: BLE001
            adsorbates_by_key[inchikey] = adsorbate_ref

    point_rows = []
    material_rows = {}
    for iso_ref in isotherm_refs:
        filename = iso_ref.get("filename")
        if not filename:
            continue
        iso = fetch_nist_json(
            f"{doi_stub}/{filename}.json",
            raw_root / doi_stub / f"{filename}.json",
        )
        adsorbent_ref = iso.get("adsorbent") or {}
        hashkey = adsorbent_ref.get("hashkey", "")
        adsorbent = adsorbents_by_hash.get(hashkey, adsorbent_ref)
        material_rows[hashkey or adsorbent_ref.get("name", "")] = {
            "source_id": "db_nist_isodb",
            "hashkey": hashkey,
            "name": adsorbent.get("name") or adsorbent_ref.get("name"),
            "formula": adsorbent.get("formula", ""),
            "synonyms": ";".join(adsorbent.get("synonyms", [])),
            "external_resources": json.dumps(adsorbent.get("External_Resources", []), ensure_ascii=False),
            "doi": iso.get("DOI") or bibliography.get("DOI"),
            "title": bibliography.get("title", ""),
            "year": bibliography.get("year", ""),
        }

        adsorbate_formula_by_key = {
            key: value.get("formula", "")
            for key, value in adsorbates_by_key.items()
        }
        adsorbate_name_by_key = {
            key: value.get("name", "")
            for key, value in adsorbates_by_key.items()
        }
        fallback_gas_name = "+".join(a.get("name", "") for a in iso.get("adsorbates", [])).strip("+")
        fallback_gas_formula = "+".join(
            adsorbate_formula_by_key.get(a.get("InChIKey"), "") for a in iso.get("adsorbates", [])
        ).strip("+")

        for idx, point in enumerate(iso.get("isotherm_data", []), start=1):
            species_rows = point.get("species_data") or [{}]
            for sp in species_rows:
                inchikey = sp.get("InChIKey", "")
                gas_name = adsorbate_name_by_key.get(inchikey) or fallback_gas_name
                gas_formula = adsorbate_formula_by_key.get(inchikey) or fallback_gas_formula
                point_rows.append(
                    {
                        "record_id": f"nist_{safe_slug(filename)}_p{idx}_{safe_slug(gas_name or 'gas')}",
                        "mof_id": hashkey,
                        "MOF_name": adsorbent.get("name") or adsorbent_ref.get("name"),
                        "chemical_formula": adsorbent.get("formula", ""),
                        "metal_node": "",
                        "organic_linker": "",
                        "pore_size": "",
                        "pore_size_unit": "",
                        "CSD_refcode": "",
                        "MOFid": "",
                        "MOFkey": "",
                        "source_material_id": hashkey,
                        "topology": "",
                        "surface_area_BET": "",
                        "surface_area_BET_unit": "",
                        "pore_volume": "",
                        "pore_volume_unit": "",
                        "gas_type": gas_formula,
                        "gas_name": gas_name,
                        "temperature": iso.get("temperature"),
                        "temperature_unit": "K",
                        "pressure": point.get("pressure"),
                        "pressure_unit": iso.get("pressureUnits"),
                        "measurement_type": "capacity",
                        "capacity_value": sp.get("adsorption", point.get("total_adsorption")),
                        "capacity_unit": iso.get("adsorptionUnits"),
                        "isotherm_id": filename,
                        "DOI": iso.get("DOI") or bibliography.get("DOI"),
                        "publication_year": bibliography.get("year", ""),
                        "source_id": "db_nist_isodb",
                        "source_type": "github_api_mirror",
                        "source_url": nist_raw_url(f"{doi_stub}/{filename}.json"),
                        "source_location": iso.get("articleSource", ""),
                        "source_database": "NIST ISODB",
                        "extraction_method": "github_mirror_json",
                        "extraction_confidence": "high" if iso.get("category") == "exp" else "medium",
                        "notes": (
                            f"NIST category={iso.get('category')}; "
                            f"articleSource={iso.get('articleSource', '')}; "
                            f"digitizer={iso.get('digitizer', '')}."
                        ),
                    }
                )

    materials_path = ROOT / batch["materials_output"]
    points_path = ROOT / batch["isotherm_points_output"]
    materials_path.parent.mkdir(parents=True, exist_ok=True)
    points_path.parent.mkdir(parents=True, exist_ok=True)

    material_fields = [
        "source_id",
        "hashkey",
        "name",
        "formula",
        "synonyms",
        "external_resources",
        "doi",
        "title",
        "year",
    ]
    with materials_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=material_fields)
        writer.writeheader()
        for row in material_rows.values():
            writer.writerow(row)

    if point_rows:
        with points_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(point_rows[0].keys()))
            writer.writeheader()
            writer.writerows(point_rows)
    else:
        points_path.write_text("", encoding="utf-8")

    return {
        "batch_id": batch.get("batch_id"),
        "doi_stub": doi_stub,
        "doi": bibliography.get("DOI"),
        "title": bibliography.get("title"),
        "year": bibliography.get("year"),
        "raw_directory": str(raw_root.relative_to(ROOT)),
        "materials_output": str(materials_path.relative_to(ROOT)),
        "isotherm_points_output": str(points_path.relative_to(ROOT)),
        "material_rows": len(material_rows),
        "isotherm_json_count": len(isotherm_refs),
        "isotherm_point_rows": len(point_rows),
    }


def parse_mofxdb_detail(target: dict) -> dict:
    raw_mof_path = ROOT / target["raw_mof_path"]
    mof = fetch_json(target["mof_url"], raw_mof_path)
    raw_iso_dir = ROOT / target["raw_isotherm_directory"]
    raw_iso_dir.mkdir(parents=True, exist_ok=True)

    atom_counts = atom_counts_from_cif(mof.get("cif", ""))
    formula = " ".join(f"{symbol}{count}" for symbol, count in atom_counts.items())
    metals = metal_symbols(mof.get("elements", []))
    mofid = mof.get("mofid") or ""
    topology = ""
    if "MOFid-v1." in mofid:
        topology = mofid.split("MOFid-v1.")[-1].split(".")[0]

    material_summary = {
        "source_id": target["source_id"],
        "mofdb_id": mof.get("id"),
        "name": mof.get("name"),
        "url": target["mof_url"],
        "lcd": mof.get("lcd"),
        "pld": mof.get("pld"),
        "surface_area_m2g": mof.get("surface_area_m2g"),
        "surface_area_m2cm3": mof.get("surface_area_m2cm3"),
        "void_fraction": mof.get("void_fraction"),
        "mofid": mofid,
        "mofkey": mof.get("mofkey"),
        "database": mof.get("database"),
        "elements": [e.get("symbol") for e in mof.get("elements", [])],
        "cif_atom_count_formula_preview": formula,
        "metal_node_preview": metals,
        "isotherm_count": len(mof.get("isotherms", [])),
    }
    material_path = ROOT / target["material_summary_output"]
    material_path.parent.mkdir(parents=True, exist_ok=True)
    material_path.write_text(json.dumps(material_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    rows = []
    mof_slug = safe_slug(mof.get("name") or str(target["mofdb_id"]))
    for iso_ref in mof.get("isotherms", []):
        iso_path = iso_ref.get("isotherm_url")
        if not iso_path:
            continue
        iso_url = "https://mof.tech.northwestern.edu" + iso_path
        iso_id = iso_ref.get("id")
        raw_iso_path = raw_iso_dir / f"isotherm_{iso_id}.json"
        iso = fetch_json(iso_url, raw_iso_path)
        adsorbates = iso.get("adsorbates") or []
        gas_formula = "+".join(a.get("formula", "") for a in adsorbates).strip("+")
        gas_name = "+".join(a.get("name", "") for a in adsorbates).strip("+")
        formula_by_name = {a.get("name"): a.get("formula") for a in adsorbates if a.get("name")}
        for idx, point in enumerate(iso.get("isotherm_data", []), start=1):
            species = point.get("species_data") or []
            species_rows = species if len(species) > 1 else [species[0] if species else {}]
            for sp in species_rows:
                mixed = len(species) > 1
                rows.append(
                    {
                        "record_id": f"mofxdb_{mof_slug}_iso{iso.get('id', iso_id)}_p{idx}"
                        + (f"_{sp.get('name')}" if mixed else ""),
                        "mof_id": f"mofxdb_{mof_slug}",
                        "MOF_name": mof.get("name"),
                        "chemical_formula": formula,
                        "metal_node": metals,
                        "organic_linker": "from MOFid/CIF; not normalized yet",
                        "pore_size": mof.get("pld"),
                        "pore_size_unit": "A",
                        "CSD_refcode": "",
                        "MOFid": mofid,
                        "MOFkey": mof.get("mofkey") or "",
                        "source_material_id": str(mof.get("id") or ""),
                        "topology": topology,
                        "surface_area_BET": mof.get("surface_area_m2g"),
                        "surface_area_BET_unit": "m2/g",
                        "pore_volume": "",
                        "pore_volume_unit": "",
                        "gas_type": sp.get("formula") or formula_by_name.get(sp.get("name")) or gas_formula,
                        "gas_name": sp.get("name") or gas_name,
                        "temperature": iso.get("temperature"),
                        "temperature_unit": "K",
                        "pressure": point.get("pressure"),
                        "pressure_unit": iso.get("pressureUnits"),
                        "measurement_type": "capacity",
                        "capacity_value": sp.get("adsorption", point.get("total_adsorption")),
                        "capacity_unit": iso.get("adsorptionUnits"),
                        "isotherm_id": str(iso.get("id", iso_id)),
                        "DOI": iso.get("DOI"),
                        "publication_year": "",
                        "source_id": "db_mofxdb",
                        "source_type": "database_api",
                        "source_url": iso_url,
                        "source_location": iso.get("filename", "") or iso.get("articleSource", ""),
                        "source_database": "MOFX-DB",
                        "extraction_method": "web_api_json",
                        "extraction_confidence": "medium",
                        "notes": (
                            f"MOFX-DB category={iso.get('category')}; "
                            f"composition={sp.get('composition', '')}; "
                            f"origin and units require final verification."
                        ),
                    }
                )

    points_path = ROOT / target["isotherm_points_output"]
    points_path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        with points_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        points_path.write_text("", encoding="utf-8")

    return {
        "mof_name": mof.get("name"),
        "mofdb_id": mof.get("id"),
        "raw_mof_path": str(raw_mof_path.relative_to(ROOT)),
        "raw_isotherm_directory": str(raw_iso_dir.relative_to(ROOT)),
        "material_summary_output": str(material_path.relative_to(ROOT)),
        "isotherm_points_output": str(points_path.relative_to(ROOT)),
        "isotherm_json_count": len(list(raw_iso_dir.glob("isotherm_*.json"))),
        "isotherm_point_rows": len(rows),
    }


def summarize_probe(page: dict, api_path: Path | None, snapshot_info: dict | None) -> dict:
    summary = {
        "source_id": page["source_id"],
        "page_id": page["page_id"],
        "url": page["url"],
        "api_probe_url": page.get("api_probe_url", ""),
        "snapshot": snapshot_info,
        "accepted_records": 0,
        "accepted_record_reason": "Probe only; no records accepted until origin, units, and license are verified.",
    }
    if api_path and api_path.is_file():
        raw = api_path.read_text(encoding="utf-8", errors="replace")
        summary["api_probe_path"] = str(api_path.relative_to(ROOT))
        summary["api_probe_bytes"] = api_path.stat().st_size
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            summary["api_probe_format"] = "html_or_text"
            summary["api_probe_preview"] = raw[:300].replace("\n", " ")
        else:
            summary["api_probe_format"] = "json"
            summary["json_top_level_keys"] = list(data.keys())[:20] if isinstance(data, dict) else []
            if isinstance(data, dict):
                summary["json_pages"] = data.get("pages")
                summary["json_page"] = data.get("page")
                results = data.get("results", [])
                summary["json_result_count"] = len(results) if isinstance(results, list) else None
                if isinstance(results, list) and results:
                    first = results[0]
                    summary["first_result_name"] = first.get("name")
                    summary["first_result_id"] = first.get("id")
                    summary["first_result_lcd"] = first.get("lcd")
                    summary["first_result_pld"] = first.get("pld")
                    summary["first_result_isotherm_count"] = len(first.get("isotherms", []))
                    summary["first_result_heat_count"] = len(first.get("heats", []))
    return summary


def main() -> None:
    with MANIFEST.open(encoding="utf-8") as f:
        manifest = json.load(f)

    ensure_output_header()
    summaries = []

    print(f"Web extraction v{manifest.get('web_extraction_version')}")
    print(f"Output: {manifest.get('output_records_file')}")
    print(f"Probe summary: {manifest.get('probe_summary_file')}")

    for page in manifest.get("input_pages", []):
        print(f"\n- {page['page_id']}: {page['url']}")
        snapshot_info = None
        snapshot_path = ROOT / page["raw_snapshot_path"]
        try:
            snapshot_info = fetch_url(page["url"], snapshot_path)
            print(f"  snapshot: {snapshot_info['path']} ({snapshot_info['bytes']} bytes)")
        except Exception as exc:  # noqa: BLE001 - log probe failure for course artifact
            snapshot_info = {"error": f"{type(exc).__name__}: {exc}"}
            print(f"  snapshot error: {snapshot_info['error']}")

        api_path = None
        if page.get("api_probe_url") and page.get("raw_api_probe_path"):
            api_path = ROOT / page["raw_api_probe_path"]
            try:
                api_info = fetch_url(page["api_probe_url"], api_path)
                print(f"  api probe: {api_info['path']} ({api_info['bytes']} bytes)")
            except Exception as exc:  # noqa: BLE001
                api_path = None
                print(f"  api probe error: {type(exc).__name__}: {exc}")

        summaries.append(summarize_probe(page, api_path, snapshot_info))

    detail_summaries = []
    for target in manifest.get("detail_probe_mofs", []):
        if target.get("source_id") != "db_mofxdb":
            continue
        print(f"\n- detailed MOFX-DB probe: {target['mof_name']} ({target['mof_url']})")
        detail = parse_mofxdb_detail(target)
        detail_summaries.append(detail)
        print(f"  isotherm points: {detail['isotherm_point_rows']}")
        print(f"  output: {detail['isotherm_points_output']}")

    for batch in manifest.get("detail_probe_batches", []):
        if batch.get("source_id") != "db_mofxdb":
            continue
        print(f"\n- MOFX-DB detail batch: {batch.get('batch_id')} (limit={batch.get('limit')})")
        batch_details = []
        for target in detail_targets_from_api(batch):
            print(f"  {target['mof_name']}: {target['mof_url']}")
            detail = parse_mofxdb_detail(target)
            batch_details.append(detail)
            print(f"    isotherm points: {detail['isotherm_point_rows']}")
        combined = write_batch_preview(batch, batch_details)
        detail_summaries.append(
            {
                "batch_id": batch.get("batch_id"),
                "status": batch.get("status"),
                "mof_count": len(batch_details),
                "details": batch_details,
                **combined,
            }
        )
        print(f"  combined materials: {combined['combined_materials_output']}")
        print(f"  combined isotherm points: {combined['combined_isotherm_points_output']}")
        print(f"  combined point rows: {combined['isotherm_point_rows']}")

    nist_summaries = []
    for batch in manifest.get("nist_mirror_batches", []):
        if batch.get("source_id") != "db_nist_isodb":
            continue
        print(f"\n- NIST ISODB GitHub mirror batch: {batch.get('batch_id')}")
        detail = parse_nist_mirror_batch(batch)
        nist_summaries.append(detail)
        print(f"  DOI: {detail['doi']}")
        print(f"  isotherms: {detail['isotherm_json_count']}")
        print(f"  material rows: {detail['material_rows']}")
        print(f"  isotherm point rows: {detail['isotherm_point_rows']}")
        print(f"  output: {detail['isotherm_points_output']}")

    if detail_summaries:
        summaries.append({"detail_probe_mofs": detail_summaries})
    if nist_summaries:
        summaries.append({"nist_mirror_batches": nist_summaries})
    PROBE_SUMMARY.write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")
    append_log(
        {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "step": "web_extraction",
            "source_id": "web_manifest",
            "status": "probe_successful_no_accepted_records",
            "tool": "extract_web.py",
            "output": str(WEB_CSV.relative_to(ROOT)),
            "issue": "Web sources probed; accepted records remain empty pending unit/origin/license verification",
        }
    )
    print(f"\nWrote probe summary to {PROBE_SUMMARY.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
