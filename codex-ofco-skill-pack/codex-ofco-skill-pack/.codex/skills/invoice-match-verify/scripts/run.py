#!/usr/bin/env python3
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

SKILL_NAME = "invoice_match_verify"
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


def normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9가-힣]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_set(text: str) -> set:
    return set(normalize_text(text).split()) - {""}


def to_float(value: Any, field_name: str) -> float:
    if value is None or value == "":
        fail(f"Required numeric field missing: {field_name}")
    try:
        return float(value)
    except (TypeError, ValueError):
        fail(f"Invalid numeric value for {field_name}: {value!r}")


def load_reference_records(input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    if "reference_records" in input_data:
        raw = input_data["reference_records"]
    elif "reference_records_path" in input_data:
        raw = load_json(Path(input_data["reference_records_path"]))
    else:
        fail("Either 'reference_records' or 'reference_records_path' is required.")

    if isinstance(raw, dict):
        if "202503" in raw and isinstance(raw["202503"], list):
            records = raw["202503"]
        else:
            records = []
            for value in raw.values():
                if isinstance(value, list):
                    records.extend(value)
    elif isinstance(raw, list):
        records = raw
    else:
        fail("Reference records must be a list or an object containing lists.")

    if not records:
        fail("Reference record set is empty.")

    return records


def extract_reference_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    amount = record.get("Amount (AED)", record.get("amount_aed"))
    invoice_no = record.get("INVOICE NUMBER (OFCO)", record.get("invoice_no", ""))
    subject = record.get("SUBJECT", "")
    ref_no = record.get("NO.", record.get("NO", ""))
    samsung_ref = record.get("SAMSUNG REF", record.get("samsung_ref", ""))
    return {
        "reference_no": ref_no,
        "invoice_no": str(invoice_no or ""),
        "subject": str(subject or ""),
        "amount_aed": float(amount) if amount not in (None, "") else None,
        "samsung_ref": str(samsung_ref or "")
    }


def score_candidate(
    target: Dict[str, Any],
    candidate: Dict[str, Any],
    invoice_no_weight: float,
    subject_weight: float,
    amount_weight: float
) -> Tuple[float, float]:
    target_invoice = normalize_text(target.get("invoice_no", ""))
    cand_invoice = normalize_text(candidate["invoice_no"])
    invoice_score = 1.0 if target_invoice and cand_invoice and target_invoice == cand_invoice else 0.0

    target_tokens = token_set(target["subject"])
    cand_tokens = token_set(candidate["subject"])
    if not target_tokens or not cand_tokens:
        subject_score = 0.0
    else:
        overlap = len(target_tokens & cand_tokens)
        union = len(target_tokens | cand_tokens)
        subject_score = overlap / union if union else 0.0

    target_amount = float(target["bj_amount"])
    cand_amount = candidate["amount_aed"]
    if cand_amount in (None, 0):
        deviation_pct = math.inf
        amount_score = 0.0
    else:
        deviation_pct = abs(target_amount - cand_amount) / abs(cand_amount) * 100.0
        amount_score = max(0.0, 1.0 - min(deviation_pct / 100.0, 1.0))

    score = (
        invoice_score * invoice_no_weight
        + subject_score * subject_weight
        + amount_score * amount_weight
    )
    return score, deviation_pct


def validate_target_rows(rows: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows, list) or not rows:
        fail("'target_rows' must be a non-empty array.")

    validated: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            fail(f"target_rows[{idx}] must be an object.")
        for required in ("row_id", "bj_amount", "subject"):
            if required not in row:
                fail(f"target_rows[{idx}] missing required field: {required}")
        validated.append(
            {
                "row_id": str(row["row_id"]),
                "bj_amount": to_float(row["bj_amount"], f"target_rows[{idx}].bj_amount"),
                "subject": str(row["subject"]),
                "invoice_no": str(row.get("invoice_no", "")),
                "samsung_ref": str(row.get("samsung_ref", ""))
            }
        )
    return validated


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: run.py <input.json>")

    input_path = Path(sys.argv[1])
    input_data = load_json(input_path)

    target_rows = validate_target_rows(input_data.get("target_rows"))
    records = [extract_reference_fields(r) for r in load_reference_records(input_data)]

    tolerance_pct = float(input_data.get("tolerance_pct", 2.0))
    invoice_no_weight = float(input_data.get("invoice_no_weight", 0.35))
    subject_weight = float(input_data.get("subject_weight", 0.35))
    amount_weight = float(input_data.get("amount_weight", 0.30))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []

    for target in target_rows:
        ranked = []
        for record in records:
            if record["amount_aed"] is None:
                continue
            score, deviation_pct = score_candidate(
                target,
                record,
                invoice_no_weight,
                subject_weight,
                amount_weight
            )
            ranked.append(
                {
                    "score": round(score, 6),
                    "deviation_pct": round(deviation_pct, 2) if math.isfinite(deviation_pct) else None,
                    "reference_no": record["reference_no"],
                    "invoice_no": record["invoice_no"],
                    "subject": record["subject"],
                    "amount_aed": record["amount_aed"],
                    "samsung_ref": record["samsung_ref"]
                }
            )

        ranked.sort(key=lambda x: (x["deviation_pct"] is None, x["deviation_pct"], -x["score"]))
        best = ranked[0] if ranked else None

        if not best:
            status = "UNMATCHED"
        elif best["deviation_pct"] is not None and best["deviation_pct"] <= tolerance_pct:
            status = "MATCHED"
        else:
            status = "MISMATCH"

        results.append(
            {
                "row_id": target["row_id"],
                "status": status,
                "bj_amount": round(target["bj_amount"], 2),
                "subject": target["subject"],
                "invoice_no": target["invoice_no"],
                "best_match": best,
                "top_candidates": ranked[:5]
            }
        )

    summary = {
        "skill": SKILL_NAME,
        "tolerance_pct": round(tolerance_pct, 2),
        "total_rows": len(results),
        "matched": sum(1 for r in results if r["status"] == "MATCHED"),
        "mismatch": sum(1 for r in results if r["status"] == "MISMATCH"),
        "unmatched": sum(1 for r in results if r["status"] == "UNMATCHED")
    }

    (OUT_DIR / "match_results.json").write_text(
        json.dumps({"results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
