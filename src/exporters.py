import json
from pathlib import Path


def export_data_tree(accounts: list[dict], contacts: list[dict], output_dir: str = "data") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    account_ref_map: dict[str, str] = {}
    account_records: list[dict] = []

    for idx, account in enumerate(accounts, start=1):
        ref_id = f"AccountRef{idx}"
        account_ref_map[account["SyntheticId"]] = ref_id

        account_records.append({
            "attributes": {
                "type": "Account",
                "referenceId": ref_id,
            },
            "Name": account["Name"],
            "Phone": account["Phone"],
            "Website": account["Website"],
            "BillingStreet": account["BillingStreet"],
            "BillingCity": account["BillingCity"],
            "BillingState": account["BillingState"],
            "BillingPostalCode": account["BillingPostalCode"],
            "ShippingStreet": account["ShippingStreet"],
            "ShippingCity": account["ShippingCity"],
            "ShippingState": account["ShippingState"],
            "ShippingPostalCode": account["ShippingPostalCode"],
            # Add more safe/importable fields later
        })

    contact_records: list[dict] = []

    for idx, contact in enumerate(contacts, start=1):
        parent_ref = account_ref_map[contact["AccountSyntheticId"]]

        contact_records.append({
            "attributes": {
                "type": "Contact",
                "referenceId": f"ContactRef{idx}",
            },
            "FirstName": contact["FirstName"],
            "LastName": contact["LastName"],
            "Title": contact["Title"],
            "MailingStreet": contact["MailingStreet"],
            "MailingCity": contact["MailingCity"],
            "MailingState": contact["MailingState"],
            "MailingPostalCode": contact["MailingPostalCode"],
            "Email": contact["Email"],
            "Phone": contact["Phone"],
            "AccountId": f"@{parent_ref}",
        })

    with open(out / "Account.json", "w", encoding="utf-8") as f:
        json.dump({"records": account_records}, f, indent=2)

    with open(out / "Contact.json", "w", encoding="utf-8") as f:
        json.dump({"records": contact_records}, f, indent=2)

    plan = [
        {"sobject": "Account", "files": ["Account.json"]},
        {"sobject": "Contact", "files": ["Contact.json"]},
    ]

    with open(out / "plan.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)