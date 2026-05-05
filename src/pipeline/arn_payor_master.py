from src.config import ARN_PAYOR_MASTER_COUNT, SYNTHETIC_ID_FIELD
from src.generators.arn_payor_master import generate_arn_payor_master_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


def generate_arn_payor_master_step(context) -> None:
    accounts = context.get_records("all_accounts")

    arn_payor_master_records = generate_arn_payor_master_records(
        accounts=accounts,
        count=ARN_PAYOR_MASTER_COUNT,
    )

    context.set_records("arn_payor_master", arn_payor_master_records)

    print(f"Generated {len(arn_payor_master_records)} ARN Payor Master records")


def resolve_arn_payor_master_step(context) -> None:
    arn_payor_master_records = context.get_records("arn_payor_master")
    account_id_map = context.get_id_map("all_accounts")

    resolved_records = []

    for record in arn_payor_master_records:
        account_synthetic_id = record["meta"]["account_synthetic_id"]
        bill_review_account_synthetic_id = record["meta"]["bill_review_account_synthetic_id"]

        account_id = account_id_map.get(account_synthetic_id)
        bill_review_account_id = account_id_map.get(bill_review_account_synthetic_id)

        if not account_id:
            raise ValueError(
                f"Missing Account ID for ARN Payor Master Account__c: {account_synthetic_id}"
            )

        if not bill_review_account_id:
            raise ValueError(
                "Missing Account ID for ARN Payor Master "
                f"ARN_Payor_Bill_Review_Account__c: {bill_review_account_synthetic_id}"
            )

        record["fields"]["Account__c"] = account_id
        record["fields"]["ARN_Payor_Bill_Review_Account__c"] = bill_review_account_id

        resolved_records.append(record)

    context.set_records("arn_payor_master", resolved_records)


def upsert_arn_payor_master_step(context) -> None:
    arn_payor_master_records = context.get_records("arn_payor_master")

    print("Upserting ARN Payor Master records...")

    results = upsert_records(
        sf=context.sf,
        object_name="ARN_Payor_Master__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=arn_payor_master_records,
    )

    print_results("ARN Payor Master", results)


def fetch_arn_payor_master_ids_step(context) -> None:
    arn_payor_master_records = context.get_records("arn_payor_master")

    synthetic_ids = [
        record["synthetic_id"]
        for record in arn_payor_master_records
    ]

    arn_payor_master_id_map = fetch_id_map(
        sf=context.sf,
        object_name="ARN_Payor_Master__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=synthetic_ids,
    )

    context.set_id_map("arn_payor_master", arn_payor_master_id_map)

    print(f"Fetched {len(arn_payor_master_id_map)} ARN Payor Master ID mappings.")