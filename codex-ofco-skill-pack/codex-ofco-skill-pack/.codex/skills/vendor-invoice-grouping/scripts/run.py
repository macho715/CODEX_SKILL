#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SKILL_NAME = "vendor_invoice_grouping"
OUT_DIR = Path("./out") / SKILL_NAME


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


def identify_invoice_type(line: Dict[str, Any]) -> str:
    tariff = str(line.get("tariff_id", line.get("tariff_code", ""))).strip()
    desc = str(line.get("description", "")).upper()

    if tariff in {"6.10", "6.60", "6.1", "6.6"} or "SAFEEN" in desc:
        return "SAFEEN"
    if tariff in {"2.20", "201.30", "201.3"} or "ADP" in desc or "INV0325" in desc:
        return "ADP"
    return "OFCO"


def validate_lines(lines: Any) -> List[Dict[str, Any]]:
    if not isinstance(lines, list) or not lines:
        fail("'standard_lines' must be a non-empty array.")
    validated: List[Dict[str, Any]] = []
    for idx, line in enumerate(lines, start=1):
        if not isinstance(line, dict):
            fail(f"standard_lines[{idx}] must be an object.")
        if "description" not in line:
            fail(f"standard_lines[{idx}] missing required field: description")
        if "amount_excl_tax_aed" not in line:
            fail(f"standard_lines[{idx}] missing required field: amount_excl_tax_aed")
        try:
            amount_aed = float(line["amount_excl_tax_aed"])
            tax_aed = float(line.get("tax_amount_aed", 0.0) or 0.0)
            amount_usd = float(line.get("amount_excl_tax", 0.0) or 0.0)
            tax_usd = float(line.get("tax_amount", 0.0) or 0.0)
        except (TypeError, ValueError):
            fail(f"standard_lines[{idx}] has invalid numeric values.")
        validated.append(
            {
                **line,
                "amount_excl_tax_aed": amount_aed,
                "tax_amount_aed": tax_aed,
                "amount_excl_tax": amount_usd,
                "tax_amount": tax_usd
            }
        )
    return validated


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: run.py <input.json>")

    input_data = load_json(Path(sys.argv[1]))
    lines = validate_lines(input_data.get("standard_lines"))

    vendor_invoices: Dict[str, Dict[str, Any]] = {}
    unassigned_lines: List[Dict[str, Any]] = []

    for line in lines:
        vendor_invoice_no = line.get("vendor_invoice_no")
        if not vendor_invoice_no:
            unassigned_lines.append(line)
            continue

        if vendor_invoice_no not in vendor_invoices:
            vendor_invoices[vendor_invoice_no] = {
                "vendor_invoice_no": vendor_invoice_no,
                "invoice_type": identify_invoice_type(line),
                "lines": [],
                "total_amount_aed": 0.0,
                "total_amount_usd": 0.0,
                "total_tax_aed": 0.0,
                "total_tax_usd": 0.0
            }

        group = vendor_invoices[vendor_invoice_no]
        group["lines"].append(line)
        group["total_amount_aed"] += line["amount_excl_tax_aed"]
        group["total_amount_usd"] += line["amount_excl_tax"]
        group["total_tax_aed"] += line["tax_amount_aed"]
        group["total_tax_usd"] += line["tax_amount"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    grouped_output = {
        "vendor_invoices": vendor_invoices,
        "unassigned_lines": unassigned_lines
    }
    summary = {
        "skill": SKILL_NAME,
        "vendor_group_count": len(vendor_invoices),
        "unassigned_count": len(unassigned_lines),
        "types": {}
    }
    for group in vendor_invoices.values():
        summary["types"][group["invoice_type"]] = summary["types"].get(group["invoice_type"], 0) + 1

    (OUT_DIR / "grouped_vendor_invoices.json").write_text(
        json.dumps(grouped_output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    (OUT_DIR / "group_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
