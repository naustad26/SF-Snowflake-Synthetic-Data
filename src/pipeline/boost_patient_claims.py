from src.generators.boost_patient_claims import generate_boost_patient_claim_records


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

    context.sf.bulk.Boost_Patient_Claim__c.upsert(
        records,
        "Synthetic_Id__c"
    )

    print(f"Upserted {len(records)} Boost Patient Claims")