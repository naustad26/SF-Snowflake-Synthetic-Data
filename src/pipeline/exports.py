from src.config import OUTPUT_DIR, EXPORT_RAW_DATA
from src.exporters import export_raw_records


def export_generated_records_step(context) -> None:
    if not EXPORT_RAW_DATA:
        return

    export_raw_records(
        context.get_records("parent_accounts"),
        "parent_accounts_raw.json",
        OUTPUT_DIR,
    )

    export_raw_records(
        context.get_records("child_accounts"),
        "child_accounts_raw.json",
        OUTPUT_DIR,
    )

    export_raw_records(
        context.get_records("boost_accounts"),
        "boost_accounts_raw.json",
        OUTPUT_DIR,
    )

    export_raw_records(
        context.get_records("contacts"),
        "contacts_raw.json",
        OUTPUT_DIR,
    )