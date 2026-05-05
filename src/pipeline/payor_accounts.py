from src.config import (
    PAYOR_ACCOUNT_COUNT,
    PAYOR_ACCOUNT_RECORD_TYPE_DEVELOPER_NAME,
    SYNTHETIC_ID_FIELD,
)
from src.generators.payor_accounts import generate_payor_account_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


def fetch_account_record_type_id_by_developer_name(sf, developer_name: str) -> str:
    escaped_developer_name = developer_name.replace("'", "\\'")

    query = f"""
        SELECT Id, DeveloperName
        FROM RecordType
        WHERE SObjectType = 'Account'
        AND DeveloperName = '{escaped_developer_name}'
        LIMIT 1
    """

    result = sf.query(query)
    records = result.get("records", [])

    if not records:
        raise ValueError(
            "Could not find Account RecordType with DeveloperName "
            f"'{developer_name}'. Check Setup > Object Manager > Account > Record Types."
        )

    return records[0]["Id"]


def generate_payor_accounts_step(context) -> None:
    payor_accounts = generate_payor_account_records(
        count=PAYOR_ACCOUNT_COUNT,
    )

    context.set_records("payor_accounts", payor_accounts)

    print(f"Generated {len(payor_accounts)} Payor/Bill Review Accounts")


def resolve_payor_accounts_step(context) -> None:
    payor_accounts = context.get_records("payor_accounts")

    record_type_id = fetch_account_record_type_id_by_developer_name(
        sf=context.sf,
        developer_name=PAYOR_ACCOUNT_RECORD_TYPE_DEVELOPER_NAME,
    )

    for account in payor_accounts:
        account["fields"]["RecordTypeId"] = record_type_id

    context.set_records("payor_accounts", payor_accounts)


def upsert_payor_accounts_step(context) -> None:
    payor_accounts = context.get_records("payor_accounts")

    print("Upserting Payor/Bill Review Accounts...")

    results = upsert_records(
        sf=context.sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=payor_accounts,
    )

    print_results("Payor/Bill Review Account", results)


def fetch_payor_account_ids_step(context) -> None:
    payor_accounts = context.get_records("payor_accounts")

    synthetic_ids = [
        account["synthetic_id"]
        for account in payor_accounts
    ]

    payor_account_id_map = fetch_id_map(
        sf=context.sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=synthetic_ids,
    )

    context.set_id_map("payor_accounts", payor_account_id_map)

    print(f"Fetched {len(payor_account_id_map)} Payor/Bill Review Account ID mappings.")