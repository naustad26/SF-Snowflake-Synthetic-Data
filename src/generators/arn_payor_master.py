import random
from faker import Faker

fake = Faker()

PAYOR_TYPES = [
    "WC",
    "Auto",
    "Commercial",
    "Personal Injury (PIP)",
]

BOOST_PAYOR_STATUSES = [
    "Accepted",
    "Not Accepted",
    "Archive",
]

PRIMARY_STATUS_METHODS = [
    "EMAIL",
    "PHONE",
    "PORTAL",
]

PREFERRED_SUBMISSION_METHODS = [
    "Mail",
    "Fax",
    "Email",
    "EDI",
]

CLAIM_SPECIFIC_VALUES = [
    "No",
    "Yes",
]

PAYOR_NAME_PREFIXES = [
    "Great Lakes",
    "Summit",
    "Pioneer",
    "MetroCare",
    "Northstar",
    "Evergreen",
    "Lakeshore",
    "Blue Ridge",
    "Ironwood",
    "Cedar Valley",
    "Oakline",
    "Harbor",
    "Keystone",
    "Riverbend",
    "Mapleview",
]

PAYOR_NAME_SUFFIXES = [
    "Mutual",
    "Claims",
    "Insurance",
    "Casualty",
    "Health Plan",
    "Administrators",
    "Benefits",
    "Risk Group",
    "Indemnity",
    "Assurance",
]


def generate_payor_name() -> str:
    return f"{random.choice(PAYOR_NAME_PREFIXES)} {random.choice(PAYOR_NAME_SUFFIXES)}"


def generate_type_value() -> str:
    selected_count = random.choices(
        population=[1, 2, 3],
        weights=[70, 25, 5],
        k=1,
    )[0]

    selected_types = random.sample(PAYOR_TYPES, selected_count)
    return ";".join(selected_types)


def generate_arn_payor_master_records(payor_accounts, count: int):
    records = []

    if not payor_accounts:
        raise ValueError("Cannot generate ARN Payor Master records without Payor/Bill Review Accounts.")

    for i in range(count):
        payor_account = random.choice(payor_accounts)

        payor_account_sid = payor_account["synthetic_id"]

        submission_method = random.choice(PREFERRED_SUBMISSION_METHODS)

        email_for_appeals = fake.company_email()
        email_for_bill_submission = fake.company_email()
        email_for_status_inquiry = fake.company_email()

        fax = fake.numerify(text="###-###-####")
        phone = fake.numerify(text="###-###-####")

        if submission_method == "Email":
            preferred_address = email_for_bill_submission
        else:
            preferred_address = None

        synthetic_id = f"APM-{i + 1:06d}"

        fields = {
            "Synthetic_Id__c": synthetic_id,
            "Name": generate_payor_name(),

            "Type__c": generate_type_value(),

            "Mailing_Street__c": fake.street_address(),
            "Mailing_City__c": fake.city(),
            "Mailing_State__c": fake.state_abbr(),
            "Mailing_Zip__c": fake.zipcode(),

            "Email_for_Appeals__c": email_for_appeals,
            "Email_for_bill_submission__c": email_for_bill_submission,
            "Email_For_Status_Inquiry__c": email_for_status_inquiry,

            "Boost_Payor_Status__c": random.choices(
                population=BOOST_PAYOR_STATUSES,
                weights=[80, 15, 5],
                k=1,
            )[0],

            "Primary_Status_Method__c": random.choice(PRIMARY_STATUS_METHODS),

            "Email__c": fake.company_email(),
            "Phone__c": phone,
            "Fax__c": fax,

            "Active_With_Boost__c": random.choices(
                population=[True, False],
                weights=[85, 15],
                k=1,
            )[0],

            "Preferred_Method_to_Submit_Claims__c": submission_method,
            "Preferred_Method_Fax_or_Email_Address__c": preferred_address,

            "Claim_Specific__c": random.choice(CLAIM_SPECIFIC_VALUES),
        }

        records.append({
            "object": "ARN_Payor_Master__c",
            "synthetic_id": synthetic_id,
            "fields": fields,
            "meta": {
                "payor_account_synthetic_id": payor_account_sid,
            },
        })

    return records