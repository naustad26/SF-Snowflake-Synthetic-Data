from config import (
    RANDOM_SEED,
    ACCOUNT_COUNT,
    MIN_CONTACTS_PER_ACCOUNT,
    MAX_CONTACTS_PER_ACCOUNT,
)
from generators import set_seed, generate_accounts, generate_contacts_for_accounts
from exporters import export_data_tree


def main() -> None:
    set_seed(RANDOM_SEED)

    accounts = generate_accounts(ACCOUNT_COUNT)
    contacts = generate_contacts_for_accounts(
        accounts,
        min_per_account=MIN_CONTACTS_PER_ACCOUNT,
        max_per_account=MAX_CONTACTS_PER_ACCOUNT,
    )

    export_data_tree(accounts, contacts, output_dir="data")


if __name__ == "__main__":
    main()