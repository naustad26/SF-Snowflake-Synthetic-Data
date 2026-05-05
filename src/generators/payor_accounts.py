import random
from faker import Faker

fake = Faker()


PAYOR_ACCOUNT_PREFIXES = [
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
    "Sterling",
    "Guardian",
    "Apex",
    "Meridian",
    "Cobalt",
]

PAYOR_ACCOUNT_SUFFIXES = [
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
    "Bill Review",
    "Claims Management",
    "Review Services",
]


def generate_payor_account_name() -> str:
    return f"{random.choice(PAYOR_ACCOUNT_PREFIXES)} {random.choice(PAYOR_ACCOUNT_SUFFIXES)}"


def generate_payor_account_records(count: int):
    records = []

    for i in range(count):
        synthetic_id = f"PAYOR-ACCT-{i + 1:06d}"

        fields = {
            "Synthetic_Id__c": synthetic_id,
            "Name": generate_payor_account_name(),

            # Basic Account fields.
            "BillingStreet": fake.street_address(),
            "BillingCity": fake.city(),
            "BillingState": fake.state_abbr(),
            "BillingPostalCode": fake.zipcode(),
            "BillingCountry": "USA",

            "Phone": fake.numerify(text="###-###-####"),
            "Website": fake.url(),

            # Do NOT populate client/clinic-specific fields here.
            # Do NOT populate Boost Account lookup here.
            # Do NOT populate ParentId here.
            # RecordTypeId is resolved later in the pipeline.
        }

        records.append({
            "object": "Account",
            "synthetic_id": synthetic_id,
            "fields": fields,
            "meta": {
                "account_role": "payor_bill_review",
            },
        })

    return records