import random
from datetime import date, timedelta
from faker import Faker

fake = Faker()


CASE_STATUSES = [
    "New ARN Response",
    "New Member Response",
    "Member Working",
    "New Member Case",
    "ARN Working",
    "New ARN Case",
    "On Hold",
    "New",
    "In Progress",
    "Waiting for Customer",
    "Escalated",
    "Response Received",
]

CASE_ORIGINS = [
    "Status Request",
    "Appeal",
    "Other",
    "Denial Received",
    "Information Requested",
    "Payment",
    "Email",
    "Utilization Review",
    "Chatter",
    "Submission Form",
]

CASE_PRIORITIES = [
    "Low",
    "Medium",
    "High",
]

CASE_TYPES = [
    "Fax Recieved",
    "Member Case",
    "Payor Case",
    "Other",
    "Check Payment"
]

CASE_REASONS = [
    "Status",
    "Appeal",
    "Denial Received",
    "Information Requested",
    "Other",
]


def _get_field(record, field_name: str, default=None):
    if "fields" in record:
        return record["fields"].get(field_name, default)

    return record.get(field_name, default)


def _get_synthetic_id(record) -> str:
    if "synthetic_id" in record:
        return record["synthetic_id"]

    if "fields" in record:
        return record["fields"]["Synthetic_Id__c"]

    return record["Synthetic_Id__c"]


def _get_meta(record, key: str, default=None):
    return record.get("meta", {}).get(key, default)


def _future_follow_up_date() -> str:
    return (
        date.today()
        + timedelta(days=random.randint(3, 45))
    ).isoformat()


def _generate_subject(origin: str) -> str:
    if origin == "Appeal":
        return random.choice([
            "Appeal documentation requested",
            "Appeal follow-up needed",
            "Appeal status request",
            "Appeal response received",
        ])

    if origin == "Payment":
        return random.choice([
            "Payment received - review needed",
            "Need EOB/payment clarification",
            "Check received - need DOS",
            "Payment mismatch review",
            "CC payment received - review needed",
        ])

    if origin == "Denial Received":
        return random.choice([
            "Denial received - next steps needed",
            "Denial review requested",
            "Review denial and determine appeal",
        ])

    if origin == "Information Requested":
        return random.choice([
            "Information requested by payer",
            "Medical records requested",
            "Need claim documentation",
        ])

    if origin == "Status Request":
        return random.choice([
            "Status request for claim",
            "Provider requesting status",
            "Member requesting update",
            "Claim status inquiry",
        ])

    return random.choice([
        "Member response received",
        "ARN response needed",
        "Claim confirmation needed from member",
        "Provider follow-up requested",
        "Case created from portal request",
    ])


def _generate_description(origin: str) -> str:
    if origin == "Appeal":
        return (
            "Appeal-related case. Review denial details, documentation, medical records, "
            "related Boost Ticket notes, and payer response before next action."
        )

    if origin == "Payment":
        return (
            "Payment-related case. Review check/EOB details and determine whether payment "
            "should be posted, reconciled, or escalated."
        )

    if origin == "Denial Received":
        return (
            "Denial received. Review payer reason, affected DOS, and determine whether "
            "appeal, rebill, or member follow-up is needed."
        )

    if origin == "Information Requested":
        return (
            "Payer or member requested additional information. Review documents needed "
            "and update the related Boost Ticket."
        )

    if origin == "Status Request":
        return (
            "Status inquiry received. Confirm current payer status, related bills, and "
            "ticket notes before responding."
        )

    return (
        "Case generated for related Boost workflow. Review associated ticket, claim, "
        "and bill details before next action."
    )



def _select_contact_for_case(contacts):
    if not contacts:
        return None

    return random.choice(contacts)


def generate_case_records(
    boost_claim_cases,
    contacts,
    case_probability_per_boost_ticket: float,
    min_cases_per_selected_boost_ticket: int,
    max_cases_per_selected_boost_ticket: int,
):
    records = []

    if not boost_claim_cases:
        raise ValueError("Cannot generate Cases without Boost Ticket records.")

    for boost_ticket in boost_claim_cases:
        if random.random() > case_probability_per_boost_ticket:
            continue

        boost_ticket_synthetic_id = _get_synthetic_id(boost_ticket)

        boost_synthetic_id = _get_meta(boost_ticket, "boost_synthetic_id")
        boost_patient_claim_synthetic_id = _get_meta(
            boost_ticket,
            "boost_patient_claim_synthetic_id",
        )
        boost_account_synthetic_id = _get_meta(
            boost_ticket,
            "boost_account_synthetic_id",
        )

        selected_contact = _select_contact_for_case(contacts)

        contact_synthetic_id = None
        account_synthetic_id = None

        if selected_contact:
            contact_synthetic_id = _get_synthetic_id(selected_contact)

            account_synthetic_id = (
                _get_meta(selected_contact, "account_synthetic_id")
                or _get_meta(selected_contact, "parent_account_synthetic_id")
                or _get_meta(selected_contact, "child_account_synthetic_id")
                or _get_field(selected_contact, "_account_synthetic_id")
            )

        case_count = random.randint(
            min_cases_per_selected_boost_ticket,
            max_cases_per_selected_boost_ticket,
        )

        for case_number in range(case_count):
            origin = random.choice(CASE_ORIGINS)

            status = random.choices(
                population=CASE_STATUSES,
                weights=[4, 4, 10, 5, 12, 5, 7, 10, 22, 8, 5, 8],
                k=1,
            )[0]

            synthetic_id = f"CASE-{boost_ticket_synthetic_id}-{case_number + 1:03d}"

            supplied_name = fake.name()
            supplied_email = f"synthetic.case.{synthetic_id.lower()}@example.invalid"

            fields = {
                "Synthetic_Id__c": synthetic_id,

                "Subject": _generate_subject(origin),
                "Status": status,
                "Origin": origin,
                "Priority": random.choice(CASE_PRIORITIES),

                "Description": _generate_description(origin),
                "Follow_up_Date__c": _future_follow_up_date(),

                "SuppliedName": supplied_name,
                "SuppliedEmail": supplied_email,
                "SuppliedPhone": fake.numerify(text="###-###-####"),
                "SuppliedCompany": fake.company(),
            }

            fields["Type"] = random.choice(CASE_TYPES)
            fields["Reason"] = random.choice(CASE_REASONS)

            records.append({
                "object": "Case",
                "synthetic_id": synthetic_id,
                "fields": fields,
                "meta": {
                    "boost_ticket_synthetic_id": boost_ticket_synthetic_id,
                    "boost_synthetic_id": boost_synthetic_id,
                    "boost_patient_claim_synthetic_id": boost_patient_claim_synthetic_id,
                    "boost_account_synthetic_id": boost_account_synthetic_id,
                    "contact_synthetic_id": contact_synthetic_id,
                    "account_synthetic_id": account_synthetic_id,
                },
            })

    return records