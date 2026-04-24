def resolve_contact_relationships(
    contacts: list[dict],
    account_id_map: dict[str, str],
) -> list[dict]:
    resolved_contacts: list[dict] = []

    for contact in contacts:
        account_synthetic_id = contact["parent_refs"]["Account"]

        if account_synthetic_id not in account_id_map:
            raise ValueError(
                f"Missing Salesforce AccountId for synthetic account {account_synthetic_id}"
            )

        resolved_fields = dict(contact["fields"])
        resolved_fields["AccountId"] = account_id_map[account_synthetic_id]

        resolved_contacts.append({
            **contact,
            "fields": resolved_fields,
        })

    return resolved_contacts


def resolve_account_parent_relationships(
    child_accounts: list[dict],
    account_id_map: dict[str, str],
) -> list[dict]:
    resolved_accounts: list[dict] = []

    for account in child_accounts:
        parent_synthetic_id = account["parent_refs"]["Account"]

        if parent_synthetic_id not in account_id_map:
            raise ValueError(
                f"Missing Salesforce parent AccountId for synthetic account {parent_synthetic_id}"
            )

        resolved_fields = dict(account["fields"])
        resolved_fields["ParentId"] = account_id_map[parent_synthetic_id]

        resolved_accounts.append({
            **account,
            "fields": resolved_fields,
        })

    return resolved_accounts