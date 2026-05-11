from src.generators.cpt_codes import generate_cpt_code_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


CPT_CODE_EXTERNAL_ID_FIELD = "CPT_CODE_ID__c"


def generate_cpt_codes_step(context) -> None:
    cpt_codes = generate_cpt_code_records()

    context.set_records("cpt_codes", cpt_codes)

    print(f"Generated {len(cpt_codes)} CPT Code records")


def upsert_cpt_codes_step(context) -> None:
    cpt_codes = context.get_records("cpt_codes")

    if not cpt_codes:
        print("No CPT Code records to upsert")
        return

    print("Upserting CPT Code records...")

    results = upsert_records(
        sf=context.sf,
        object_name="CPT_Codes__c",
        external_id_field=CPT_CODE_EXTERNAL_ID_FIELD,
        records=cpt_codes,
    )

    print_results("CPT Code", results)


def fetch_cpt_code_ids_step(context) -> None:
    cpt_codes = context.get_records("cpt_codes")

    if not cpt_codes:
        context.set_id_map("cpt_codes", {})
        return

    cpt_code_external_ids = [
        record["synthetic_id"]
        for record in cpt_codes
    ]

    cpt_code_id_map = fetch_id_map(
        sf=context.sf,
        object_name="CPT_Codes__c",
        external_id_field=CPT_CODE_EXTERNAL_ID_FIELD,
        synthetic_ids=cpt_code_external_ids,
    )

    context.set_id_map("cpt_codes", cpt_code_id_map)

    print(f"Fetched {len(cpt_code_id_map)} CPT Code ID mappings.")