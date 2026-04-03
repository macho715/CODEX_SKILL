#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SKILL_NAME = "flow_code_validator"
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


def validate_shipments(shipments: Any) -> List[Dict[str, Any]]:
    if not isinstance(shipments, list) or not shipments:
        fail("'shipments' must be a non-empty array.")
    validated = []
    for idx, item in enumerate(shipments, start=1):
        if not isinstance(item, dict):
            fail(f"shipments[{idx}] must be an object.")
        for field in ("shipment_id", "final_location", "current_flow_code"):
            if field not in item:
                fail(f"shipments[{idx}] missing required field: {field}")
        try:
            current_flow_code = int(item["current_flow_code"])
        except (TypeError, ValueError):
            fail(f"shipments[{idx}] current_flow_code must be an integer.")
        validated.append(
            {
                "shipment_id": str(item["shipment_id"]),
                "final_location": str(item["final_location"]).strip().upper(),
                "current_flow_code": current_flow_code,
                "pre_arrival": bool(item.get("pre_arrival", False)),
                "requires_warehouse_storage": bool(item.get("requires_warehouse_storage", False)),
                "mosb_leg": bool(item.get("mosb_leg", False)),
                "site_assigned": bool(item.get("site_assigned", True))
            }
        )
    return validated


def infer_flow_code(item: Dict[str, Any]) -> Dict[str, Any]:
    destination = item["final_location"]

    if item["pre_arrival"]:
        return {"expected_flow_code": 0, "reason": "pre-arrival"}

    if destination in {"MIR", "SHU"}:
        if item["requires_warehouse_storage"]:
            return {"expected_flow_code": 2, "reason": "onshore via warehouse"}
        return {"expected_flow_code": 1, "reason": "onshore direct"}

    if destination in {"AGI", "DAS"}:
        if not item["site_assigned"]:
            return {"expected_flow_code": 5, "reason": "offshore destination but site routing incomplete"}
        if item["requires_warehouse_storage"]:
            return {"expected_flow_code": 4, "reason": "offshore via warehouse and MOSB"}
        return {"expected_flow_code": 3, "reason": "offshore via MOSB"}

    if item["mosb_leg"] and not item["site_assigned"]:
        return {"expected_flow_code": 5, "reason": "MOSB present but site not assigned"}

    return {"expected_flow_code": 5, "reason": "unknown or mixed routing"}


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: run.py <input.json>")

    input_data = load_json(Path(sys.argv[1]))
    shipments = validate_shipments(input_data.get("shipments"))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    validated_shipments = []

    for item in shipments:
        inferred = infer_flow_code(item)
        status = "PASS" if inferred["expected_flow_code"] == item["current_flow_code"] else "FAIL"
        validated_shipments.append(
            {
                **item,
                **inferred,
                "status": status
            }
        )

    summary = {
        "skill": SKILL_NAME,
        "total_shipments": len(validated_shipments),
        "pass_count": sum(1 for x in validated_shipments if x["status"] == "PASS"),
        "fail_count": sum(1 for x in validated_shipments if x["status"] == "FAIL")
    }

    (OUT_DIR / "validated_shipments.json").write_text(
        json.dumps({"validated_shipments": validated_shipments}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    (OUT_DIR / "flow_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
