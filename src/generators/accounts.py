# Generator for synthetic account data
import random
from .base import fake, next_id, generate_phone

ACCOUNT_STATUSES = ["Active", "Inactive"]

CUSTOMER_TYPES = [
    "ARN Member",
    "Boost",
    "Marketing",
    "Other",
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

LOCATION_SUFFIXES = [
    "Flint",
    "Grand Blanc",
    "Lansing",
    "Detroit",
    "Ann Arbor",
    "Saginaw",
    "Bay City",
    "Troy",
    "Livonia",
    "Novi",
]


def weighted_account_status() -> str:
    return random.choices(ACCOUNT_STATUSES, weights=[95, 5], k=1)[0]


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


def generate_account_addresses() -> tuple[dict, bool]:
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

    addresses = {
        "BillingStreet": billing_street,
        "BillingCity": billing_city,
        "BillingState": billing_state,
        "BillingPostalCode": billing_postal,
        "ShippingStreet": shipping_street,
        "ShippingCity": shipping_city,
        "ShippingState": shipping_state,
        "ShippingPostalCode": shipping_postal,
    }

    return addresses, same_shipping


def generate_account_fields(name: str) -> tuple[dict, bool]:
    addresses, same_shipping = generate_account_addresses()

    fields = {
        "Name": name,
        "Phone": generate_phone(),
        "Website": generate_website(name),
        **addresses,
        "Account_Status__c": weighted_account_status(),
        "Customer_Type__c": generate_customer_type(),
        "Billing_Type__c": weighted_billing_type(),
        "Main_Point_of_Contact__c": fake.name(),
        "Software_EMR_being_used__c": random.choice(EMR_OPTIONS),
        "Number_of_Years_in_Business__c": random.randint(1, 40),
        "Other_notes__c": generate_notes(),
    }

    return fields, same_shipping


def generate_location_account(parent_account: dict, city: str) -> dict:
    synthetic_id = next_id("ACC")
    parent_fields = parent_account["fields"]
    parent_name = parent_fields["Name"]

    name = f"{parent_name} - {city}"

    fields, same_shipping = generate_account_fields(name)

    # Keep customer type similar to parent for realism
    fields["Customer_Type__c"] = parent_fields["Customer_Type__c"]
    fields["Account_Status__c"] = parent_fields["Account_Status__c"]

    return {
        "object": "Account",
        "synthetic_id": synthetic_id,
        "parent_refs": {
            "Account": parent_account["synthetic_id"],
        },
        "fields": {
            "Synthetic_Id__c": synthetic_id,
            **fields,
        },
        "meta": {
            "is_location_account": True,
            "parent_account_name": parent_name,
            "same_shipping_as_billing": same_shipping,
        },
    }


def generate_account_hierarchy(
    parent_count: int,
    min_children_per_parent: int = 0,
    max_children_per_parent: int = 4,
) -> tuple[list[dict], list[dict]]:
    parent_accounts: list[dict] = []
    child_accounts: list[dict] = []

    for _ in range(parent_count):
        parent = generate_account()

        child_count = random.randint(min_children_per_parent, max_children_per_parent)
        parent["fields"]["Child_Accounts__c"] = child_count
        parent["meta"]["is_parent_account"] = True

        parent_accounts.append(parent)

        if child_count > 0:
            cities = random.sample(
                LOCATION_SUFFIXES,
                k=min(child_count, len(LOCATION_SUFFIXES)),
            )

            for city in cities:
                child_accounts.append(generate_location_account(parent, city))

    return parent_accounts, child_accounts


def generate_account() -> dict:
    synthetic_id = next_id("ACC")
    name = generate_company_name()
    fields, same_shipping = generate_account_fields(name)

    return {
        "object": "Account",
        "synthetic_id": synthetic_id,
        "fields": {
            "Synthetic_Id__c": synthetic_id,
            **fields,
        },
        "meta": {
            "same_shipping_as_billing": same_shipping,
        },
    }


def generate_accounts(count: int) -> list[dict]:
    return [generate_account() for _ in range(count)]