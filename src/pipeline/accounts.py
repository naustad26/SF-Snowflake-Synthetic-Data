from src.config import (
    PARENT_ACCOUNT_COUNT,
    MIN_CHILD_ACCOUNTS_PER_PARENT,
    MAX_CHILD_ACCOUNTS_PER_PARENT,
    SYNTHETIC_ID_FIELD,
)
from src.generators.accounts import generate_account_hierarchy
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.loaders.resolver import (
    resolve_account_parent_relationships,
    resolve_account_boost_account_lookup,
)
from src.pipeline.helpers import print_results


def generate_account_hierarchy_step(context) -> None:
    parent_accounts, child_accounts = generate_account_hierarchy(
        parent_count=PARENT_ACCOUNT_COUNT,
        min_children_per_parent=MIN_CHILD_ACCOUNTS_PER_PARENT,
        max_children_per_parent=MAX_CHILD_ACCOUNTS_PER_PARENT,
    )

    context.set_records("parent_accounts", parent_accounts)
    context.set_records("child_accounts", child_accounts)
    context.set_records("all_accounts", parent_accounts + child_accounts)

    print(f"Generated {len(parent_accounts)} parent accounts")
    print(f"Generated {len(child_accounts)} child accounts")


def resolve_parent_accounts_boost_lookup_step(context) -> None:
    parent_accounts = context.get_records("parent_accounts")
    boost_account_by_parent = context.get_id_map("boost_account_by_parent")

    resolved_parent_accounts = resolve_account_boost_account_lookup(
        parent_accounts,
        boost_account_by_parent,
    )

    context.set_records("parent_accounts", resolved_parent_accounts)


def upsert_parent_accounts_step(context) -> None:
    parent_accounts = context.get_records("parent_accounts")

    print("Upserting parent Accounts...")
    results = upsert_records(
        sf=context.sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=parent_accounts,
    )
    print_results("Parent Account", results)

    parent_synthetic_ids = [a["synthetic_id"] for a in parent_accounts]
    parent_account_id_map = fetch_id_map(
        sf=context.sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=parent_synthetic_ids,
    )

    context.set_id_map("parent_accounts", parent_account_id_map)


def resolve_child_accounts_step(context) -> None:
    child_accounts = context.get_records("child_accounts")
    parent_account_id_map = context.get_id_map("parent_accounts")
    boost_account_by_parent = context.get_id_map("boost_account_by_parent")

    resolved_child_accounts = resolve_account_parent_relationships(
        child_accounts,
        parent_account_id_map,
    )

    resolved_child_accounts = resolve_account_boost_account_lookup(
        resolved_child_accounts,
        boost_account_by_parent,
    )

    context.set_records("child_accounts", resolved_child_accounts)


def upsert_child_accounts_step(context) -> None:
    child_accounts = context.get_records("child_accounts")

    print("Upserting child Accounts...")
    results = upsert_records(
        sf=context.sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=child_accounts,
    )
    print_results("Child Account", results)


def fetch_all_account_ids_step(context) -> None:
    parent_accounts = context.get_records("parent_accounts")
    child_accounts = context.get_records("child_accounts")
    all_accounts = parent_accounts + child_accounts

    context.set_records("all_accounts", all_accounts)

    all_account_synthetic_ids = [a["synthetic_id"] for a in all_accounts]
    all_account_id_map = fetch_id_map(
        sf=context.sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=all_account_synthetic_ids,
    )

    context.set_id_map("all_accounts", all_account_id_map)

    print(f"Fetched {len(all_account_id_map)} total Account ID mappings.")