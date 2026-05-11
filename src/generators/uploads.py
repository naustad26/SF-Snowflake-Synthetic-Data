import random
from .base import fake, next_id


ARN_PROCESSING_STATUSES = [
    "Completed",
]

UPLOAD_STATUSES = [
    "Complete",
]


UPLOAD_COMMENTS = [
    None,
    "",
    "Files uploaded for processing.",
    "Upload reviewed and routed for processing.",
    "Client upload received.",
    "Additional documentation uploaded by client.",
    "Upload package ready for ARN review.",
]


def generate_upload_for_boost_account(boost_account: dict, index: int) -> dict:
    synthetic_id = next_id("UPLOAD")

    boost_account_sid = boost_account["synthetic_id"]

    parent_account_sid = boost_account.get("meta", {}).get("source_parent_account")

    if not parent_account_sid:
        raise ValueError(
            f"Boost Account {boost_account_sid} is missing meta.source_parent_account"
        )

    return {
        "object": "Upload__c",
        "synthetic_id": synthetic_id,
        "fields": {
            "Synthetic_Id__c": synthetic_id,

            # Do not set Name.
            # Upload__c.Name is Auto Number, e.g. UN-00272.

            "ARN_Processing_Status__c": random.choice(ARN_PROCESSING_STATUSES),
            "Status__c": random.choice(UPLOAD_STATUSES),
            "Comments__c": random.choice(UPLOAD_COMMENTS),
        },
        "meta": {
            "boost_account_synthetic_id": boost_account_sid,
            "account_synthetic_id": parent_account_sid,
        },
    }


def generate_upload_records(
    boost_accounts: list[dict],
    min_uploads_per_boost_account: int = 0,
    max_uploads_per_boost_account: int = 2,
    upload_probability: float = 0.75,
) -> list[dict]:
    records = []

    for boost_account in boost_accounts:
        if random.random() > upload_probability:
            continue

        upload_count = random.randint(
            min_uploads_per_boost_account,
            max_uploads_per_boost_account,
        )

        for i in range(upload_count):
            records.append(
                generate_upload_for_boost_account(
                    boost_account=boost_account,
                    index=i,
                )
            )

    return records