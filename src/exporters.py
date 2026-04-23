import json
from pathlib import Path


def export_raw_records(records: list[dict], filename: str, output_dir: str = "data") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    with open(out / filename, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)