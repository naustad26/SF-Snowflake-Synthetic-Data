from src.config import (
    ARN_CHECK_TO_MEMBER_COUNT,
    ARN_CHECK_TO_MEMBER_RECORD_TYPE_DEVELOPER_NAME,
    SYNTHETIC_ID_FIELD,
)
from src.generators.arn_checks_to_members import generate_arn_checks_to_members_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results

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
            f"'{developer_name}'."
        )

    return records[0]["Id"]


def generate_arn_checks_to_members_step(context) -> None:
    boost_accounts = context.get_records("boost_accounts")
    deposits = context.get_records("deposits")

    records = generate_arn_checks_to_members_records(
        boost_accounts=boost_accounts,
        deposits=deposits,
        count=ARN_CHECK_TO_MEMBER_COUNT,
    )

    context.set_records("arn_checks_to_members", records)

    print(f"Generated {len(records)} ARN Check to Member records")


def resolve_arn_checks_to_members_step(context) -> None:
    records = context.get_records("arn_checks_to_members")

    account_id_map = context.get_id_map("all_accounts")
    boost_account_id_map = context.get_id_map("boost_accounts")
    deposit_id_map = context.get_id_map("deposits")

    record_type_id = None

    if ARN_CHECK_TO_MEMBER_RECORD_TYPE_DEVELOPER_NAME:
        record_type_id = fetch_record_type_id_by_developer_name(
            sf=context.sf,
            object_api_name="ARN_Checks_to_Members__c",
            developer_name=ARN_CHECK_TO_MEMBER_RECORD_TYPE_DEVELOPER_NAME,
        )

    resolved_records = []

    for record in records:
        account_synthetic_id = record["meta"].get("account_synthetic_id")
        boost_account_synthetic_id = record["meta"].get("boost_account_synthetic_id")
        deposit_synthetic_id = record["meta"].get("deposit_synthetic_id")

        if record_type_id:
            record["fields"]["RecordTypeId"] = record_type_id

        if account_synthetic_id:
            account_id = account_id_map.get(account_synthetic_id)

            if account_id:
                record["fields"]["Account__c"] = account_id

        if boost_account_synthetic_id:
            boost_account_id = boost_account_id_map.get(boost_account_synthetic_id)

            if boost_account_id:
                record["fields"]["Boost_Account__c"] = boost_account_id

        if deposit_synthetic_id:
            deposit_id = deposit_id_map.get(deposit_synthetic_id)

            if deposit_id:
                record["fields"]["Deposit__c"] = deposit_id

        resolved_records.append(record)

    context.set_records("arn_checks_to_members", resolved_records)


def upsert_arn_checks_to_members_step(context) -> None:
    records = context.get_records("arn_checks_to_members")

    print("Upserting ARN Check to Member records...")

    results = upsert_records(
        sf=context.sf,
        object_name="ARN_Checks_to_Members__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=records,
    )

    print_results("ARN Check to Member", results)


def fetch_arn_check_to_member_ids_step(context) -> None:
    records = context.get_records("arn_checks_to_members")

    synthetic_ids = [
        record["synthetic_id"]
        for record in records
    ]

    id_map = fetch_id_map(
        sf=context.sf,
        object_name="ARN_Checks_to_Members__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=synthetic_ids,
    )

    context.set_id_map("arn_checks_to_members", id_map)

    print(f"Fetched {len(id_map)} ARN Check to Member ID mappings.")