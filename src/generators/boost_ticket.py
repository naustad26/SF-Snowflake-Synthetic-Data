import random
from datetime import date, timedelta
from faker import Faker

fake = Faker()


BOOST_TICKET_STATUSES = [
    "Open",
    "Waiting For Payor",
    'Waiting For Member',
    "Escalated"
]


NEXT_STEP_METHODS = [
    "Review",
    "Call",
    "Email",
    "Portal",
    "Review Case Comment",
    "Resubmit",
]


SUBJECT_PATTERNS = [
    "Status Inquiry {date1}, {date2}, {date3}",
    "{payor} BILL RECEIVED",
    "Status Inquiry- All {month} DOS",
    "{date1}, {date2} & {date3} Status Inquiry",
    "Attorney records request",
    "CC Payment received - Multiple Pts - Need Paper check ${amount}",
    "Chk {check_number} - Need DOS",
    "APPEAL - {dos} - {code}",
    "CLAIM CONFIRMATION NEEDED FROM MEMBER",
    "Payment received - need to confirm DOS",
    "Payer status request - no response received",
    "Rebill needed due to payer rejection",
]


PAYOR_NAMES = [
    "CIGNA",
    "BCBS",
    "Sedgwick",
    "State Farm",
    "Progressive",
    "Liberty Mutual",
    "Travelers",
    "Auto-Owners",
    "United Healthcare",
    "Aetna",
]


CPT_CODES = [
    "97110",
    "97112",
    "97140",
    "97530",
    "97535",
    "99203",
    "99213",
]


MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
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


def _short_date() -> str:
    generated_date = fake.date_between(start_date="-180d", end_date="today")
    return f"{generated_date.month}/{generated_date.day}"


def _full_dos_date() -> str:
    generated_date = fake.date_between(start_date="-365d", end_date="today")
    return generated_date.strftime("%m/%d/%y")


def _future_follow_up_date() -> str:
    return (
        date.today()
        + timedelta(days=random.randint(7, 45))
    ).isoformat()


def _generate_subject() -> str:
    pattern = random.choice(SUBJECT_PATTERNS)

    return pattern.format(
        date1=_short_date(),
        date2=_short_date(),
        date3=_short_date(),
        payor=random.choice(PAYOR_NAMES),
        month=random.choice(MONTHS),
        amount=round(random.uniform(100, 2500), 2),
        check_number=str(random.randint(100000, 999999)),
        dos=_full_dos_date(),
        code=random.choice(CPT_CODES),
    )[:80]


def _generate_description(subject: str) -> str:
    templates = [
        (
            "Need to determine if this check is paying for one of the open dates of service. "
            "The amount appears to match an EOB in house, but there is no clear indicator "
            "connecting the check to the bill."
        ),
        (
            "Please review payer response and confirm whether the bill should be appealed, "
            "rebilled, or monitored for additional payment."
        ),
        (
            "Member/provider requested a status update. Review claim activity, payer notes, "
            "and any recent payments before responding."
        ),
        (
            "Payer rejected or delayed processing. Verify submission method, payer ID, and "
            "claim details before next outreach."
        ),
        (
            "Appeal requested for non-payment or reduction. Review documentation, coding, "
            "medical records, and payer explanation before submitting."
        ),
    ]

    if "APPEAL" in subject.upper():
        return (
            "PLEASE APPEAL THE NON-PAYMENT OR REDUCTION FOR THE LISTED DATE OF SERVICE. "
            "Review the clinical notes, plan of care, and payer response before sending. "
            "Update the ticket with payer response and next expected action."
        )

    if "CHECK" in subject.upper() or "CHK" in subject.upper() or "PAYMENT" in subject.upper():
        return (
            "Need to determine which date of service this payment belongs to. "
            "Review check details, EOBs, billed charges, and open outstanding balances. "
            "Post payment or document mismatch as appropriate."
        )

    return random.choice(templates)


def _generate_recent_update() -> str:
    update_date = _short_date()

    updates = [
        "Reviewed payer response and updated claim notes.",
        "Called payer for status. Claim is still under review.",
        "Payment appears received but needs to be matched to DOS.",
        "Reviewed EOB and confirmed partial payment.",
        "Appeal status requested. Awaiting payer response.",
        "Member/provider update reviewed and next action documented.",
        "Claim needs additional follow-up before closure.",
    ]

    return f"{update_date}- {random.choice(updates)}"


def _generate_next_steps(status: str) -> str:
    if status == "Closed":
        return "Closed Ticket."

    next_steps = [
        "Call payer for status and update ticket with response.",
        "Review EOB and determine whether appeal or rebill is needed.",
        "Monitor for payment and follow up if nothing is received.",
        "Email payer contact for claim status and document response.",
        "Post payment details, update outstanding amount, and reassign if needed.",
        "Review related bills and confirm whether all open DOS are accounted for.",
        "Send appeal or status inquiry, then set follow-up date.",
    ]

    return random.choice(next_steps)


def generate_boost_claim_case_records(
    boost_records,
    ticket_probability: float,
    min_tickets_per_selected_boost: int,
    max_tickets_per_selected_boost: int,
):
    records = []

    if not boost_records:
        raise ValueError("Cannot generate Boost Tickets without Boost records.")

    ticket_index = 1

    for boost in boost_records:
        if random.random() > ticket_probability:
            continue

        boost_synthetic_id = _get_synthetic_id(boost)

        boost_account_synthetic_id = (
            _get_meta(boost, "boost_account_synthetic_id")
            or _get_field(boost, "_boost_account_synthetic_id")
            or _get_field(boost, "ARN_Account__c")
        )

        boost_patient_claim_synthetic_id = (
            _get_meta(boost, "boost_patient_claim_synthetic_id")
            or _get_field(boost, "_boost_patient_claim_synthetic_id")
        )

        ticket_count = random.randint(
            min_tickets_per_selected_boost,
            max_tickets_per_selected_boost,
        )

        for ticket_number in range(ticket_count):
            synthetic_id = f"BT-{boost_synthetic_id}-{ticket_number + 1:03d}"

            subject = _generate_subject()
            status = random.choices(
                population=BOOST_TICKET_STATUSES,
                weights=[70, 10, 10, 10],
                k=1,
            )[0]

            fields = {
                "Synthetic_Id__c": synthetic_id,
                "Name": subject,

                "Status__c": status,

                "Description__c": _generate_description(subject),
                "More_Recent_Update__c": _generate_recent_update(),
                "Next_steps__c": _generate_next_steps(status),
                "Next_Step_Method__c": random.choice(NEXT_STEP_METHODS),

                "Follow_up_date__c": None if status == "Closed" else _future_follow_up_date(),

                "Date_Of_Service__c": random.choice([
                    _full_dos_date(),
                    f"{_full_dos_date()}, {_full_dos_date()}",
                    "Multiple DOS",
                    "All open DOS",
                    None,
                ]),

                "Open_Bills_Related_to_Ticket__c": random.randint(0, 5),
                "Open_Tasks_Related_to_Ticket__c": random.randint(0, 3),

                "Thread_Token__c": f"ref:boost-ticket:{synthetic_id}",
            }

            records.append({
                "object": "Boost_Claim_Case__c",
                "synthetic_id": synthetic_id,
                "fields": fields,
                "meta": {
                    "boost_synthetic_id": boost_synthetic_id,
                    "boost_account_synthetic_id": boost_account_synthetic_id,
                    "boost_patient_claim_synthetic_id": boost_patient_claim_synthetic_id,
                },
            })

            ticket_index += 1

    return records