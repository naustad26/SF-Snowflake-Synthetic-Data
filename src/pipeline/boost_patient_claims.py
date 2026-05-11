import random
from src.generators.boost_patient_claims import generate_boost_patient_claim_records
from src.config import SYNTHETIC_ID_FIELD
from src.loaders.salesforce import upsert_records
from src.pipeline.helpers import print_results

def generate_boost_patient_claims_step(context):
    boost_accounts = context.get_records("boost_accounts")

    boost_patient_claims = generate_boost_patient_claim_records(
        boost_accounts
    )

    context.set_records("boost_patient_claims", boost_patient_claims)


def resolve_boost_patient_claims_step(context):
    boost_account_id_map = context.get_id_map("boost_accounts")
    boost_patient_claims = context.get_records("boost_patient_claims")

    for claim in boost_patient_claims:
        boost_account_sid = claim.pop("_boost_account_synthetic_id")
        claim["ARN_Account__c"] = boost_account_id_map[boost_account_sid]

    context.set_records("boost_patient_claims", boost_patient_claims)


def upsert_boost_patient_claims_step(context):
    records = context.get_records("boost_patient_claims")

    if not records:
        print("No Boost Patient Claims to upsert")
        return

    results = context.sf.bulk.Boost_Patient_Claim__c.upsert(
        records,
        "Synthetic_Id__c"
    )

    successes = [r for r in results if r.get("success")]
    failures = [r for r in results if not r.get("success")]

    print(
        f"Boost Patient Claim upsert complete. "
        f"Success: {len(successes)}, Failed: {len(failures)}"
    )

    if failures:
        print("Boost Patient Claim failures:")
        print(failures[:5])
        

def update_boost_patient_claim_arn_payor_master_lookup_step(context) -> None:
    boost_patient_claims = context.get_records("boost_patient_claims")
    arn_payor_master_id_map = context.get_id_map("arn_payor_master")

    if not boost_patient_claims:
        print("No Boost Patient Claims to update with ARN Payor Master")
        return

    if not arn_payor_master_id_map:
        raise ValueError(
            "Cannot update Boost Patient Claims with ARN Payor Master because "
            "arn_payor_master ID map is empty."
        )

    arn_payor_master_ids = list(arn_payor_master_id_map.values())

    updates = []

    for claim in boost_patient_claims:
        claim_synthetic_id = claim["Synthetic_Id__c"]

        updates.append({
            "object": "Boost_Patient_Claim__c",
            "synthetic_id": claim_synthetic_id,
            "fields": {
                SYNTHETIC_ID_FIELD: claim_synthetic_id,
                "ARN_Payor_Master__c": random.choice(arn_payor_master_ids),
            },
            "meta": {},
        })

    print("Updating Boost Patient Claims with ARN Payor Master lookup...")

    results = upsert_records(
        sf=context.sf,
        object_name="Boost_Patient_Claim__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=updates,
    )

    print_results("Boost Patient Claim ARN Payor Master lookup update", results)