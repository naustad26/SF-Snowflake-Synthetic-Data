import random

from .base import fake, next_id


LEAD_STATUSES = [
    "Open - Not Contacted",
    "Working - Contacted",
]

LEAD_SOURCES = [
    "Web",
    "Referral",
    "Phone Inquiry",
    "Conference",
    "Synthetic Data",
]

CLINIC_COMPANY_SUFFIXES = [
    "Physical Therapy",
    "Rehab",
    "Therapy Center",
    "Sports Medicine",
    "Wellness Clinic",
]


def generate_lead_company_name() -> str:
    return f"{fake.last_name()} {random.choice(CLINIC_COMPANY_SUFFIXES)}"


def generate_lead_records(
    count: int = 25,
) -> list[dict]:
    records = []

    for _ in range(count):
        synthetic_id = next_id("LEAD")

        first_name = fake.first_name()
        last_name = fake.last_name()
        company = generate_lead_company_name()

        records.append({
            "object": "Lead",
            "synthetic_id": synthetic_id,
            "fields": {
                "Synthetic_Id__c": synthetic_id,

                "FirstName": first_name,
                "LastName": last_name,
                "Company": company,

                # Use non-routable emails so lead automation cannot email real people.
                "Email": f"synthetic.lead.{synthetic_id.lower()}@example.invalid",

                "Phone": fake.numerify(text="###-###-####"),
                "Status": random.choice(LEAD_STATUSES),
                "LeadSource": random.choice(LEAD_SOURCES),

                "Title": random.choice([
                    "Owner",
                    "Clinic Manager",
                    "Billing Manager",
                    "Office Manager",
                    "Practice Administrator",
                ]),

                "Street": fake.street_address(),
                "City": fake.city(),
                "State": fake.state_abbr(),
                "PostalCode": fake.postcode(),
                "Country": "United States",
            },
            "meta": {},
        })

    return records