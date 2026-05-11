from src.config import SYNTHETIC_ID_FIELD
from src.generators.arn_fees import generate_arn_fee_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


def generate_arn_fees_step(context) -> None:
    boost_accounts = context.get_records("boost_accounts")
    arn_payors = context.get_records("arn_payors")

    arn_fees = generate_arn_fee_records(
        boost_accounts=boost_accounts,
        arn_payors=arn_payors,
        fee_probability_per_boost_account=0.85,
        min_fees_per_boost_account=1,
        max_fees_per_boost_account=4,
    )

    context.set_records("arn_fees", arn_fees)

    print(f"Generated {len(arn_fees)} ARN Fee records")


def resolve_arn_fees_step(context) -> None:
    arn_fees = context.get_records("arn_fees")

    if not arn_fees:
        print("No ARN Fee records to resolve")
        return

    boost_account_id_map = context.get_id_map("boost_accounts")
    arn_payor_id_map = context.get_id_map("arn_payors")

    for arn_fee in arn_fees:
        boost_account_synthetic_id = arn_fee["meta"]["boost_account_synthetic_id"]
        arn_payor_synthetic_id = arn_fee["meta"]["arn_payor_synthetic_id"]

        if boost_account_synthetic_id not in boost_account_id_map:
            raise KeyError(
                f"ARN Fee {arn_fee['synthetic_id']} references Boost Account "
                f"{boost_account_synthetic_id}, but it was not found in the Boost Account ID map."
            )

        if arn_payor_synthetic_id not in arn_payor_id_map:
            raise KeyError(
                f"ARN Fee {arn_fee['synthetic_id']} references ARN Payor "
                f"{arn_payor_synthetic_id}, but it was not found in the ARN Payor ID map."
            )

        arn_fee["fields"]["Boost_Account__c"] = boost_account_id_map[
            boost_account_synthetic_id
        ]

        arn_fee["fields"]["ARN_Payor__c"] = arn_payor_id_map[
            arn_payor_synthetic_id
        ]

    context.set_records("arn_fees", arn_fees)


def upsert_arn_fees_step(context) -> None:
    arn_fees = context.get_records("arn_fees")

    if not arn_fees:
        print("No ARN Fee records to upsert")
        return

    print("Upserting ARN Fee records...")

    results = upsert_records(
        sf=context.sf,
        object_name="ARN_Fees__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=arn_fees,
    )

    print_results("ARN Fee", results)


def fetch_arn_fee_ids_step(context) -> None:
    arn_fees = context.get_records("arn_fees")

    if not arn_fees:
        context.set_id_map("arn_fees", {})
        return

    arn_fee_synthetic_ids = [
        arn_fee["synthetic_id"]
        for arn_fee in arn_fees
    ]

    arn_fee_id_map = fetch_id_map(
        sf=context.sf,
        object_name="ARN_Fees__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=arn_fee_synthetic_ids,
    )

    context.set_id_map("arn_fees", arn_fee_id_map)

    print(f"Fetched {len(arn_fee_id_map)} ARN Fee ID mappings.")