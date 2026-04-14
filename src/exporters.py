import csv
import os


def write_csv(filename: str, rows: list[dict]) -> None:
    if not rows:
        return

    directory = os.path.dirname(filename)

    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)