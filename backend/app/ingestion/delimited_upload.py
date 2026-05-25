import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any


def hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def store_raw_file(raw_dir: Path, filename: str, content: bytes) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name
    path = raw_dir / f"{hash_bytes(content)[:12]}-{safe_name}"
    path.write_bytes(content)
    return path


def parse_records(filename: str, content: bytes) -> list[dict[str, Any]]:
    text = content.decode("utf-8-sig")
    if filename.lower().endswith(".json"):
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            parsed = parsed.get("records", [parsed])
        if not isinstance(parsed, list):
            raise ValueError("JSON input must be a list or contain a records list.")
        return [dict(row) for row in parsed]
    if filename.lower().endswith(".csv"):
        return [dict(row) for row in csv.DictReader(io.StringIO(text))]
    if filename.lower().endswith((".txt", ".tsv")):
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",\t|")
        except csv.Error:
            dialect = csv.excel_tab
        return [dict(row) for row in csv.DictReader(io.StringIO(text), dialect=dialect)]
    raise ValueError("Only CSV, tab-delimited TXT/TSV, and JSON uploads are supported.")


def raw_record_hash(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, default=str).encode("utf-8")
    return hash_bytes(payload)


def mapped_value(record: dict[str, Any], fields: dict[str, str], target: str) -> Any:
    column = fields.get(target)
    return record.get(column) if column else None


def as_int(value: Any) -> int:
    try:
        return int(float(str(value).replace(",", ""))) if value not in (None, "") else 0
    except ValueError:
        return 0


def map_severity_features(record: dict[str, Any], fields: dict[str, str]) -> dict[str, int]:
    return {
        feature: as_int(mapped_value(record, fields, feature))
        for feature in ("injuries", "fatalities", "evacuated", "quantity_released")
    }
