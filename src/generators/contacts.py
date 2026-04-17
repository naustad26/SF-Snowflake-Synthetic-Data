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

CONTACT_OWNERS = [
    "Daniel Brodie",
    "Lisa Selden",
]

CONTACT_RECORD_TYPES = [
    "Case Manager/Adjuster",
    "Customer",
    "Prospect",
    "Referral Source",
    "Vendor"
]

CONTACT_STATUSES = [
    "Active",
    "Deceased",
    "Moved",
    "Retired",
    "Do Not Market",
    "Account Inactive",
    "Not Qualified",
    "Treat as Lead"
]

def domain_from_website(website: str) -> str:
    return (
        website.replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .strip("/")
    )

def weighted_contact_status(account: dict) -> str:
    if account["Account_Status__c"] == "Inactive":
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


def weighted_contact_record_type(account: dict) -> str:
    customer_types = account["Customer_Type__c"].split(";")

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

def generate_contact_for_account(account: dict) -> dict:
    first_name = fake.first_name()
    last_name = fake.last_name()
    domain = domain_from_website(account["Website"])

    use_account_address = random.choices([True, False], weights=[80, 20], k=1)[0]

    if use_account_address:
        mailing_street = account["BillingStreet"]
        mailing_city = account["BillingCity"]
        mailing_state = account["BillingState"]
        mailing_postal = account["BillingPostalCode"]
    else:
        mailing_street = fake.street_address()
        mailing_city = fake.city()
        mailing_state = fake.state_abbr()
        mailing_postal = fake.postcode()

    return {
        "SyntheticId": next_id("CON"),
        "FirstName": first_name,
        "LastName": last_name,
        "Name": f"{first_name} {last_name}",
        "Title": random.choice(CONTACT_TITLES),
        "MailingStreet": mailing_street,
        "MailingCity": mailing_city,
        "MailingState": mailing_state,
        "MailingPostalCode": mailing_postal,
        "Email": f"{first_name.lower()}.{last_name.lower()}@{domain}",
        "Phone": generate_phone(),
        "AccountSyntheticId": account["SyntheticId"],
        "AccountName": account["Name"],
        "ContactOwnerName": random.choice(CONTACT_OWNERS),
        "ContactRecordType": weighted_contact_record_type(account),
        "Physican_Status": weighted_contact_status(account),
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