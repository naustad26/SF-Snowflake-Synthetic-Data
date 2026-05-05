import random
from faker import Faker

fake = Faker()


PAYOR_CONTACT_TITLES = [
    "Claims Adjuster",
    "Senior Claims Adjuster",
    "Bill Review Specialist",
    "Claims Examiner",
    "Claims Supervisor",
    "Utilization Review Coordinator",
    "Appeals Coordinator",
    "EDI Contact",
    "Provider Relations Representative",
    "Payment Processing Specialist",
    "Claims Manager",
]


def generate_payor_contact_records(
    payor_accounts,
    min_contacts_per_account: int,
    max_contacts_per_account: int,
):
    records = []

    if not payor_accounts:
        raise ValueError("Cannot generate Payor Contacts without Payor/Bill Review Accounts.")

    for account in payor_accounts:
        account_synthetic_id = account["synthetic_id"]

        contact_count = random.randint(
            min_contacts_per_account,
            max_contacts_per_account,
        )

        for i in range(contact_count):
            synthetic_id = f"PAYOR-CON-{account_synthetic_id}-{i + 1:03d}"

            first_name = fake.first_name()
            last_name = fake.last_name()

            fields = {
                "Synthetic_Id__c": synthetic_id,
                "FirstName": first_name,
                "LastName": last_name,
                "Email": fake.email(),
                "Phone": fake.numerify(text="###-###-####"),
                "MobilePhone": fake.numerify(text="###-###-####"),
                "Title": random.choice(PAYOR_CONTACT_TITLES),
            }

            records.append({
                "object": "Contact",
                "synthetic_id": synthetic_id,
                "fields": fields,
                "meta": {
                    "payor_account_synthetic_id": account_synthetic_id,
                    "contact_role": "payor_bill_review",
                },
            })

    return records