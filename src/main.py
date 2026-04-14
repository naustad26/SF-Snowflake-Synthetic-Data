from generators import generate_accounts
from exporters import write_csv


def main() -> None:
    accounts = generate_accounts(25)
    write_csv("accounts.csv", accounts)
    print(f"Generated {len(accounts)} accounts.")


if __name__ == "__main__":
    main()