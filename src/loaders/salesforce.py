import os
from typing import Any
from dotenv import load_dotenv
from simple_salesforce import Salesforce


load_dotenv()


def get_salesforce_client() -> Salesforce:
    username = os.getenv("SF_USERNAME")
    password = os.getenv("SF_PASSWORD")
    domain = os.getenv("SF_DOMAIN", "test")
    organization_id = os.getenv("SF_ORGANIZATION_ID")
    security_token = os.getenv("SF_SECURITY_TOKEN")

    if not username:
        raise ValueError("Missing SF_USERNAME in .env")
    if not password:
        raise ValueError("Missing SF_PASSWORD in .env")

    login_kwargs = {
        "username": username,
        "password": password,
        "domain": domain,
    }

    if security_token:
        login_kwargs["security_token"] = security_token
    elif organization_id:
        login_kwargs["organizationId"] = organization_id
    else:
        raise ValueError(
            "Provide either SF_SECURITY_TOKEN or SF_ORGANIZATION_ID in .env"
        )

    return Salesforce(**login_kwargs)


def upsert_records(
    sf: Salesforce,
    object_name: str,
    external_id_field: str,
    records: list[dict],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    sobject = getattr(sf, object_name)

    for record in records:
        synthetic_id = record["fields"][external_id_field]
        payload = dict(record["fields"])
        payload.pop(external_id_field, None)

        try:
            response = sobject.upsert(
                f"{external_id_field}/{synthetic_id}",
                payload,
            )
            results.append({
                "synthetic_id": synthetic_id,
                "success": True,
                "response": response,
            })
        except Exception as exc:
            results.append({
                "synthetic_id": synthetic_id,
                "success": False,
                "error": str(exc),
            })

    return results


def fetch_id_map(
    sf: Salesforce,
    object_name: str,
    external_id_field: str,
    synthetic_ids: list[str],
) -> dict[str, str]:
    if not synthetic_ids:
        return {}

    quoted_ids = ",".join(f"'{sid}'" for sid in synthetic_ids)
    query = (
        f"SELECT Id, {external_id_field} "
        f"FROM {object_name} "
        f"WHERE {external_id_field} IN ({quoted_ids})"
    )

    result = sf.query_all(query)

    return {
        row[external_id_field]: row["Id"]
        for row in result["records"]
    }