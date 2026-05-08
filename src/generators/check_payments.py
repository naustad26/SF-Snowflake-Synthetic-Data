import random


def _get_synthetic_id(record: dict) -> str:
    if "synthetic_id" in record:
        return record["synthetic_id"]

    if "fields" in record:
        return record["fields"]["Synthetic_Id__c"]

    return record["Synthetic_Id__c"]


def _get_meta(record: dict, key: str, default=None):
    return record.get("meta", {}).get(key, default)


def generate_check_payment_name(index: int) -> str:
    """
    Check Payment Name is Text(80).
    Keep it stable and readable.
    """
    return f"CP-{index + 1:06d}"


def generate_check_payment_records(
    incoming_check_payments: list[dict],
    probability_per_incoming_payment: float,
    min_check_payments_per_incoming_payment: int,
    max_check_payments_per_incoming_payment: int,
):
    records = []

    if not incoming_check_payments:
        raise ValueError(
            "Cannot generate Check Payments without Incoming Check Payments."
        )

    global_index = 0

    for incoming_payment in incoming_check_payments:
        if random.random() > probability_per_incoming_payment:
            continue

        incoming_payment_synthetic_id = _get_synthetic_id(incoming_payment)

        boost_synthetic_id = _get_meta(
            incoming_payment,
            "boost_synthetic_id",
        )

        check_count = random.randint(
            min_check_payments_per_incoming_payment,
            max_check_payments_per_incoming_payment,
        )

        for i in range(check_count):
            synthetic_id = f"CP-{incoming_payment_synthetic_id}-{i + 1:03d}"

            fields = {
                "Synthetic_Id__c": synthetic_id,
                "Name": generate_check_payment_name(global_index),
            }

            records.append({
                "object": "Check_Payment__c",
                "synthetic_id": synthetic_id,
                "fields": fields,
                "meta": {
                    "incoming_check_payment_synthetic_id": incoming_payment_synthetic_id,
                    "boost_synthetic_id": boost_synthetic_id,
                },
            })

            global_index += 1

    return records