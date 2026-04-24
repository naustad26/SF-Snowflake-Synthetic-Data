from src.config import (
    SEED,
    PARENT_ACCOUNT_COUNT,
    MIN_CHILD_ACCOUNTS_PER_PARENT,
    MAX_CHILD_ACCOUNTS_PER_PARENT,
    MIN_CONTACTS_PER_ACCOUNT,
    MAX_CONTACTS_PER_ACCOUNT,
    OUTPUT_DIR,
    EXPORT_RAW_DATA,
    LOAD_TO_SALESFORCE,
    SYNTHETIC_ID_FIELD,
)
from src.generators.base import set_seed
from src.generators.accounts import generate_account_hierarchy
from src.generators.contacts import generate_contacts_for_accounts
from src.exporters import export_raw_records
from src.loaders.salesforce import get_salesforce_client, upsert_records, fetch_id_map
from src.loaders.resolver import (
    resolve_account_parent_relationships,
    resolve_contact_relationships,
)


def print_results(label: str, results: list[dict]) -> None:
    success_count = sum(1 for r in results if r["success"])
    failure_count = len(results) - success_count

    print(f"{label} upsert complete. Success: {success_count}, Failed: {failure_count}")

    if failure_count:
        print(f"\n{label} failures:")
        for result in results:
            if not result["success"]:
                print(f"- {result['synthetic_id']}: {result['error']}")


def main() -> None:
    set_seed(SEED)

    parent_accounts, child_accounts = generate_account_hierarchy(
        parent_count=PARENT_ACCOUNT_COUNT,
        min_children_per_parent=MIN_CHILD_ACCOUNTS_PER_PARENT,
        max_children_per_parent=MAX_CHILD_ACCOUNTS_PER_PARENT,
    )

    all_accounts = parent_accounts + child_accounts

    # More realistic: put contacts mostly on location/child accounts if they exist.
    contact_base_accounts = child_accounts if child_accounts else parent_accounts

    contacts = generate_contacts_for_accounts(
        contact_base_accounts,
        min_per_account=MIN_CONTACTS_PER_ACCOUNT,
        max_per_account=MAX_CONTACTS_PER_ACCOUNT,
    )

    print(f"Generated {len(parent_accounts)} parent account records.")
    print(f"Generated {len(child_accounts)} child/location account records.")
    print(f"Generated {len(contacts)} contact records.")

    if EXPORT_RAW_DATA:
        export_raw_records(parent_accounts, "parent_accounts_raw.json", OUTPUT_DIR)
        export_raw_records(child_accounts, "child_accounts_raw.json", OUTPUT_DIR)
        export_raw_records(contacts, "contacts_raw.json", OUTPUT_DIR)

    if not LOAD_TO_SALESFORCE:
        print("Load disabled. Export only mode.")
        return

    sf = get_salesforce_client()

    print("Upserting parent Accounts...")
    parent_results = upsert_records(
        sf=sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=parent_accounts,
    )
    print_results("Parent Account", parent_results)

    parent_synthetic_ids = [account["synthetic_id"] for account in parent_accounts]
    parent_account_id_map = fetch_id_map(
        sf=sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=parent_synthetic_ids,
    )

    print(f"Fetched {len(parent_account_id_map)} parent Account ID mappings.")

    resolved_child_accounts = resolve_account_parent_relationships(
        child_accounts,
        parent_account_id_map,
    )

    print("Upserting child/location Accounts...")
    child_results = upsert_records(
        sf=sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=resolved_child_accounts,
    )
    print_results("Child Account", child_results)

    all_account_synthetic_ids = [account["synthetic_id"] for account in all_accounts]
    all_account_id_map = fetch_id_map(
        sf=sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=all_account_synthetic_ids,
    )

    print(f"Fetched {len(all_account_id_map)} total Account ID mappings.")

    resolved_contacts = resolve_contact_relationships(
        contacts,
        all_account_id_map,
    )

    print("Upserting Contacts...")
    contact_results = upsert_records(
        sf=sf,
        object_name="Contact",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=resolved_contacts,
    )
    print_results("Contact", contact_results)


if __name__ == "__main__":
    main()