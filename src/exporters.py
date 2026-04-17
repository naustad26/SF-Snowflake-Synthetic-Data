# Exporters for synthetic data
import csv


def export_csv(filename: str, records: list[dict]) -> None:
    if not records:
        return

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)