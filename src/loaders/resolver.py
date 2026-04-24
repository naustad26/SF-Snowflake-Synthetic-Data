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


def resolve_account_boost_account_lookup(
    accounts: list[dict],
    boost_account_id_by_parent_account: dict[str, str],
) -> list[dict]:
    resolved_accounts: list[dict] = []

    for account in accounts:
        parent_synthetic_id = (
            account.get("parent_refs", {}).get("Account")
            or account["synthetic_id"]
        )

        if parent_synthetic_id not in boost_account_id_by_parent_account:
            raise ValueError(
                f"Missing Boost Account Id for parent account {parent_synthetic_id}"
            )

        resolved_fields = dict(account["fields"])
        resolved_fields["Boost_Account_Billed_Under__c"] = (
            boost_account_id_by_parent_account[parent_synthetic_id]
        )

        resolved_accounts.append({
            **account,
            "fields": resolved_fields,
        })

    return resolved_accounts

def build_boost_account_lookup_updates(
    boost_accounts: list[dict],
    parent_account_id_map: dict[str, str],
    contact_id_map: dict[str, str],
    contacts: list[dict],
    account_root_parent_map: dict[str, str],
    external_id_field: str,
) -> list[dict]:
    updates: list[dict] = []

    # Build parent account synthetic id -> first contact synthetic id
    main_contact_by_parent: dict[str, str] = {}

    for contact in contacts:
        contact_account_synthetic_id = contact["parent_refs"]["Account"]
        root_parent_synthetic_id = account_root_parent_map[contact_account_synthetic_id]

        if root_parent_synthetic_id not in main_contact_by_parent:
            main_contact_by_parent[root_parent_synthetic_id] = contact["synthetic_id"]

    for boost_account in boost_accounts:
        boost_synthetic_id = boost_account["synthetic_id"]
        parent_account_synthetic_id = boost_account["meta"]["source_parent_account"]

        fields = {
            external_id_field: boost_synthetic_id,
            "Community_Account__c": parent_account_id_map[parent_account_synthetic_id],
        }

        contact_synthetic_id = main_contact_by_parent.get(parent_account_synthetic_id)

        if contact_synthetic_id and contact_synthetic_id in contact_id_map:
            fields["Main_Contact__c"] = contact_id_map[contact_synthetic_id]

        updates.append({
            "object": "ARN_Account__c",
            "synthetic_id": boost_synthetic_id,
            "fields": fields,
        })

    return updates	