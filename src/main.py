from src.config import (
    SEED,
    ACCOUNT_COUNT,
    OUTPUT_DIR,
    EXPORT_RAW_DATA,
    LOAD_TO_SALESFORCE,
    SYNTHETIC_ID_FIELD,
)
from src.generators.base import set_seed
from src.generators.accounts import generate_accounts
from src.exporters import export_raw_records
from src.loaders.salesforce import get_salesforce_client, upsert_records, fetch_id_map


def main() -> None:
    set_seed(SEED)

    accounts = generate_accounts(ACCOUNT_COUNT)

    if EXPORT_RAW_DATA:
        export_raw_records(accounts, "accounts_raw.json", OUTPUT_DIR)

    print(f"Generated {len(accounts)} account records.")

    if not LOAD_TO_SALESFORCE:
        print("Load disabled. Export only mode.")
        return

    sf = get_salesforce_client()

    print("Upserting Accounts...")
    results = upsert_records(
        sf=sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        records=accounts,
    )

    success_count = sum(1 for r in results if r["success"])
    failure_count = len(results) - success_count

    print(f"Account upsert complete. Success: {success_count}, Failed: {failure_count}")

    if failure_count:
        print("\nFailures:")
        for result in results:
            if not result["success"]:
                print(f"- {result['synthetic_id']}: {result['error']}")

    synthetic_ids = [account["synthetic_id"] for account in accounts]
    account_id_map = fetch_id_map(
        sf=sf,
        object_name="Account",
        external_id_field=SYNTHETIC_ID_FIELD,
        synthetic_ids=synthetic_ids,
    )

    print(f"Fetched {len(account_id_map)} Account ID mappings.")


if __name__ == "__main__":
    main()