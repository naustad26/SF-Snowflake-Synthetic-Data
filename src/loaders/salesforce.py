import os
from typing import Any

from dotenv import load_dotenv
from simple_salesforce import Salesforce

from src.config import (
    SALESFORCE_BULK_UPSERT_ENABLED,
    SALESFORCE_BULK_BATCH_SIZE,
    SALESFORCE_BULK_USE_SERIAL,
    SALESFORCE_BULK_UPSERT_EXCLUDED_OBJECTS,
)


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


def _build_bulk_payload(records: list[dict]) -> list[dict[str, Any]]:
    """
    Bulk API upsert requires the external ID field to be present in each row.
    So unlike REST upsert, do not remove the external ID from the payload.
    """
    return [
        dict(record["fields"])
        for record in records
    ]


def _normalize_bulk_results(
    records: list[dict],
    raw_results: list[dict],
    external_id_field: str,
) -> list[dict[str, Any]]:
    normalized_results: list[dict[str, Any]] = []

    for record, raw_result in zip(records, raw_results):
        synthetic_id = record["fields"][external_id_field]
        success = bool(raw_result.get("success"))

        errors = raw_result.get("errors") or []

        normalized_results.append({
            "synthetic_id": synthetic_id,
            "success": success,
            "response": raw_result if success else None,
            "error": "; ".join(str(error) for error in errors) if errors else "",
            "raw": raw_result,
        })

    return normalized_results


def bulk_upsert_records(
    sf: Salesforce,
    object_name: str,
    external_id_field: str,
    records: list[dict],
) -> list[dict[str, Any]]:
    if not records:
        return []

    bulk_object = getattr(sf.bulk, object_name)

    payload = _build_bulk_payload(records)

    raw_results = bulk_object.upsert(
        payload,
        external_id_field,
        batch_size=SALESFORCE_BULK_BATCH_SIZE,
        use_serial=SALESFORCE_BULK_USE_SERIAL,
    )

    return _normalize_bulk_results(
        records=records,
        raw_results=raw_results,
        external_id_field=external_id_field,
    )


def rest_upsert_records(
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

        # REST upsert identifies the record through the URL, so the external ID
        # does not need to be included in the body.
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
                "error": "",
            })
        except Exception as exc:
            results.append({
                "synthetic_id": synthetic_id,
                "success": False,
                "response": None,
                "error": str(exc),
            })

    return results

def upsert_records(
    sf: Salesforce,
    object_name: str,
    external_id_field: str,
    records: list[dict],
) -> list[dict[str, Any]]:
    if not records:
        return []

    should_use_bulk = (
        SALESFORCE_BULK_UPSERT_ENABLED
        and object_name not in SALESFORCE_BULK_UPSERT_EXCLUDED_OBJECTS
    )

    if should_use_bulk:
        return bulk_upsert_records(
            sf=sf,
            object_name=object_name,
            external_id_field=external_id_field,
            records=records,
        )

    return rest_upsert_records(
        sf=sf,
        object_name=object_name,
        external_id_field=external_id_field,
        records=records,
    )

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