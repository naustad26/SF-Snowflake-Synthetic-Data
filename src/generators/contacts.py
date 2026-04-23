# Generator for synthetic contact data associated with accounts
import random
from .base import fake, next_id, generate_phone

CONTACT_TITLES = [
    "Owner",
    "Office Manager",
    "Billing Manager",
    "Clinic Director",
    "Practice Administrator",
    "Revenue Cycle Manager",
]

# Keep these as resolver-friendly source values for now.
# Later you may want to switch these to usernames/emails instead of display names.
CONTACT_OWNERS = [
    "Daniel Brodie",
    "Lisa Selden",
]

# Keep these as source labels for now.
# Later, using DeveloperName-style keys would be safer than labels.
CONTACT_RECORD_TYPES = [
    "Case Manager/Adjuster",
    "Customer",
    "Prospect",
    "Referral Source",
    "Vendor",
]

CONTACT_STATUSES = [
    "Active",
    "Deceased",
    "Moved",
    "Retired",
    "Do Not Market",
    "Account Inactive",
    "Not Qualified",
    "Treat as Lead",
]


def domain_from_website(website: str) -> str:
    return (
        website.replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .strip("/")
    )


def weighted_contact_status(account_fields: dict) -> str:
    if account_fields["Account_Status__c"] == "Inactive":
        return random.choices(
            CONTACT_STATUSES,
            weights=[35, 1, 5, 8, 10, 30, 4, 7],
            k=1,
        )[0]

    return random.choices(
        CONTACT_STATUSES,
        weights=[88, 1, 2, 2, 2, 1, 1, 3],
        k=1,
    )[0]


def weighted_contact_record_type(account_fields: dict) -> str:
    customer_types = account_fields["Customer_Type__c"].split(";")

    if "Boost" in customer_types or "ARN Member" in customer_types:
        return random.choices(
            CONTACT_RECORD_TYPES,
            weights=[30, 50, 8, 7, 5],
            k=1,
        )[0]

    return random.choices(
        CONTACT_RECORD_TYPES,
        weights=[25, 35, 20, 10, 10],
        k=1,
    )[0]


def generate_contact_fields(account_fields: dict, first_name: str, last_name: str) -> dict:
    domain = domain_from_website(account_fields["Website"])

    use_account_address = random.choices([True, False], weights=[80, 20], k=1)[0]

    if use_account_address:
        mailing_street = account_fields["BillingStreet"]
        mailing_city = account_fields["BillingCity"]
        mailing_state = account_fields["BillingState"]
        mailing_postal = account_fields["BillingPostalCode"]
    else:
        mailing_street = fake.street_address()
        mailing_city = fake.city()
        mailing_state = fake.state_abbr()
        mailing_postal = fake.postcode()

    return {
        "FirstName": first_name,
        "LastName": last_name,
        "Title": random.choice(CONTACT_TITLES),
        "MailingStreet": mailing_street,
        "MailingCity": mailing_city,
        "MailingState": mailing_state,
        "MailingPostalCode": mailing_postal,
        "Email": f"{first_name.lower()}.{last_name.lower()}@{domain}",
        "Phone": generate_phone(),
    }


def generate_contact_for_account(account: dict) -> dict:
    """
    Expects account in canonical format, e.g.
    {
        "object": "Account",
        "synthetic_id": "ACC000001",
        "fields": {...}
    }
    """
    account_fields = account["fields"]

    first_name = fake.first_name()
    last_name = fake.last_name()
    synthetic_id = next_id("CON")

    return {
        "object": "Contact",
        "synthetic_id": synthetic_id,
        "parent_refs": {
            "Account": account["synthetic_id"],
        },
        "fields": {
            "Synthetic_Id__c": synthetic_id,
            **generate_contact_fields(account_fields, first_name, last_name),
        },
        "meta": {
            "full_name": f"{first_name} {last_name}",
            "account_name": account_fields["Name"],
            "contact_owner_name": random.choice(CONTACT_OWNERS),
            "contact_record_type_name": weighted_contact_record_type(account_fields),
            "contact_status": weighted_contact_status(account_fields),
        },
    }


def generate_contacts_for_accounts(
    accounts: list[dict],
    min_per_account: int = 1,
    max_per_account: int = 4,
) -> list[dict]:
    contacts: list[dict] = []

    for account in accounts:
        contact_count = random.randint(min_per_account, max_per_account)
        for _ in range(contact_count):
            contacts.append(generate_contact_for_account(account))

    return contacts