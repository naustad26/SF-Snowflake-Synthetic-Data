from src.config import (
    CASE_PROBABILITY_PER_BOOST_TICKET,
    MIN_CASES_PER_SELECTED_BOOST_TICKET,
    MAX_CASES_PER_SELECTED_BOOST_TICKET,
    SYNTHETIC_ID_FIELD,
)

try:
    from src.config import CASE_RECORD_TYPE_DEVELOPER_NAME
except ImportError:
    CASE_RECORD_TYPE_DEVELOPER_NAME = None

from src.generators.cases import generate_case_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


def fetch_case_record_type_id_by_developer_name(sf, developer_name: str) -> str:
    escaped_developer_name = developer_name.replace("'", "\\'")

    query = f"""
        SELECT Id, DeveloperName
        FROM RecordType
        WHERE SObjectType = 'Case'
        AND DeveloperName = '{escaped_developer_name}'
        LIMIT 1
    """

    result = sf.query(query)
    records = result.get("records", [])

    if not records:
        raise ValueError(
            "Could not find Case RecordType with DeveloperName "
            f"'{developer_name}'. Check Setup > Object Manager > Case > Record Types."
        )

    return records[0]["Id"]


def generate_cases_step(context) -> None:
    boost_claim_cases = context.get_records("boost_claim_cases")
    contacts = context.get_records("contacts")

    cases = generate_case_records(
        boost_claim_cases=boost_claim_cases,
        contacts=contacts,
        case_probability_per_boost_ticket=CASE_PROBABILITY_PER_BOOST_TICKET,
        min_cases_per_selected_boost_ticket=MIN_CASES_PER_SELECTED_BOOST_TICKET,
        max_cases_per_selected_boost_ticket=MAX_CASES_PER_SELECTED_BOOST_TICKET,
    )

    context.set_records("cases", cases)

    print(f"Generated {len(cases)} Case records")


def resolve_cases_step(context) -> None:
    cases = context.get_records("cases")

    boost_claim_case_id_map = context.get_id_map("boost_claim_cases")
    contact_id_map = context.get_id_map("contacts")
    account_id_map = context.get_id_map("all_accounts")
    boost_id_map = context.get_id_map("boost")
    boost_patient_claim_id_map = context.get_id_map("boost_patient_claims")

    record_type_id = None

    if CASE_RECORD_TYPE_DEVELOPER_NAME:
        record_type_id = fetch_case_record_type_id_by_developer_name(
            sf=context.sf,
            developer_name=CASE_RECORD_TYPE_DEVELOPER_NAME,
        )

    resolved_cases = []

    for case in cases:
        boost_ticket_synthetic_id = case["meta"].get("boost_ticket_synthetic_id")
        boost_synthetic_id = case["meta"].get("boost_synthetic_id")
        boost_patient_claim_synthetic_id = case["meta"].get(
            "boost_patient_claim_synthetic_id"
        )
        contact_synthetic_id = case["meta"].get("contact_synthetic_id")
        account_synthetic_id = case["meta"].get("account_synthetic_id")

        if record_type_id:
            case["fields"]["RecordTypeId"] = record_type_id

        if boost_ticket_synthetic_id:
            boost_ticket_id = boost_claim_case_id_map.get(boost_ticket_synthetic_id)

            if boost_ticket_id:
                # Case has both fields. Populate both for first pass.
                case["fields"]["Boost_Claim_Case__c"] = boost_ticket_id

        if boost_synthetic_id:
            boost_id = boost_id_map.get(boost_synthetic_id)

            if boost_id:
                case["fields"]["Bill__c"] = boost_id

        if boost_patient_claim_synthetic_id:
            boost_patient_claim_id = boost_patient_claim_id_map.get(
                boost_patient_claim_synthetic_id
            )

            if boost_patient_claim_id:
                case["fields"]["Boost_Patient_Claim__c"] = boost_patient_claim_id

        if account_synthetic_id:
            account_id = account_id_map.get(account_synthetic_id)

            if account_id:
                case["fields"]["AccountId"] = account_id

        if contact_synthetic_id:
            contact_id = contact_id_map.get(contact_synthetic_id)

            if contact_id:
                case["fields"]["ContactId"] = contact_id

        resolved_cases.append(case)

    context.set_records("cases", resolved_cases)


def upsert_cases_step(context) -> None:
    cases = context.get_records("cases")

    print("Upserting Case records...")

    results = upsert_records(
        sf=context.sf,
        object_name="Case",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=cases,
    )

    print_results("Case", results)


def fetch_case_ids_step(context) -> None:
    cases = context.get_records("cases")

    synthetic_ids = [
        case["synthetic_id"]
        for case in cases
    ]

    case_id_map = fetch_id_map(
        sf=context.sf,
        object_name="Case",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=synthetic_ids,
    )

    context.set_id_map("cases", case_id_map)

    print(f"Fetched {len(case_id_map)} Case ID mappings.")