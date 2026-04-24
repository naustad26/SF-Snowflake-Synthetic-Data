import random
from .base import fake, next_id

BANK_ACCOUNT_TYPES = [
    "Checking",
    "Savings",
]

CLEARINGHOUSES = [
    "Availity",
    "Office Ally",
    "Waystar",
    "Change Healthcare",
    "TriZetto",
    "Claim.MD",
]


def generate_tax_id() -> str:
    return f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"


def generate_routing_number() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(9))


def generate_bank_account_number() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(random.randint(8, 12)))


def generate_boost_account_for_parent_account(parent_account: dict) -> dict:
    synthetic_id = next_id("BACC")
    parent_fields = parent_account["fields"]

    active = parent_fields.get("Account_Status__c") == "Active"
    ach = random.choices([True, False], weights=[75, 25], k=1)[0]

    return {
        "object": "ARN_Account__c",
        "synthetic_id": synthetic_id,
        "account_refs": {
            "Accounts": [parent_account["synthetic_id"]],
        },
        "fields": {
            "Synthetic_Id__c": synthetic_id,
            "Name": parent_fields["Name"],
            "Tax_ID__c": generate_tax_id(),
            "ACH__c": ach,
            "Active__c": active,
            "Important_Notes_Uploads__c": random.choice([
                "Uploads generally received monthly.",
                "Client occasionally requires follow-up on missing files.",
                "High-volume billing account.",
                "Monitor payer mix and monthly claim volume.",
            ]),
            "Monthly_Average__c": random.randint(50, 800),
            "Bank_Name__c": fake.company() + " Bank",
            "Bank_Account_Number__c": generate_bank_account_number(),
            "Bank_Routing_Transit_Number__c": generate_routing_number(),
            "Bank_Account_Type__c": random.choice(BANK_ACCOUNT_TYPES),
            "Name_on_Bank_Account__c": parent_fields["Name"],
            "Clearinghouse_Used__c": random.choice(CLEARINGHOUSES),
            "BS_VIP__c": random.choices([True, False], weights=[10, 90], k=1)[0],
            "Percentage_of_Claims__c": round(random.uniform(40, 100), 2),
            "EOR_Method__c": random.choice([
                "Portal",
                "Email",
                "Clearinghouse",
                "SFTP",
            ]),
            "Actual_Amount__c": random.randint(10000, 250000),
            "BS_Bill_count_Last_Month__c": random.randint(20, 500),
        },
        "meta": {
            "source_parent_account": parent_account["synthetic_id"],
        },
    }


def generate_boost_accounts_for_parent_accounts(
    parent_accounts: list[dict],
) -> list[dict]:
    return [
        generate_boost_account_for_parent_account(parent)
        for parent in parent_accounts
    ]