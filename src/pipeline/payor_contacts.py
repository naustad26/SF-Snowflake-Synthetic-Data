from src.config import (
    MIN_PAYOR_CONTACTS_PER_ACCOUNT,
    MAX_PAYOR_CONTACTS_PER_ACCOUNT,
    SYNTHETIC_ID_FIELD,
)
from src.generators.payor_contacts import generate_payor_contact_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


def generate_payor_contacts_step(context) -> None:
    payor_accounts = context.get_records("payor_accounts")

    payor_contacts = generate_payor_contact_records(
        payor_accounts=payor_accounts,
        min_contacts_per_account=MIN_PAYOR_CONTACTS_PER_ACCOUNT,
        max_contacts_per_account=MAX_PAYOR_CONTACTS_PER_ACCOUNT,
    )

    context.set_records("payor_contacts", payor_contacts)

    print(f"Generated {len(payor_contacts)} Payor Contacts")


def resolve_payor_contacts_step(context) -> None:
    payor_contacts = context.get_records("payor_contacts")
    payor_account_id_map = context.get_id_map("payor_accounts")

    resolved_contacts = []

    for contact in payor_contacts:
        payor_account_synthetic_id = contact["meta"]["payor_account_synthetic_id"]
        payor_account_id = payor_account_id_map.get(payor_account_synthetic_id)

        if not payor_account_id:
            raise ValueError(
                "Missing Payor/Bill Review Account ID for Payor Contact: "
                f"{payor_account_synthetic_id}"
            )

        contact["fields"]["AccountId"] = payor_account_id

        resolved_contacts.append(contact)

    context.set_records("payor_contacts", resolved_contacts)


def upsert_payor_contacts_step(context) -> None:
    payor_contacts = context.get_records("payor_contacts")

    print("Upserting Payor Contacts...")

    results = upsert_records(
        sf=context.sf,
        object_name="Contact",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=payor_contacts,
    )

    print_results("Payor Contact", results)


def fetch_payor_contact_ids_step(context) -> None:
    payor_contacts = context.get_records("payor_contacts")

    synthetic_ids = [
        contact["synthetic_id"]
        for contact in payor_contacts
    ]

    payor_contact_id_map = fetch_id_map(
        sf=context.sf,
        object_name="Contact",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=synthetic_ids,
    )

    context.set_id_map("payor_contacts", payor_contact_id_map)

    print(f"Fetched {len(payor_contact_id_map)} Payor Contact ID mappings.")