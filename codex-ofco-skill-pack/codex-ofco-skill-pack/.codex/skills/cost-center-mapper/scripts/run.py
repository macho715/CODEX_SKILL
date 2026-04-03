#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SKILL_NAME = "cost_center_mapper"
OUT_DIR = Path("./out") / SKILL_NAME

SUBJECT_PATTERNS = [
    (
        re.compile(r"safeen.*channel.*crossing|channel crossing", re.IGNORECASE),
        {
            "cost_main": "PORT HANDLING",
            "cost_center_a": "PORT HANDLING CHARGE",
            "cost_center_b": "CHANNEL TRANSIT CHARGES",
            "price_center": "CHANNEL TRANSIT CHARGES",
            "cost_item_code": "CHANNEL_CROSSING_CHARGES_FOR_VESSELS_WITH_1000_TO_3_001_GT"
        }
    ),
    (
        re.compile(r"adp.*port.*dues|port dues", re.IGNORECASE),
        {
            "cost_main": "PORT HANDLING",
            "cost_center_a": "PORT HANDLING CHARGE",
            "cost_center_b": "PORT DUES & SERVICES CHARGES",
            "price_center": "PORT DUES",
            "cost_item_code": "PORT_DUES_FOR_VESSELS_WITH_ABOVE_1_000_UP_TO_3_001GT"
        }
    ),
    (
        re.compile(r"cargo clearance", re.IGNORECASE),
        {
            "cost_main": "CONTRACT",
            "cost_center_a": "CONTRACT",
            "cost_center_b": "AF FOR CC",
            "price_center": "AGENCY FEE FOR CARGO CLEARANCE",
            "cost_item_code": "AGENCY_FEE_FOR_CARGO_CLEARANCE"
        }
    ),
    (
        re.compile(r"arranging fw supply|fw supply", re.IGNORECASE),
        {
            "cost_main": "CONTRACT",
            "cost_center_a": "CONTRACT",
            "cost_center_b": "AF FOR FW SA",
            "price_center": "SUPPLY_WATER_5001IG",
            "cost_item_code": "SUPPLY_WATER_5001IG"
        }
    ),
    (
        re.compile(r"berthing arrangement", re.IGNORECASE),
        {
            "cost_main": "CONTRACT",
            "cost_center_a": "CONTRACT(AF FOR BA)",
            "cost_center_b": "CONTRACT",
            "price_center": "AGENCY FEE FOR BERTHING ARRANGEMENT",
            "cost_item_code": "AGENCY_FEE_FOR_BERTHING_ARRANGEMENT"
        }
    ),
    (
        re.compile(r"5000\s*ig\s*fw|supply water 5001ig", re.IGNORECASE),
        {
            "cost_main": "AT COST",
            "cost_center_a": "AT COST",
            "cost_center_b": "AT COST(WATER SUPPLY)",
            "price_center": "SUPPLY_WATER_5001IG",
            "cost_item_code": "SUPPLY_WATER_5001IG"
        }
    ),
    (
        re.compile(r"document processing charge", re.IGNORECASE),
        {
            "cost_main": "PORT HANDLING",
            "cost_center_a": "PORT HANDLING CHARGE",
            "cost_center_b": "DOCUMENT PROCESSING",
            "price_center": "DOCUMENT PROCESSING CHARGE",
            "cost_item_code": "DOCUMENT_PROCESSING_CHARGE"
        }
    ),
    (
        re.compile(r"bulk material.*direct delivery", re.IGNORECASE),
        {
            "cost_main": "PORT HANDLING",
            "cost_center_a": "PORT HANDLING CHARGE",
            "cost_center_b": "BULK CARGO HANDLING CHARGES",
            "price_center": "BULK MATERIAL",
            "cost_item_code": "BULK_MATERIAL_SOLIDS_A_PARCEL_SIZE_0_10_001_TONS_DIRECT_DELIVERY"
        }
    )
]

TARIFF_HINTS = {
    "6.1": "CHANNEL_TRANSIT_CROSSING_REQUEST",
    "6.6": "CHANNEL_CROSSING_CHARGES_FOR_VESSELS_WITH_1000_TO_3_001_GT",
    "2.20": "DOCUMENT_PROCESSING_CHARGE",
    "201.3": "BULK_MATERIAL_SOLIDS_A_PARCEL_SIZE_0_10_001_TONS_DIRECT_DELIVERY",
    "201.30": "BULK_MATERIAL_SOLIDS_A_PARCEL_SIZE_0_10_001_TONS_DIRECT_DELIVERY"
}


def fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"Missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {path}: {exc}")


def load_data(input_data: Dict[str, Any], inline_key: str, path_key: str) -> Any:
    if inline_key in input_data:
        return input_data[inline_key]
    if path_key in input_data:
        return load_json(Path(input_data[path_key]))
    fail(f"Required input missing: {inline_key} or {path_key}")


def normalize_cost_items(raw: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    items = {}
    for item in raw.get("cost_items", []):
        code = item.get("code")
        if code:
            items[code] = item
    if not items:
        fail("cost_items is empty or invalid.")
    return items


def normalize_field_names(raw: Dict[str, Any]) -> set:
    fields = raw.get("cost_item_fields", [])
    if not isinstance(fields, list) or not fields:
        fail("cost_item_fields is empty or invalid.")
    return set(str(x) for x in fields)


def map_by_code(code: str, cost_items: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
    item = cost_items.get(code)
    if not item:
        return None
    return {
        "cost_item_code": code,
        "qty_field": item.get("qty_field"),
        "amount_field": item.get("amount_field")
    }


def classify_by_pattern(description: str) -> Optional[Dict[str, Any]]:
    for pattern, mapping in SUBJECT_PATTERNS:
        if pattern.search(description or ""):
            return dict(mapping)
    return None


def classify_by_tariff(tariff: str, cost_items: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
    code = TARIFF_HINTS.get(str(tariff or "").strip())
    if not code:
        return None
    mapped = map_by_code(code, cost_items)
    if not mapped:
        return None
    for _, pattern_mapping in SUBJECT_PATTERNS:
        if pattern_mapping["cost_item_code"] == code:
            result = dict(pattern_mapping)
            result.update(mapped)
            return result
    return None


def validate_lines(lines: Any) -> List[Dict[str, Any]]:
    if not isinstance(lines, list) or not lines:
        fail("'lines' must be a non-empty array.")
    for idx, line in enumerate(lines, start=1):
        if not isinstance(line, dict):
            fail(f"lines[{idx}] must be an object.")
        if "description" not in line:
            fail(f"lines[{idx}] missing required field: description")
    return lines


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: run.py <input.json>")

    input_data = load_json(Path(sys.argv[1]))
    lines = validate_lines(input_data.get("lines"))
    cost_items = normalize_cost_items(load_data(input_data, "cost_items", "cost_items_path"))
    field_names = normalize_field_names(load_data(input_data, "cost_item_fields", "cost_item_fields_path"))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapped_lines = []
    failures = []

    for idx, line in enumerate(lines, start=1):
        description = str(line.get("description", ""))
        tariff = str(line.get("tariff_id", line.get("tariff_code", ""))).strip()

        mapping = classify_by_tariff(tariff, cost_items)
        if not mapping:
            mapping = classify_by_pattern(description)

        if mapping:
            code_data = map_by_code(mapping["cost_item_code"], cost_items)
            if not code_data:
                failures.append({"index": idx, "reason": f"cost item code not found: {mapping['cost_item_code']}"})
                continue
            mapping.update(code_data)
        else:
            failures.append({"index": idx, "reason": "no tariff or subject pattern matched"})
            continue

        qty_field = mapping.get("qty_field")
        amount_field = mapping.get("amount_field")

        if qty_field not in field_names or amount_field not in field_names:
            failures.append(
                {
                    "index": idx,
                    "reason": "immutable field validation failed",
                    "qty_field": qty_field,
                    "amount_field": amount_field
                }
            )
            continue

        mapped_line = dict(line)
        mapped_line.update(mapping)
        mapped_lines.append(mapped_line)

    if failures:
        (OUT_DIR / "mapping_summary.json").write_text(
            json.dumps(
                {
                    "skill": SKILL_NAME,
                    "mapped_count": len(mapped_lines),
                    "failed_count": len(failures),
                    "failures": failures,
                    "status": "FAILED"
                },
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )
        fail("One or more lines could not be mapped safely.")

    (OUT_DIR / "mapped_lines.json").write_text(
        json.dumps({"mapped_lines": mapped_lines}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    (OUT_DIR / "mapping_summary.json").write_text(
        json.dumps(
            {
                "skill": SKILL_NAME,
                "mapped_count": len(mapped_lines),
                "failed_count": 0,
                "status": "OK"
            },
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
