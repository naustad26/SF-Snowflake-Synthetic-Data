# Main entry point for synthetic data generation

from config import (
    RANDOM_SEED,
    ACCOUNT_COUNT,
    MIN_CONTACTS_PER_ACCOUNT,
    MAX_CONTACTS_PER_ACCOUNT,
)
from generators import set_seed, generate_accounts, generate_contacts_for_accounts
from exporters import export_csv


def main() -> None:
    set_seed(RANDOM_SEED)

    accounts = generate_accounts(2)
    contacts = generate_contacts_for_accounts(accounts, 1, 2)

    export_csv("accounts.csv", accounts)
    export_csv("contacts.csv", contacts)


if __name__ == "__main__":
    main()