from src.config import (
    CHECK_PAYMENT_PROBABILITY_PER_INCOMING_PAYMENT,
    MIN_CHECK_PAYMENTS_PER_INCOMING_PAYMENT,
    MAX_CHECK_PAYMENTS_PER_INCOMING_PAYMENT,
    SYNTHETIC_ID_FIELD,
)
from src.generators.check_payments import generate_check_payment_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


def generate_check_payments_step(context) -> None:
    incoming_check_payments = context.get_records("incoming_check_payments")

    check_payments = generate_check_payment_records(
        incoming_check_payments=incoming_check_payments,
        probability_per_incoming_payment=CHECK_PAYMENT_PROBABILITY_PER_INCOMING_PAYMENT,
        min_check_payments_per_incoming_payment=MIN_CHECK_PAYMENTS_PER_INCOMING_PAYMENT,
        max_check_payments_per_incoming_payment=MAX_CHECK_PAYMENTS_PER_INCOMING_PAYMENT,
    )

    context.set_records("check_payments", check_payments)

    print(f"Generated {len(check_payments)} Check Payment records")


def resolve_check_payments_step(context) -> None:
    check_payments = context.get_records("check_payments")

    boost_id_map = context.get_id_map("boost")
    incoming_check_payment_id_map = context.get_id_map("incoming_check_payments")
    arn_check_to_member_id_map = context.get_id_map("arn_checks_to_members")

    if not boost_id_map:
        raise ValueError("Cannot resolve Check Payments because Boost ID map is missing.")

    if not incoming_check_payment_id_map:
        raise ValueError(
            "Cannot resolve Check Payments because Incoming Check Payment ID map is missing."
        )

    arn_check_to_member_ids = (
        list(arn_check_to_member_id_map.values())
        if arn_check_to_member_id_map
        else []
    )

    resolved_records = []

    for index, record in enumerate(check_payments):
        boost_synthetic_id = record["meta"].get("boost_synthetic_id")
        incoming_check_payment_synthetic_id = record["meta"].get(
            "incoming_check_payment_synthetic_id"
        )

        boost_id = boost_id_map.get(boost_synthetic_id)

        if not boost_id:
            raise ValueError(
                f"Missing Boost ID for Check Payment: {boost_synthetic_id}"
            )

        incoming_check_payment_id = incoming_check_payment_id_map.get(
            incoming_check_payment_synthetic_id
        )

        if not incoming_check_payment_id:
            raise ValueError(
                "Missing Incoming Check Payment ID for Check Payment: "
                f"{incoming_check_payment_synthetic_id}"
            )

        record["fields"]["Bill__c"] = boost_id
        record["fields"]["Incoming_Check_Payment__c"] = incoming_check_payment_id

        if arn_check_to_member_ids:
            record["fields"]["ARN_Check_To_Member__c"] = arn_check_to_member_ids[
                index % len(arn_check_to_member_ids)
            ]

        resolved_records.append(record)

    context.set_records("check_payments", resolved_records)


def upsert_check_payments_step(context) -> None:
    check_payments = context.get_records("check_payments")

    print("Upserting Check Payment records...")

    results = upsert_records(
        sf=context.sf,
        object_name="Check_Payment__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=check_payments,
    )

    print_results("Check Payment", results)


def fetch_check_payment_ids_step(context) -> None:
    check_payments = context.get_records("check_payments")

    synthetic_ids = [
        record["synthetic_id"]
        for record in check_payments
    ]

    id_map = fetch_id_map(
        sf=context.sf,
        object_name="Check_Payment__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=synthetic_ids,
    )

    context.set_id_map("check_payments", id_map)

    print(f"Fetched {len(id_map)} Check Payment ID mappings.")