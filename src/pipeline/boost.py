from src.generators.boost import generate_boost_records


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