from src.config import (
    SEED,
    PARENT_ACCOUNT_COUNT,
    MIN_CHILD_ACCOUNTS_PER_PARENT,
    MAX_CHILD_ACCOUNTS_PER_PARENT,
    MIN_PARENT_CONTACTS_PER_ACCOUNT,
    MAX_PARENT_CONTACTS_PER_ACCOUNT,
    MIN_CHILD_CONTACTS_PER_ACCOUNT,
    MAX_CHILD_CONTACTS_PER_ACCOUNT,
    OUTPUT_DIR,
    EXPORT_RAW_DATA,
    LOAD_TO_SALESFORCE,
    SYNTHETIC_ID_FIELD,
)
from src.generators.base import set_seed
from src.generators.accounts import generate_account_hierarchy
from src.generators.contacts import generate_contacts_for_accounts
from src.generators.boost_accounts import generate_boost_accounts_for_parent_accounts
from src.exporters import export_raw_records
from src.loaders.salesforce import get_salesforce_client, upsert_records, fetch_id_map
from src.loaders.resolver import (
    resolve_account_parent_relationships,
    resolve_contact_relationships,
    resolve_account_boost_account_lookup,
    build_boost_account_lookup_updates,
)


def build_boost_account_id_by_parent_account(
    boost_accounts: list[dict],
    boost_account_id_map: dict[str, str],
) -> dict[str, str]:
    result: dict[str, str] = {}

    for boost_account in boost_accounts:
        parent_account_synthetic_id = boost_account["meta"]["source_parent_account"]
        boost_account_synthetic_id = boost_account["synthetic_id"]

        result[parent_account_synthetic_id] = boost_account_id_map[
            boost_account_synthetic_id
        ]

    return result

def build_account_root_parent_map(
    parent_accounts: list[dict],
    child_accounts: list[dict],
) -> dict[str, str]:
    result: dict[str, str] = {}

    for parent in parent_accounts:
        result[parent["synthetic_id"]] = parent["synthetic_id"]

    for child in child_accounts:
        result[child["synthetic_id"]] = child["parent_refs"]["Account"]

    return result

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

    boost_accounts = generate_boost_accounts_for_parent_accounts(parent_accounts)

    all_accounts = parent_accounts + child_accounts

    parent_contacts = generate_contacts_for_accounts(
        parent_accounts,
        min_per_account=MIN_PARENT_CONTACTS_PER_ACCOUNT,
        max_per_account=MAX_PARENT_CONTACTS_PER_ACCOUNT,
    )

    child_contacts = generate_contacts_for_accounts(
        child_accounts,
        min_per_account=MIN_CHILD_CONTACTS_PER_ACCOUNT,
        max_per_account=MAX_CHILD_CONTACTS_PER_ACCOUNT,
    )

    contacts = parent_contacts + child_contacts

    print(f"Generated {len(parent_accounts)} parent accounts")
    print(f"Generated {len(child_accounts)} child accounts")
    print(f"Generated {len(boost_accounts)} boost accounts")
    print(f"Generated {len(contacts)} contacts")

    if EXPORT_RAW_DATA:
        export_raw_records(parent_accounts, "parent_accounts_raw.json", OUTPUT_DIR)
        export_raw_records(child_accounts, "child_accounts_raw.json", OUTPUT_DIR)
        export_raw_records(boost_accounts, "boost_accounts_raw.json", OUTPUT_DIR)
        export_raw_records(contacts, "contacts_raw.json", OUTPUT_DIR)

    if not LOAD_TO_SALESFORCE:
        print("Export only mode")
        return

    sf = get_salesforce_client()

    # --- BOOST ACCOUNTS FIRST ---
    print("Upserting Boost Accounts...")
    boost_results = upsert_records(
        sf=sf,
        object_name="ARN_Account__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=boost_accounts,
    )
    print_results("Boost Account", boost_results)

    boost_synthetic_ids = [b["synthetic_id"] for b in boost_accounts]
    boost_account_id_map = fetch_id_map(
        sf=sf,
        object_name="ARN_Account__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=boost_synthetic_ids,
    )

    boost_account_by_parent = build_boost_account_id_by_parent_account(
        boost_accounts,
        boost_account_id_map,
    )

    # --- PARENT ACCOUNTS ---
    parent_accounts = resolve_account_boost_account_lookup(
        parent_accounts,
        boost_account_by_parent,
    )

    print("Upserting parent Accounts...")
    parent_results = upsert_records(
        sf=sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=parent_accounts,
    )
    print_results("Parent Account", parent_results)

    parent_ids = [a["synthetic_id"] for a in parent_accounts]
    parent_account_id_map = fetch_id_map(
        sf=sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=parent_ids,
    )

    # --- CHILD ACCOUNTS ---
    child_accounts = resolve_account_parent_relationships(
        child_accounts,
        parent_account_id_map,
    )

    child_accounts = resolve_account_boost_account_lookup(
        child_accounts,
        boost_account_by_parent,
    )

    print("Upserting child Accounts...")
    child_results = upsert_records(
        sf=sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=child_accounts,
    )
    print_results("Child Account", child_results)

    # --- CONTACTS ---
    all_account_ids = [a["synthetic_id"] for a in all_accounts]
    all_account_id_map = fetch_id_map(
        sf=sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=all_account_ids,
    )

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

    contact_synthetic_ids = [contact["synthetic_id"] for contact in contacts]
    contact_id_map = fetch_id_map(
        sf=sf,
        object_name="Contact",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=contact_synthetic_ids,
    )

    print(f"Fetched {len(contact_id_map)} Contact ID mappings.")

    print(f"Fetched {len(contact_id_map)} Contact ID mappings.")

    account_root_parent_map = build_account_root_parent_map(
        parent_accounts,
        child_accounts,
    )

    boost_lookup_updates = build_boost_account_lookup_updates(
        boost_accounts=boost_accounts,
        parent_account_id_map=parent_account_id_map,
        contact_id_map=contact_id_map,
        contacts=contacts,
        account_root_parent_map=account_root_parent_map,
        external_id_field=SYNTHETIC_ID_FIELD,
    )

    print("Updating Boost Account lookup fields...")
    boost_lookup_results = upsert_records(
        sf=sf,
        object_name="ARN_Account__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=boost_lookup_updates,
    )

    print_results("Boost Account lookup update", boost_lookup_results)

if __name__ == "__main__":
    main()