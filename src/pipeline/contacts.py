from src.config import (
    MIN_PARENT_CONTACTS_PER_ACCOUNT,
    MAX_PARENT_CONTACTS_PER_ACCOUNT,
    MIN_CHILD_CONTACTS_PER_ACCOUNT,
    MAX_CHILD_CONTACTS_PER_ACCOUNT,
    SYNTHETIC_ID_FIELD,
)
from src.generators.contacts import generate_contacts_for_accounts
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.loaders.resolver import resolve_contact_relationships
from src.pipeline.helpers import print_results


def generate_contacts_step(context) -> None:
    parent_accounts = context.get_records("parent_accounts")
    child_accounts = context.get_records("child_accounts")

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

    context.set_records("contacts", contacts)

    print(f"Generated {len(contacts)} contacts")


def resolve_contacts_step(context) -> None:
    contacts = context.get_records("contacts")
    all_account_id_map = context.get_id_map("all_accounts")

    resolved_contacts = resolve_contact_relationships(
        contacts,
        all_account_id_map,
    )

    context.set_records("contacts", resolved_contacts)


def upsert_contacts_step(context) -> None:
    contacts = context.get_records("contacts")

    print("Upserting Contacts...")
    results = upsert_records(
        sf=context.sf,
        object_name="Contact",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=contacts,
    )
    print_results("Contact", results)

    contact_synthetic_ids = [contact["synthetic_id"] for contact in contacts]
    contact_id_map = fetch_id_map(
        sf=context.sf,
        object_name="Contact",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=contact_synthetic_ids,
    )

    context.set_id_map("contacts", contact_id_map)

    print(f"Fetched {len(contact_id_map)} Contact ID mappings.")