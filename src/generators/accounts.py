# Generator for synthetic account data
import random
from .base import fake, next_id, generate_phone

ACCOUNT_STATUSES = ["Active", "Inactive"]

CUSTOMER_TYPES = [
    "ARN Member",
    "Boost",
    "Marketing",
    "Other",
    "Consulting",
    "Billing",
]

COMPANY_SUFFIXES = [
    "Physical Therapy",
    "Rehabilitation",
    "Rehab Center",
    "Therapy Group",
    "PT Clinic",
    "Rehab Services",
]

BILLING_TYPES = [
    "Billing company",
    "in-house billing",
]

EMR_OPTIONS = [
    "WebPT",
    "Epic",
    "athenahealth",
    "Clinicient",
    "Prompt EMR",
    "Raintree",
    "Other",
]


def weighted_account_status() -> str:
    return random.choices(ACCOUNT_STATUSES, weights=[85, 15], k=1)[0]


def weighted_billing_type() -> str:
    return random.choices(BILLING_TYPES, weights=[75, 25], k=1)[0]


def generate_customer_type() -> str:
    count = random.choices([1, 2], weights=[80, 20], k=1)[0]
    values = random.sample(CUSTOMER_TYPES, count)
    return ";".join(values)


def generate_company_name() -> str:
    return f"{fake.last_name()} {random.choice(COMPANY_SUFFIXES)}"


def generate_website(name: str) -> str:
    base = name.lower().replace(" ", "").replace(",", "")
    return f"https://www.{base}.com"


def generate_notes() -> str:
    templates = [
        "Client focused on improving billing efficiency and reducing denials.",
        "Recently onboarded, still in early implementation phase.",
        "High volume clinic with steady monthly billing.",
        "Interested in expanding services and improving payer mix.",
    ]
    return random.choice(templates)


def generate_account() -> dict:
    name = generate_company_name()

    billing_street = fake.street_address()
    billing_city = fake.city()
    billing_state = fake.state_abbr()
    billing_postal = fake.postcode()

    same_shipping = random.choice([True, False])

    if same_shipping:
        shipping_street = billing_street
        shipping_city = billing_city
        shipping_state = billing_state
        shipping_postal = billing_postal
    else:
        shipping_street = fake.street_address()
        shipping_city = fake.city()
        shipping_state = fake.state_abbr()
        shipping_postal = fake.postcode()

    return {
        "SyntheticId": next_id("ACC"),
        "Name": name,
        "Phone": generate_phone(),
        "Website": generate_website(name),
        "BillingStreet": billing_street,
        "BillingCity": billing_city,
        "BillingState": billing_state,
        "BillingPostalCode": billing_postal,
        "ShippingStreet": shipping_street,
        "ShippingCity": shipping_city,
        "ShippingState": shipping_state,
        "ShippingPostalCode": shipping_postal,
        "Account_Status__c": weighted_account_status(),
        "Customer_Type__c": generate_customer_type(),
        "Billing_Type__c": weighted_billing_type(),
        "Main_Point_of_Contact__c": fake.name(),
        "Software_EMR_being_used__c": random.choice(EMR_OPTIONS),
        "Number_of_Years_in_Business__c": random.randint(1, 40),
        "Other_notes__c": generate_notes(),
    }


def generate_accounts(count: int) -> list[dict]:
    return [generate_account() for _ in range(count)]