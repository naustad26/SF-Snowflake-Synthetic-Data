from src.config import SYNTHETIC_ID_FIELD
from src.generators.boost_accounts import generate_boost_accounts_for_parent_accounts
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.loaders.resolver import build_boost_account_lookup_updates
from src.pipeline.helpers import (
    print_results,
    build_boost_account_id_by_parent_account,
    build_account_root_parent_map,
)


def generate_boost_accounts_step(context) -> None:
    parent_accounts = context.get_records("parent_accounts")

    boost_accounts = generate_boost_accounts_for_parent_accounts(parent_accounts)

    context.set_records("boost_accounts", boost_accounts)

    print(f"Generated {len(boost_accounts)} boost accounts")


def upsert_boost_accounts_step(context) -> None:
    boost_accounts = context.get_records("boost_accounts")

    print("Upserting Boost Accounts...")
    results = upsert_records(
        sf=context.sf,
        object_name="ARN_Account__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=boost_accounts,
    )
    print_results("Boost Account", results)

    boost_synthetic_ids = [b["synthetic_id"] for b in boost_accounts]
    boost_account_id_map = fetch_id_map(
        sf=context.sf,
        object_name="ARN_Account__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=boost_synthetic_ids,
    )

    context.set_id_map("boost_accounts", boost_account_id_map)

    boost_account_by_parent = build_boost_account_id_by_parent_account(
        boost_accounts,
        boost_account_id_map,
    )

    context.set_id_map("boost_account_by_parent", boost_account_by_parent)


def update_boost_account_lookup_fields_step(context) -> None:
    boost_accounts = context.get_records("boost_accounts")
    parent_accounts = context.get_records("parent_accounts")
    child_accounts = context.get_records("child_accounts")
    contacts = context.get_records("contacts")

    parent_account_id_map = context.get_id_map("parent_accounts")
    contact_id_map = context.get_id_map("contacts")

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
    results = upsert_records(
        sf=context.sf,
        object_name="ARN_Account__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=boost_lookup_updates,
    )
    print_results("Boost Account lookup update", results)