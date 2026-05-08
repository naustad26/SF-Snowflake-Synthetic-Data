from src.config import (
    MIN_INCOMING_CHECK_PAYMENTS_PER_BOOST,
    MAX_INCOMING_CHECK_PAYMENTS_PER_BOOST,
    INCOMING_CHECK_PAYMENT_PROBABILITY,
)
from src.generators.incoming_check_payments import generate_incoming_check_payment_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results
import random

INCOMING_CHECK_PAYMENT_EXTERNAL_ID_FIELD = "Use_for_Transfer__c"


def generate_incoming_check_payments_step(context) -> None:
    boost_records = context.get_records("boost")

    incoming_check_payments = generate_incoming_check_payment_records(
        boost_records=boost_records,
        min_payments_per_boost=MIN_INCOMING_CHECK_PAYMENTS_PER_BOOST,
        max_payments_per_boost=MAX_INCOMING_CHECK_PAYMENTS_PER_BOOST,
        payment_probability=INCOMING_CHECK_PAYMENT_PROBABILITY,
    )

    context.set_records("incoming_check_payments", incoming_check_payments)

    print(f"Generated {len(incoming_check_payments)} Incoming Check Payment records")


def resolve_incoming_check_payments_step(context) -> None:
    incoming_check_payments = context.get_records("incoming_check_payments")

    boost_id_map = context.get_id_map("boost")
    deposit_id_map = context.get_id_map("deposits")
    boost_patient_claim_id_map = context.get_id_map("boost_patient_claims")

    arn_check_to_member_id_map = context.get_id_map("arn_checks_to_members")
    arn_check_to_member_ids = (
        list(arn_check_to_member_id_map.values())
        if arn_check_to_member_id_map
        else []
    )

    if not boost_id_map:
        raise ValueError(
            "Cannot resolve Incoming Check Payments because Boost ID map is missing."
        )

    if not deposit_id_map:
        raise ValueError(
            "Cannot resolve Incoming Check Payments because Deposit ID map is missing."
        )

    deposit_ids = list(deposit_id_map.values())

    resolved_records = []

    for index, record in enumerate(incoming_check_payments):
        boost_synthetic_id = record["meta"]["boost_synthetic_id"]
        boost_patient_claim_synthetic_id = record["meta"].get(
            "boost_patient_claim_synthetic_id"
        )

        boost_id = boost_id_map.get(boost_synthetic_id)

        if not boost_id:
            raise ValueError(
                f"Missing Boost ID for Incoming Check Payment: {boost_synthetic_id}"
            )

        record["fields"]["Bill__c"] = boost_id

        # Simple first-pass distribution.
        # Later, you can group payments by deposit/check date.
        record["fields"]["Deposit__c"] = deposit_ids[index % len(deposit_ids)]

        # Populate the ARN Check to Member related list / Conga grid.
        if arn_check_to_member_ids:
            record["fields"]["ARN_Check_to_Member__c"] = arn_check_to_member_ids[
                index % len(arn_check_to_member_ids)
            ]

        if boost_patient_claim_synthetic_id and boost_patient_claim_id_map:
            boost_patient_claim_id = boost_patient_claim_id_map.get(
                boost_patient_claim_synthetic_id
            )

            if boost_patient_claim_id:
                record["fields"]["Boost_Patient_Claim__c"] = boost_patient_claim_id

        resolved_records.append(record)

    context.set_records("incoming_check_payments", resolved_records)


def upsert_incoming_check_payments_step(context) -> None:
    incoming_check_payments = context.get_records("incoming_check_payments")

    print("Upserting Incoming Check Payment records...")

    results = upsert_records(
        sf=context.sf,
        object_name="Incoming_Check_Payment__c",
        external_id_field=INCOMING_CHECK_PAYMENT_EXTERNAL_ID_FIELD,
        records=incoming_check_payments,
    )

    print_results("Incoming Check Payment", results)


def fetch_incoming_check_payment_ids_step(context) -> None:
    incoming_check_payments = context.get_records("incoming_check_payments")

    external_ids = [
        record["fields"][INCOMING_CHECK_PAYMENT_EXTERNAL_ID_FIELD]
        for record in incoming_check_payments
    ]

    incoming_check_payment_id_map = fetch_id_map(
        sf=context.sf,
        object_name="Incoming_Check_Payment__c",
        external_id_field=INCOMING_CHECK_PAYMENT_EXTERNAL_ID_FIELD,
        synthetic_ids=external_ids,
    )

    context.set_id_map("incoming_check_payments", incoming_check_payment_id_map)

    print(
        f"Fetched {len(incoming_check_payment_id_map)} "
        "Incoming Check Payment ID mappings."
    )