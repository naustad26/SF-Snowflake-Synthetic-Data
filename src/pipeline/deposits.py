from src.config import (
    DEPOSIT_COUNT,
    DEPOSIT_RECORD_TYPE_DEVELOPER_NAME,
)
from src.generators.deposits import generate_deposit_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


DEPOSIT_EXTERNAL_ID_FIELD = "Deposit_ID__c"


def fetch_record_type_id_by_developer_name(
    sf,
    object_api_name: str,
    developer_name: str,
) -> str:
    escaped_developer_name = developer_name.replace("'", "\\'")

    query = f"""
        SELECT Id, DeveloperName
        FROM RecordType
        WHERE SObjectType = '{object_api_name}'
        AND DeveloperName = '{escaped_developer_name}'
        LIMIT 1
    """

    result = sf.query(query)
    records = result.get("records", [])

    if not records:
        raise ValueError(
            f"Could not find {object_api_name} RecordType with DeveloperName "
            f"'{developer_name}'. Check Setup > Object Manager > {object_api_name} > Record Types."
        )

    return records[0]["Id"]


def generate_deposits_step(context) -> None:
    deposits = generate_deposit_records(
        count=DEPOSIT_COUNT,
    )

    context.set_records("deposits", deposits)

    print(f"Generated {len(deposits)} Deposit records")


def resolve_deposits_step(context) -> None:
    deposits = context.get_records("deposits")

    if DEPOSIT_RECORD_TYPE_DEVELOPER_NAME:
        record_type_id = fetch_record_type_id_by_developer_name(
            sf=context.sf,
            object_api_name="Deposit__c",
            developer_name=DEPOSIT_RECORD_TYPE_DEVELOPER_NAME,
        )

        for deposit in deposits:
            deposit["fields"]["RecordTypeId"] = record_type_id

    context.set_records("deposits", deposits)


def upsert_deposits_step(context) -> None:
    deposits = context.get_records("deposits")

    print("Upserting Deposit records...")

    results = upsert_records(
        sf=context.sf,
        object_name="Deposit__c",
        external_id_field=DEPOSIT_EXTERNAL_ID_FIELD,
        records=deposits,
    )

    print_results("Deposit", results)


def fetch_deposit_ids_step(context) -> None:
    deposits = context.get_records("deposits")

    deposit_ids = [
        deposit["fields"][DEPOSIT_EXTERNAL_ID_FIELD]
        for deposit in deposits
    ]

    deposit_id_map = fetch_id_map(
        sf=context.sf,
        object_name="Deposit__c",
        external_id_field=DEPOSIT_EXTERNAL_ID_FIELD,
        synthetic_ids=deposit_ids,
    )

    context.set_id_map("deposits", deposit_id_map)

    print(f"Fetched {len(deposit_id_map)} Deposit ID mappings.")