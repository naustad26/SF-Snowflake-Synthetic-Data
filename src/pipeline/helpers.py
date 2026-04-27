def print_results(label: str, results: list[dict]) -> None:
    success_count = sum(1 for r in results if r["success"])
    failure_count = len(results) - success_count

    print(f"{label} upsert complete. Success: {success_count}, Failed: {failure_count}")

    if failure_count:
        print(f"\n{label} failures:")
        for result in results:
            if not result["success"]:
                print(f"- {result['synthetic_id']}: {result['error']}")


def build_boost_account_id_by_parent_account(
    boost_accounts: list[dict],
    boost_account_id_map: dict[str, str],
) -> dict[str, str]:
    result: dict[str, str] = {}

    for boost_account in boost_accounts:
        parent_account_synthetic_id = boost_account["meta"]["source_parent_account"]
        boost_account_synthetic_id = boost_account["synthetic_id"]

        result[parent_account_synthetic_id] = boost_account_id_map[
            boost_account_synthetic_id
        ]

    return result


def build_account_root_parent_map(
    parent_accounts: list[dict],
    child_accounts: list[dict],
) -> dict[str, str]:
    result: dict[str, str] = {}

    for parent in parent_accounts:
        result[parent["synthetic_id"]] = parent["synthetic_id"]

    for child in child_accounts:
        result[child["synthetic_id"]] = child["parent_refs"]["Account"]

    return result