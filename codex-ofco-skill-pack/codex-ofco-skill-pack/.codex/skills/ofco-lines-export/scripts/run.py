#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SKILL_NAME = "ofco_lines_export"
OUT_DIR = Path("./out") / SKILL_NAME
COLUMNS = [
    "invoice_no",
    "line_no",
    "tariff_id",
    "description",
    "unit1",
    "unit2",
    "unit3",
    "rate",
    "amount_excl_tax",
    "tax_rate_pct",
    "tax_amount",
    "total_incl_tax",
    "calc_check",
    "evidence"
]


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


def round2(value: Any) -> float:
    return round(float(value or 0.0), 2)


def normalize_units(line: Dict[str, Any]) -> Dict[str, float]:
    u1 = float(line.get("unit1", 0.0) or 0.0)
    u2 = float(line.get("unit2", 0.0) or 0.0)
    u3 = float(line.get("unit3", 0.0) or 0.0)
    if u1 == 0.0 and u2 == 0.0 and u3 == 0.0:
        return {"unit1": 1.0, "unit2": 1.0, "unit3": 1.0}
    return {"unit1": u1 if u1 != 0 else 1.0, "unit2": u2 if u2 != 0 else 1.0, "unit3": u3 if u3 != 0 else 1.0}


def validate_lines(lines: Any) -> List[Dict[str, Any]]:
    if not isinstance(lines, list) or not lines:
        fail("'lines' must be a non-empty array.")
    required = {"invoice_no", "line_no", "tariff_id", "description", "rate", "amount_excl_tax"}
    for idx, line in enumerate(lines, start=1):
        if not isinstance(line, dict):
            fail(f"lines[{idx}] must be an object.")
        missing = sorted(required - set(line.keys()))
        if missing:
            fail(f"lines[{idx}] missing required fields: {', '.join(missing)}")
    return lines


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: run.py <input.json>")

    input_data = load_json(Path(sys.argv[1]))
    lines = validate_lines(input_data.get("lines"))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    output_lines = []

    for line in lines:
        units = normalize_units(line)
        rate = round2(line["rate"])
        amount = round2(line["amount_excl_tax"])
        tax_rate = round2(line.get("tax_rate_pct", 0.0))
        tax_amount = round2(line.get("tax_amount", 0.0))
        total = round2(line.get("total_incl_tax", amount + tax_amount))
        calc_value = round2(units["unit1"] * units["unit2"] * units["unit3"] * rate)
        calc_check = abs(calc_value - amount) <= 0.01

        output_lines.append(
            {
                "invoice_no": str(line["invoice_no"]),
                "line_no": int(line["line_no"]),
                "tariff_id": str(line["tariff_id"]),
                "description": str(line["description"]),
                "unit1": round2(units["unit1"]),
                "unit2": round2(units["unit2"]),
                "unit3": round2(units["unit3"]),
                "rate": rate,
                "amount_excl_tax": amount,
                "tax_rate_pct": tax_rate,
                "tax_amount": tax_amount,
                "total_incl_tax": total,
                "calc_check": bool(calc_check),
                "evidence": str(line.get("evidence", ""))
            }
        )

    with (OUT_DIR / "lines.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(output_lines)

    (OUT_DIR / "lines.json").write_text(
        json.dumps({"lines": output_lines}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
