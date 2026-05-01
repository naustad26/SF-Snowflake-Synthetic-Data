from src.config import SEED, LOAD_TO_SALESFORCE
from src.generators.base import set_seed
from src.loaders.salesforce import get_salesforce_client
from src.pipeline.context import PipelineContext

from src.pipeline.accounts import (
    generate_account_hierarchy_step,
    resolve_parent_accounts_boost_lookup_step,
    upsert_parent_accounts_step,
    resolve_child_accounts_step,
    upsert_child_accounts_step,
    fetch_all_account_ids_step,
)

from src.pipeline.boost_accounts import (
    generate_boost_accounts_step,
    upsert_boost_accounts_step,
    update_boost_account_lookup_fields_step,
)

from src.pipeline.contacts import (
    generate_contacts_step,
    resolve_contacts_step,
    upsert_contacts_step,
)

from src.pipeline.boost_patient_claims import (
    generate_boost_patient_claims_step,
    resolve_boost_patient_claims_step,
    upsert_boost_patient_claims_step,
)

from src.pipeline.exports import export_generated_records_step


def run_pipeline() -> None:
    set_seed(SEED)

    context = PipelineContext()

    # Generate synthetic records
    generate_account_hierarchy_step(context)
    generate_boost_accounts_step(context)
    generate_contacts_step(context)
    generate_boost_patient_claims_step(context)

    export_generated_records_step(context)

    if not LOAD_TO_SALESFORCE:
        print("Export only mode")
        return

    context.sf = get_salesforce_client()

    # Boost Accounts first (dependency root)
    upsert_boost_accounts_step(context)

    # IMPORTANT: requires boost_accounts ID map to exist
    resolve_boost_patient_claims_step(context)
    upsert_boost_patient_claims_step(context)

    # Parent Accounts
    resolve_parent_accounts_boost_lookup_step(context)
    upsert_parent_accounts_step(context)

    # Child Accounts
    resolve_child_accounts_step(context)
    upsert_child_accounts_step(context)

    # Fetch Account IDs
    fetch_all_account_ids_step(context)

    # Contacts
    resolve_contacts_step(context)
    upsert_contacts_step(context)

    # Final Boost Account updates
    update_boost_account_lookup_fields_step(context)