from multiprocessing import context

from src.config import SEED, LOAD_TO_SALESFORCE
from src.generators.base import set_seed
from src.loaders.salesforce import fetch_id_map, get_salesforce_client
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
    update_boost_patient_claim_arn_payor_master_lookup_step,
)

from src.pipeline.exports import export_generated_records_step

from src.pipeline.boost import (
    generate_boost_step,
    resolve_boost_step,
    upsert_boost_step,
    update_boost_arn_payor_lookup_step,
    update_missing_boost_uploaded_dates_step,
)

from src.pipeline.lines import (
    generate_lines_step,
    resolve_lines_step,
    upsert_lines_step,
)

from src.pipeline.arn_payor_master import (
    generate_arn_payor_master_step,
    resolve_arn_payor_master_step,
    upsert_arn_payor_master_step,
    fetch_arn_payor_master_ids_step,
)

from src.pipeline.arn_payors import (
    generate_arn_payors_step,
    resolve_arn_payors_step,
    upsert_arn_payors_step,
    fetch_arn_payor_ids_step,
)

from src.pipeline.payor_accounts import (
    generate_payor_accounts_step,
    resolve_payor_accounts_step,
    upsert_payor_accounts_step,
    fetch_payor_account_ids_step,
)

from src.pipeline.payor_contacts import (
    generate_payor_contacts_step,
    resolve_payor_contacts_step,
    upsert_payor_contacts_step,
    fetch_payor_contact_ids_step,
)

from src.pipeline.deposits import (
    generate_deposits_step,
    resolve_deposits_step,
    upsert_deposits_step,
    fetch_deposit_ids_step,
)

from src.pipeline.incoming_check_payments import (
    generate_incoming_check_payments_step,
    resolve_incoming_check_payments_step,
    upsert_incoming_check_payments_step,
    fetch_incoming_check_payment_ids_step,
)

from src.pipeline.boost_ticket import (
    generate_boost_ticket_step,
    resolve_boost_ticket_step,
    upsert_boost_ticket_step,
    fetch_boost_ticket_ids_step,
    update_boost_ticket_lookup_step,
)

from src.pipeline.cases import (
    generate_cases_step,
    resolve_cases_step,
    upsert_cases_step,
    fetch_case_ids_step,
)

from src.pipeline.arn_checks_to_members import (
    generate_arn_checks_to_members_step,
    resolve_arn_checks_to_members_step,
    upsert_arn_checks_to_members_step,
    fetch_arn_check_to_member_ids_step,
)

from src.pipeline.check_payments import (
    generate_check_payments_step,
    resolve_check_payments_step,
    upsert_check_payments_step,
    fetch_check_payment_ids_step,
)

from src.pipeline.cpt_codes import (
    generate_cpt_codes_step,
    upsert_cpt_codes_step,
    fetch_cpt_code_ids_step,
)

from src.pipeline.arn_fees import (
    generate_arn_fees_step,
    resolve_arn_fees_step,
    upsert_arn_fees_step,
    fetch_arn_fee_ids_step,
)

from src.pipeline.leads import (
    generate_leads_step,
    upsert_leads_step,
    fetch_lead_ids_step,
)


def run_pipeline() -> None:
    set_seed(SEED)

    context = PipelineContext()


    # Generate synthetic records
    generate_cpt_codes_step(context)
    generate_leads_step(context)
    generate_account_hierarchy_step(context)
    generate_payor_accounts_step(context)

    generate_boost_accounts_step(context)
    generate_contacts_step(context)
    generate_payor_contacts_step(context)

    generate_boost_patient_claims_step(context)
    generate_boost_step(context)
    generate_boost_ticket_step(context)
    generate_cases_step(context)

    generate_lines_step(context)
    generate_deposits_step(context)
    generate_arn_checks_to_members_step(context)
    generate_incoming_check_payments_step(context)
    generate_check_payments_step(context)

    generate_arn_payor_master_step(context)

    export_generated_records_step(context)

    if not LOAD_TO_SALESFORCE:
        print("Export only mode")
        return

    context.sf = get_salesforce_client()

    # Leads
    upsert_leads_step(context)
    fetch_lead_ids_step(context)

    # CPT Codes / reference data
    upsert_cpt_codes_step(context)
    fetch_cpt_code_ids_step(context)

    # Boost Accounts first
    upsert_boost_accounts_step(context)

    # Boost Patient Claims
    resolve_boost_patient_claims_step(context)
    upsert_boost_patient_claims_step(context)

    boost_patient_claim_synthetic_ids = [
        claim["Synthetic_Id__c"]
        for claim in context.get_records("boost_patient_claims")
    ]

    context.set_id_map(
        "boost_patient_claims",
        fetch_id_map(
            context.sf,
            "Boost_Patient_Claim__c",
            "Synthetic_Id__c",
            boost_patient_claim_synthetic_ids,
        )
    )

    # Boost
    resolve_boost_step(context)
    upsert_boost_step(context)

    boost_synthetic_ids = [
        boost["Synthetic_Id__c"]
        for boost in context.get_records("boost")
    ]

    context.set_id_map(
        "boost",
        fetch_id_map(
            context.sf,
            "Boost__c",
            "Synthetic_Id__c",
            boost_synthetic_ids,
        )
    )

    update_missing_boost_uploaded_dates_step(context)

    # Deposits
    resolve_deposits_step(context)
    upsert_deposits_step(context)
    fetch_deposit_ids_step(context)

    # Lines
    resolve_lines_step(context)
    upsert_lines_step(context)

    # Parent Accounts
    resolve_parent_accounts_boost_lookup_step(context)
    upsert_parent_accounts_step(context)

    # Child Accounts
    resolve_child_accounts_step(context)
    upsert_child_accounts_step(context)

    # Fetch clinic/client Account IDs
    fetch_all_account_ids_step(context)

    # ARN Checks to Members
    resolve_arn_checks_to_members_step(context)
    upsert_arn_checks_to_members_step(context)
    fetch_arn_check_to_member_ids_step(context)

    # Incoming Check Payments
    resolve_incoming_check_payments_step(context)
    upsert_incoming_check_payments_step(context)
    fetch_incoming_check_payment_ids_step(context)

    # Check Payments
    resolve_check_payments_step(context)
    upsert_check_payments_step(context)
    fetch_check_payment_ids_step(context)

    # Clinic/client Contacts
    resolve_contacts_step(context)
    upsert_contacts_step(context)

    # Payor / Bill Review Accounts
    resolve_payor_accounts_step(context)
    upsert_payor_accounts_step(context)
    fetch_payor_account_ids_step(context)

    # Payor Contacts
    resolve_payor_contacts_step(context)
    upsert_payor_contacts_step(context)
    fetch_payor_contact_ids_step(context)

    # ARN Payor Master
    resolve_arn_payor_master_step(context)
    upsert_arn_payor_master_step(context)
    fetch_arn_payor_master_ids_step(context)

    # ARN Payors
    generate_arn_payors_step(context)
    resolve_arn_payors_step(context)
    upsert_arn_payors_step(context)
    fetch_arn_payor_ids_step(context)

    update_boost_patient_claim_arn_payor_master_lookup_step(context)

    # ARN Fees
    generate_arn_fees_step(context)
    resolve_arn_fees_step(context)
    upsert_arn_fees_step(context)
    fetch_arn_fee_ids_step(context)

    # Boost Tickets
    resolve_boost_ticket_step(context)
    upsert_boost_ticket_step(context)
    fetch_boost_ticket_ids_step(context)
    update_boost_ticket_lookup_step(context)

    # Cases
    resolve_cases_step(context)
    upsert_cases_step(context)
    fetch_case_ids_step(context)

    # Update Boost ARN Payor lookup
    update_boost_arn_payor_lookup_step(context)

    # Final Boost Account updates
    update_boost_account_lookup_fields_step(context)