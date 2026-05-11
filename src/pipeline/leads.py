from src.config import SYNTHETIC_ID_FIELD, LEAD_COUNT
from src.generators.leads import generate_lead_records
from src.loaders.salesforce import upsert_records, fetch_id_map
from src.pipeline.helpers import print_results


def generate_leads_step(context) -> None:
    leads = generate_lead_records(
        count=LEAD_COUNT,
    )

    context.set_records("leads", leads)

    print(f"Generated {len(leads)} Lead records")


def upsert_leads_step(context) -> None:
    leads = context.get_records("leads")

    if not leads:
        print("No Lead records to upsert")
        return

    print("Upserting Lead records...")

    results = upsert_records(
        sf=context.sf,
        object_name="Lead",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=leads,
    )

    print_results("Lead", results)


def fetch_lead_ids_step(context) -> None:
    leads = context.get_records("leads")

    if not leads:
        context.set_id_map("leads", {})
        return

    lead_synthetic_ids = [
        lead["synthetic_id"]
        for lead in leads
    ]

    lead_id_map = fetch_id_map(
        sf=context.sf,
        object_name="Lead",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=lead_synthetic_ids,
    )

    context.set_id_map("leads", lead_id_map)

    print(f"Fetched {len(lead_id_map)} Lead ID mappings.")