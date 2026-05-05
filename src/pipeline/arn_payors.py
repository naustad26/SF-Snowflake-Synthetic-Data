from src.config import (
    ARN_PAYORS_PER_MASTER_MIN,
    ARN_PAYORS_PER_MASTER_MAX,
)
from src.generators.arn_payors import generate_arn_payor_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


ARN_PAYOR_EXTERNAL_ID_FIELD = "Payer_ID__c"


def generate_arn_payors_step(context) -> None:
    arn_payor_master_records = context.get_records("arn_payor_master")

    arn_payor_records = generate_arn_payor_records(
        arn_payor_master_records=arn_payor_master_records,
        min_payors_per_master=ARN_PAYORS_PER_MASTER_MIN,
        max_payors_per_master=ARN_PAYORS_PER_MASTER_MAX,
    )

    context.set_records("arn_payors", arn_payor_records)

    print(f"Generated {len(arn_payor_records)} ARN Payor records")


def resolve_arn_payors_step(context) -> None:
    arn_payor_records = context.get_records("arn_payors")
    arn_payor_master_id_map = context.get_id_map("arn_payor_master")

    resolved_records = []

    for record in arn_payor_records:
        master_synthetic_id = record["meta"]["arn_payor_master_synthetic_id"]
        master_id = arn_payor_master_id_map.get(master_synthetic_id)

        if not master_id:
            raise ValueError(
                f"Missing ARN Payor Master ID for ARN Payor: {master_synthetic_id}"
            )

        record["fields"]["ARN_Payor_Master__c"] = master_id

        resolved_records.append(record)

    context.set_records("arn_payors", resolved_records)


def upsert_arn_payors_step(context) -> None:
    arn_payor_records = context.get_records("arn_payors")

    print("Upserting ARN Payor records...")

    results = upsert_records(
        sf=context.sf,
        object_name="ARN_Payors__c",
        external_id_field=ARN_PAYOR_EXTERNAL_ID_FIELD,
        records=arn_payor_records,
    )

    print_results("ARN Payor", results)


def fetch_arn_payor_ids_step(context) -> None:
    arn_payor_records = context.get_records("arn_payors")

    payer_ids = [
        record["fields"][ARN_PAYOR_EXTERNAL_ID_FIELD]
        for record in arn_payor_records
    ]

    arn_payor_id_map = fetch_id_map(
        sf=context.sf,
        object_name="ARN_Payors__c",
        external_id_field=ARN_PAYOR_EXTERNAL_ID_FIELD,
        synthetic_ids=payer_ids,
    )

    context.set_id_map("arn_payors", arn_payor_id_map)

    print(f"Fetched {len(arn_payor_id_map)} ARN Payor ID mappings.")