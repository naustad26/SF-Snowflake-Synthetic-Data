from datetime import date, timedelta
import random

from src.generators.boost import generate_boost_records
from src.config import SYNTHETIC_ID_FIELD
from src.loaders.salesforce import upsert_records
from src.pipeline.helpers import print_results


def generate_boost_step(context):
    claims = context.get_records("boost_patient_claims")

    records = generate_boost_records(claims)

    context.set_records("boost", records)


def resolve_boost_step(context):
    boost_account_map = context.get_id_map("boost_accounts")
    claim_map = context.get_id_map("boost_patient_claims")

    records = context.get_records("boost")

    for r in records:
        r["ARN_Account__c"] = boost_account_map[
            r.pop("_boost_account_synthetic_id")
        ]

        r["Boost_Patient_Claim__c"] = claim_map[
            r.pop("_boost_patient_claim_synthetic_id")
        ]

    context.set_records("boost", records)


def upsert_boost_step(context):
    records = context.get_records("boost")

    if not records:
        print("No Boost records to upsert")
        return

    results = context.sf.bulk.Boost__c.upsert(
        records,
        "Synthetic_Id__c"
    )

    successes = [r for r in results if r.get("success")]
    failures = [r for r in results if not r.get("success")]

    print(
        f"Boost upsert complete. "
        f"Success: {len(successes)}, Failed: {len(failures)}"
    )

    if failures:
        print("Boost failures:")
        print(failures[:5])

def update_boost_arn_payor_lookup_step(context) -> None:
    boost_records = context.get_records("boost")
    arn_payor_id_map = context.get_id_map("arn_payors")

    if not arn_payor_id_map:
        raise ValueError("Cannot update Boost ARN_Payor__c because arn_payors ID map is empty.")

    arn_payor_ids = list(arn_payor_id_map.values())

    boost_updates = []

    for boost in boost_records:
        boost_synthetic_id = boost["Synthetic_Id__c"]

        boost_updates.append({
            "object": "Boost__c",
            "synthetic_id": boost_synthetic_id,
            "fields": {
                SYNTHETIC_ID_FIELD: boost_synthetic_id,
                "ARN_Payor__c": random.choice(arn_payor_ids),
            },
            "meta": {},
        })

    print("Updating Boost ARN Payor lookup fields...")

    results = upsert_records(
        sf=context.sf,
        object_name="Boost__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=boost_updates,
    )

    print_results("Boost ARN Payor lookup update", results)


def generate_uploaded_date() -> str:
    # Match your current pattern: sometime between 365 and 30 days ago.
    days_ago = random.randint(30, 365)
    return (date.today() - timedelta(days=days_ago)).isoformat()

def update_missing_boost_uploaded_dates_step(context) -> None:
    boost_records = context.get_records("boost")

    if not boost_records:
        print("No Boost records found for Uploaded__c update")
        return

    boost_synthetic_ids = [
        r["Synthetic_Id__c"]
        for r in boost_records
        if r.get("Synthetic_Id__c")
    ]

    if not boost_synthetic_ids:
        print("No Boost Synthetic IDs found for Uploaded__c update")
        return

    quoted_ids = ",".join(f"'{sid}'" for sid in boost_synthetic_ids)

    query = f"""
        SELECT Id, Synthetic_Id__c, Uploaded__c
        FROM Boost__c
        WHERE Synthetic_Id__c IN ({quoted_ids})
    """

    existing_boosts = context.sf.query_all(query)["records"]

    boost_updates = []

    for boost in existing_boosts:
        if boost.get("Uploaded__c"):
            continue

        synthetic_id = boost["Synthetic_Id__c"]

        boost_updates.append({
            "object": "Boost__c",
            "synthetic_id": synthetic_id,
            "fields": {
                SYNTHETIC_ID_FIELD: synthetic_id,
                "Uploaded__c": generate_uploaded_date(),
            },
            "meta": {},
        })

    if not boost_updates:
        print("No missing Boost Uploaded__c values to update")
        return

    print(f"Updating Uploaded__c for {len(boost_updates)} Boost records...")

    results = upsert_records(
        sf=context.sf,
        object_name="Boost__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=boost_updates,
    )

    print_results("Boost Uploaded__c update", results)