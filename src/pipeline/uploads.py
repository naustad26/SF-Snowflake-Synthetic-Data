from src.config import SYNTHETIC_ID_FIELD
from src.generators.uploads import generate_upload_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


def generate_uploads_step(context) -> None:
    boost_accounts = context.get_records("boost_accounts")

    uploads = generate_upload_records(
        boost_accounts=boost_accounts,
        min_uploads_per_boost_account=0,
        max_uploads_per_boost_account=2,
        upload_probability=0.75,
    )

    context.set_records("uploads", uploads)

    print(f"Generated {len(uploads)} Upload records")


def resolve_uploads_step(context) -> None:
    uploads = context.get_records("uploads")

    if not uploads:
        print("No Upload records to resolve")
        return

    boost_account_id_map = context.get_id_map("boost_accounts")
    account_id_map = context.get_id_map("parent_accounts")

    for upload in uploads:
        boost_account_sid = upload["meta"]["boost_account_synthetic_id"]
        account_sid = upload["meta"]["account_synthetic_id"]

        upload["fields"]["Boost_Account__c"] = boost_account_id_map[boost_account_sid]
        upload["fields"]["Account__c"] = account_id_map[account_sid]

    context.set_records("uploads", uploads)


def upsert_uploads_step(context) -> None:
    uploads = context.get_records("uploads")

    if not uploads:
        print("No Upload records to upsert")
        return

    print("Sample resolved Upload payload:")
    print(uploads[0])

    print("Upserting Uploads...")

    results = upsert_records(
        sf=context.sf,
        object_name="Upload__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=uploads,
    )

    print_results("Upload", results)


def fetch_upload_ids_step(context) -> None:
    uploads = context.get_records("uploads")

    if not uploads:
        context.set_id_map("uploads", {})
        return

    upload_synthetic_ids = [
        upload["synthetic_id"]
        for upload in uploads
    ]

    upload_id_map = fetch_id_map(
        sf=context.sf,
        object_name="Upload__c",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=upload_synthetic_ids,
    )

    context.set_id_map("uploads", upload_id_map)