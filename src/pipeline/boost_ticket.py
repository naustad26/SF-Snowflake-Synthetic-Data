from src.config import (
    BOOST_TICKET_PROBABILITY,
    MIN_BOOST_TICKETS_PER_SELECTED_BOOST,
    MAX_BOOST_TICKETS_PER_SELECTED_BOOST,
    SYNTHETIC_ID_FIELD,
)
from src.generators.boost_ticket import generate_boost_claim_case_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


def generate_boost_ticket_step(context) -> None:
    boost_records = context.get_records("boost")

    boost_claim_cases = generate_boost_claim_case_records(
        boost_records=boost_records,
        ticket_probability=BOOST_TICKET_PROBABILITY,
        min_tickets_per_selected_boost=MIN_BOOST_TICKETS_PER_SELECTED_BOOST,
        max_tickets_per_selected_boost=MAX_BOOST_TICKETS_PER_SELECTED_BOOST,
    )

    context.set_records("boost_claim_cases", boost_claim_cases)

    print(f"Generated {len(boost_claim_cases)} Boost Ticket records")


def resolve_boost_ticket_step(context) -> None:
    boost_claim_cases = context.get_records("boost_claim_cases")

    boost_id_map = context.get_id_map("boost")
    boost_account_id_map = context.get_id_map("boost_accounts")
    boost_patient_claim_id_map = context.get_id_map("boost_patient_claims")
    arn_payor_master_id_map = context.get_id_map("arn_payor_master")

    resolved_records = []

    arn_payor_master_ids = list(arn_payor_master_id_map.values()) if arn_payor_master_id_map else []

    for record in boost_claim_cases:
        boost_synthetic_id = record["meta"]["boost_synthetic_id"]
        boost_account_synthetic_id = record["meta"].get("boost_account_synthetic_id")
        boost_patient_claim_synthetic_id = record["meta"].get("boost_patient_claim_synthetic_id")

        boost_id = boost_id_map.get(boost_synthetic_id)

        if not boost_id:
            raise ValueError(
                f"Missing Boost ID for Boost Ticket: {boost_synthetic_id}"
            )

        record["fields"]["Boost__c"] = boost_id

        if boost_account_synthetic_id:
            boost_account_id = boost_account_id_map.get(boost_account_synthetic_id)

            if boost_account_id:
                record["fields"]["ARN_Account_lookup__c"] = boost_account_id

        if boost_patient_claim_synthetic_id:
            boost_patient_claim_id = boost_patient_claim_id_map.get(
                boost_patient_claim_synthetic_id
            )

            if boost_patient_claim_id:
                record["fields"]["Boost_Patient_Claim__c"] = boost_patient_claim_id

        # First pass: assign a realistic payer master if available.
        # Later we can make this derive from Boost.ARN_Payor__c → ARN Payor → ARN Payor Master.
        if arn_payor_master_ids:
            record["fields"]["Payor_lookup__c"] = arn_payor_master_ids[
                hash(record["synthetic_id"]) % len(arn_payor_master_ids)
            ]

        resolved_records.append(record)

    context.set_records("boost_claim_cases", resolved_records)


def upsert_boost_ticket_step(context) -> None:
    boost_claim_cases = context.get_records("boost_claim_cases")

    print("Upserting Boost Ticket records...")

    results = upsert_records(
        sf=context.sf,
        object_name="Boost_Claim_Case__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=boost_claim_cases,
    )

    print_results("Boost Ticket", results)


def fetch_boost_ticket_ids_step(context) -> None:
    boost_claim_cases = context.get_records("boost_claim_cases")

    synthetic_ids = [
        record["synthetic_id"]
        for record in boost_claim_cases
    ]

    boost_claim_case_id_map = fetch_id_map(
        sf=context.sf,
        object_name="Boost_Claim_Case__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=synthetic_ids,
    )

    context.set_id_map("boost_claim_cases", boost_claim_case_id_map)

    print(f"Fetched {len(boost_claim_case_id_map)} Boost Ticket ID mappings.")


def update_boost_ticket_lookup_step(context) -> None:
    """
    Updates Boost__c.Boost_Claim_Case__c so existing flows that search
    Boost records by Boost_Claim_Case__c can find the related bills.
    """
    boost_claim_cases = context.get_records("boost_claim_cases")
    boost_claim_case_id_map = context.get_id_map("boost_claim_cases")

    boost_updates = []

    for ticket in boost_claim_cases:
        ticket_id = boost_claim_case_id_map.get(ticket["synthetic_id"])

        if not ticket_id:
            continue

        boost_synthetic_id = ticket["meta"]["boost_synthetic_id"]

        boost_updates.append({
            "object": "Boost__c",
            "synthetic_id": boost_synthetic_id,
            "fields": {
                SYNTHETIC_ID_FIELD: boost_synthetic_id,
                "Boost_Claim_Case__c": ticket_id,
            },
            "meta": {},
        })

    if not boost_updates:
        print("No Boost records to update with Boost Ticket lookup.")
        return

    print("Updating Boost records with Boost Ticket lookup...")

    results = upsert_records(
        sf=context.sf,
        object_name="Boost__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=boost_updates,
    )

    print_results("Boost Ticket lookup update", results)