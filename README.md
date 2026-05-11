# Salesforce Synthetic Data Pipeline

This repository generates and loads synthetic Salesforce test data for claim, bill, payment, ticket, case, payor, and related portal workflows.

The current testing environment is Noah's personal `nadev` sandbox.

The pipeline is intended to create realistic, rerunnable sandbox data across related Salesforce objects without manually creating records through the Salesforce UI.

## What this pipeline does

The pipeline creates synthetic records for major business areas:

- Clinic/client Accounts
- Child Accounts
- Contacts
- Boost Accounts / `ARN_Account__c`
- Boost Patient Claims / `Boost_Patient_Claim__c`
- Boost bills / `Boost__c`
- Lines / `Lines__c`
- CPT Codes / `CPT_Codes__c`
- Payor/Bill Review Accounts
- Payor Contacts
- ARN Payor Master / `ARN_Payor_Master__c`
- ARN Payors / `ARN_Payors__c`
- Deposits / `Deposit__c`
- Incoming Check Payments / `Incoming_Check_Payment__c`
- ARN Checks to Members / `ARN_Checks_to_Members__c`
- Check Payments / `Check_Payment__c`
- Boost Tickets / `Boost_Claim_Case__c`
- Cases / `Case`
- ARN Fees / `ARN_Fees__c`

Some optional or experimental objects, such as Uploads / `Upload__c`, may be disabled depending on Salesforce automation behavior.

## Repo structure

The repo is organized around this pattern:

```text
Generators → Pipeline → Salesforce
```

Typical structure:

```text
SF-Snowflake-Synthetic-Data/
├─ src/
│  ├─ main.py
│  ├─ config.py
│  ├─ generators/
│  ├─ pipeline/
│  ├─ loaders/
│  └─ exports/
├─ docs/
└─ README.md
```

## `src/main.py`

This is the entry point.

When you run:

```powershell
python -m src.main
```

it starts the pipeline.

This file should stay small and mostly delegate to the pipeline runner.

## `src/config.py`

This file controls pipeline settings.

Examples of settings that belong here:

```python
SEED
LOAD_TO_SALESFORCE
SYNTHETIC_ID_FIELD

SALESFORCE_BULK_UPSERT_ENABLED
SALESFORCE_BULK_BATCH_SIZE
SALESFORCE_BULK_USE_SERIAL
SALESFORCE_BULK_UPSERT_EXCLUDED_OBJECTS
```

It also includes object-specific generation settings, such as how many Cases to generate per Boost Ticket.

## `src/generators/`

This folder creates synthetic data.

Generator files should usually not talk to Salesforce. They should create Python dictionaries representing records.

Examples:

```text
src/generators/accounts.py
src/generators/boost_accounts.py
src/generators/boost_patient_claims.py
src/generators/boost.py
src/generators/lines.py
src/generators/cpt_codes.py
src/generators/deposits.py
src/generators/incoming_check_payments.py
src/generators/cases.py
src/generators/arn_fees.py
```

A generator answers:

```text
What should this fake record look like?
```

Example flat generated record:

```python
{
    "Synthetic_Id__c": "LINE-BOOST-000001-0001",
    "Name": "1",
    "Date_of_Service__c": "2026-01-15",
    "_boost_synthetic_id": "BOOST-000001",
    "_cpt_code": "97110"
}
```

Temporary lookup references often start with `_`, such as:

```python
_boost_synthetic_id
_cpt_code
```

These are not Salesforce fields. They are internal helper values used later by resolver steps.

## `src/generators/base.py`

This contains shared generator utilities, such as:

```python
fake
set_seed()
next_id()
```

This is what makes generated values stable or repeatable when the seed is the same.

Example:

```python
next_id("BACC")
```

might produce:

```text
BACC-000001
```

## `src/pipeline/`

This is the orchestration layer.

Pipeline files usually have functions like:

```python
generate_*_step()
resolve_*_step()
upsert_*_step()
fetch_*_ids_step()
```

Examples:

```text
src/pipeline/accounts.py
src/pipeline/boost_accounts.py
src/pipeline/boost.py
src/pipeline/lines.py
src/pipeline/cpt_codes.py
src/pipeline/cases.py
src/pipeline/arn_fees.py
```

The pipeline answers:

```text
When do we generate this object?
When do we resolve its lookups?
When do we load it?
When do we fetch Salesforce IDs for children?
```

## `src/pipeline/run.py`

This is the main conductor.

It controls the order of the entire pipeline.

This file is important because load order matters.

For example, Lines cannot be loaded until Boost records exist, because:

```text
Lines__c.Claim__c → Boost__c
```

Lines also cannot get CPT Code lookups until CPT Codes exist, because:

```text
Lines__c.CPT_Code__c → CPT_Codes__c
```

So `src/pipeline/run.py` is the dependency map in code form.

## `src/pipeline/context.py`

This defines `PipelineContext`.

The context is the shared memory for the pipeline run.

It stores generated records:

```python
context.set_records("boost", records)
context.get_records("boost")
```

It also stores Salesforce ID maps:

```python
context.set_id_map("boost", boost_id_map)
context.get_id_map("boost")
```

An ID map looks like this:

```python
{
    "BOOST-BPC-000001-0001": "a1UWA000001abc123"
}
```

That lets the pipeline resolve child lookups.

Example:

```python
line["Claim__c"] = boost_id_map[boost_sid]
```

## `src/loaders/`

This folder handles Salesforce communication.

The most important file is probably:

```text
src/loaders/salesforce.py
```

It contains helpers like:

```python
get_salesforce_client()
upsert_records()
fetch_id_map()
```

This folder answers:

```text
How do we connect to Salesforce?
How do we upsert records?
How do we fetch Salesforce IDs?
Should we use Bulk API or normal REST?
```

## `src/loaders/resolver.py`

This is where shared lookup-resolution helpers can live.

For example, Boost Account lookup update helpers may live here:

```python
build_boost_account_lookup_updates()
```

If multiple pipeline files need similar lookup logic, it can belong here or in `src/pipeline/helpers.py`.

## `src/loaders/salesforce.py`

`src/loaders/salesforce.py` is the file that connects the pipeline to Salesforce.

Most pipeline files do not log in to Salesforce directly. They use helper functions from this file.

## What this file does

This file handles:

```text
Salesforce login
Bulk upserts
REST upserts
Fetching Salesforce record IDs
```

The pipeline calls this file when it needs to:

```text
Connect to Salesforce
Insert or update records
Look up Salesforce IDs after records are loaded
```

## Salesforce credentials

This file loads credentials from `.env` using:

```python
load_dotenv()
```

The expected `.env` values are:

```env
SF_USERNAME=your-sandbox-username
SF_PASSWORD=your-password
SF_DOMAIN=test
```

Then provide either:

```env
SF_SECURITY_TOKEN=your-security-token
```

or:

```env
SF_ORGANIZATION_ID=your-org-id
```

For sandboxes, use:

```env
SF_DOMAIN=test
```

## `get_salesforce_client()`

This function creates the Salesforce connection.

```python
context.sf = get_salesforce_client()
```

This happens in `src/pipeline/run.py`.

If credentials are missing, the function raises an error such as:

```text
Missing SF_USERNAME in .env
Missing SF_PASSWORD in .env
Provide either SF_SECURITY_TOKEN or SF_ORGANIZATION_ID in .env
```

## Upserting records

The main helper is:

```python
upsert_records()
```

Pipeline files use it like this:

```python
results = upsert_records(
    sf=context.sf,
    object_name="ARN_Fees__c",
    external_id_field="Synthetic_Id__c",
    records=arn_fees,
)
```

This function decides whether to use:

```text
Bulk API
REST API
```

based on settings in `src/config.py`.


## Expected record format

`upsert_records()` expects wrapped records like this:

```python
{
    "object": "ARN_Fees__c",
    "synthetic_id": "ARNFEE-BACC-000001-PAYER-000001",
    "fields": {
        "Synthetic_Id__c": "ARNFEE-BACC-000001-PAYER-000001",
        "Boost_Account__c": "a1C...",
        "ARN_Payor__c": "a1P...",
        "Fees_percentage__c": 30
    },
    "meta": {
        "boost_account_synthetic_id": "BACC-000001",
        "arn_payor_synthetic_id": "PAYER-000001"
    }
}
```

Only the values inside `fields` are sent to Salesforce.

The `meta` values are only used by the pipeline to resolve relationships.

## Fetching Salesforce IDs

After records are upserted, child records often need the real Salesforce IDs of parent records.

That is what this function does:

```python
fetch_id_map()
```

Example:

```python
boost_id_map = fetch_id_map(
    sf=context.sf,
    object_name="Boost__c",
    external_id_field="Synthetic_Id__c",
    synthetic_ids=boost_synthetic_ids,
)
```

It returns a map like:

```python
{
    "BOOST-000001": "a1UWA000001abc123",
    "BOOST-000002": "a1UWA000001def456"
}
```

Then resolver steps can use it:

```python
line["Claim__c"] = boost_id_map[boost_sid]
```

## When setting up another sandbox

This is one of the main files to check.

To point the repo at another sandbox, update `.env`:

```env
SF_USERNAME=your-new-sandbox-username
SF_PASSWORD=your-password
SF_DOMAIN=test
SF_SECURITY_TOKEN=your-security-token
```

or:

```env
SF_USERNAME=your-new-sandbox-username
SF_PASSWORD=your-password
SF_DOMAIN=test
SF_ORGANIZATION_ID=your-org-id
```

Before running the full pipeline, test the connection:

```python
from src.loaders.salesforce import get_salesforce_client

sf = get_salesforce_client()

result = sf.query("""
    SELECT Id, Name, IsSandbox
    FROM Organization
    LIMIT 1
""")

print(result["records"])
```

Expected:

```text
IsSandbox = true
```

## `src/pipeline/helpers.py`

This contains reusable pipeline utilities.

Examples:

```python
print_results()
build_boost_account_id_by_parent_account()
build_account_root_parent_map()
```

This is for helper code used across pipeline steps.

## `src/exports/` or generated output

This area is for generated output files when the pipeline exports records.

The export step is useful when:

```python
LOAD_TO_SALESFORCE = False
```

or when you want to inspect generated records before loading them.

The relevant pipeline step is:

```python
export_generated_records_step(context)
```

## High-level pattern

The pipeline follows this pattern:

```text
Generators → Pipeline steps → Salesforce
```

Pipeline steps generally do the following:

1. Generate records.
2. Store them in `PipelineContext`.
3. Resolve synthetic references into real Salesforce IDs.
4. Upsert records into Salesforce.
5. Fetch Salesforce IDs into ID maps for child objects.

Example relationship pattern:

```text
Generate records with synthetic IDs
Insert/upsert parent records
Fetch parent Salesforce IDs
Use parent IDs for child lookup fields
Insert/upsert child records
```

## Synthetic IDs

Most generated records use a stable synthetic external ID so the pipeline can be rerun without creating duplicates.

Common external ID pattern:

```text
Synthetic_Id__c
```

Some objects already have their own external IDs:

| Object | External ID |
|---|---|
| `Deposit__c` | `Deposit_ID__c` |
| `Incoming_Check_Payment__c` | `Use_for_Transfer__c` |
| `ARN_Payors__c` | `Payer_ID__c` |
| `CPT_Codes__c` | `CPT_CODE_ID__c` |

If a new custom object does not have a stable external ID, add:

```text
Synthetic_Id__c
Text
External ID
Unique
```

Do not use display fields or auto-number fields as the pipeline key.

## Flat records vs wrapped records

Some generators produce flat records.

Example:

```python
{
    "Synthetic_Id__c": "LINE-001",
    "Name": "1",
    "_boost_synthetic_id": "BOOST-001"
}
```

Some generators produce wrapped records.

Example:

```python
{
    "object": "ARN_Fees__c",
    "synthetic_id": "ARNFEE-BACC-001-PAYER-001",
    "fields": {
        "Synthetic_Id__c": "ARNFEE-BACC-001-PAYER-001",
        "Fees_percentage__c": 30
    },
    "meta": {
        "boost_account_synthetic_id": "BACC-001",
        "arn_payor_synthetic_id": "PAYER-001"
    }
}
```

The newer pattern is the wrapped style because it keeps Salesforce fields separate from internal metadata.

## How relationships are handled

Generators should usually avoid using real Salesforce IDs.

Instead, they store synthetic references.

Example:

```python
"meta": {
    "boost_synthetic_id": "BOOST-000001",
    "boost_account_synthetic_id": "BACC-000001"
}
```

Then resolver steps use ID maps to set real lookup fields.

Example:

```python
record["fields"]["Boost__c"] = boost_id_map[boost_synthetic_id]
record["fields"]["Boost_Account__c"] = boost_account_id_map[boost_account_synthetic_id]
```

This is the core idea of the whole repo.

## How a new object usually gets added

A new object usually needs two files:

```text
src/generators/new_object.py
src/pipeline/new_object.py
```

Then it gets wired into:

```text
src/pipeline/run.py
```

For example, for `ARN_Fees__c`:

```text
src/generators/arn_fees.py
src/pipeline/arn_fees.py
```

Then in `run.py`:

```python
from src.pipeline.arn_fees import (
    generate_arn_fees_step,
    resolve_arn_fees_step,
    upsert_arn_fees_step,
    fetch_arn_fee_ids_step,
)
```

And later:

```python
generate_arn_fees_step(context)
resolve_arn_fees_step(context)
upsert_arn_fees_step(context)
fetch_arn_fee_ids_step(context)
```

## The four-step object pattern

Most objects follow this pattern:

### 1. Generate

Create fake records.

```python
generate_cases_step(context)
```

### 2. Resolve

Convert synthetic references into Salesforce IDs.

```python
resolve_cases_step(context)
```

Example:

```python
case["fields"]["Bill__c"] = boost_id_map[boost_synthetic_id]
```

### 3. Upsert

Load the records into Salesforce.

```python
upsert_cases_step(context)
```

### 4. Fetch IDs

Store IDs for child objects.

```python
fetch_case_ids_step(context)
```

Not all objects need all four steps.

For example, if nothing else depends on an object's ID, you may not need a fetch step.

## How to run

From the repo root:

```powershell
$start = Get-Date
python -m src.main
$end = Get-Date
"Pipeline completed in $([math]::Round(($end - $start).TotalSeconds, 2)) seconds"
```

## Export-only mode

The pipeline can be configured to generate/export records without loading to Salesforce.

Check this setting in `src/config.py`:

```python
LOAD_TO_SALESFORCE
```

If `LOAD_TO_SALESFORCE = False`, the pipeline generates records and exports output without loading to Salesforce.

## Important safety notes

This pipeline can trigger Salesforce automation.

Before running large loads:

- Confirm you are connected to the intended sandbox.
- Do not run this directly against production.
- Review console output for upsert failures.
- Consider restricting sandbox email deliverability.
- Avoid generating real-looking emails.
- Avoid generating Case comment fields that trigger notification flows.

## Known automation-sensitive areas

### Cases and Case Comments

Generated Case comment fields previously caused real Case Comment records to be created by sandbox automation.

The sandbox `New Case Comment` flow then sent emails.

Those emails bounced and were picked up by production Email-to-Case.

Mitigation:

- Do not generate `Most_Recent_Case_Comment__c`.
- Do not generate `Comments`.
- Use blank or non-routable emails such as `@example.invalid`.
- Consider pausing or guarding sandbox Case Comment email flows during bulk loads.

### Cases and Bulk API

Cases are excluded from Bulk upsert because Case automation can hit email invocation limits.


## Simple explanation for another developer

This repo creates a synthetic Salesforce data graph.

It does not just insert random records.

It creates parent records, fetches their Salesforce IDs, and then uses those IDs to create related child records.

The most important files are:

```text
src/pipeline/run.py       # overall order
src/config.py             # settings
src/generators/           # fake data
src/pipeline/             # load/resolve steps
src/loaders/salesforce.py # Salesforce API operations
```

The most important concept is:

```text
Synthetic IDs are used during generation.
Salesforce IDs are fetched after upsert.
Resolver steps convert synthetic references into Salesforce lookup fields.
```

That is the heart of the pipeline.