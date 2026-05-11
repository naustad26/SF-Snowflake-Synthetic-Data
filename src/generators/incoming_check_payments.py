import random
from datetime import date, timedelta
from faker import Faker

fake = Faker()


def _get_field(record, field_name: str, default=None):
    """
    Supports both flat records and wrapped records.
    Flat:
        {"Synthetic_Id__c": "..."}
    Wrapped:
        {"fields": {"Synthetic_Id__c": "..."}}
    """
    if "fields" in record:
        return record["fields"].get(field_name, default)

    return record.get(field_name, default)


def _get_synthetic_id(record) -> str:
    """
    Supports your mixed record shapes.
    """
    if "synthetic_id" in record:
        return record["synthetic_id"]

    if "fields" in record:
        return record["fields"]["Synthetic_Id__c"]

    return record["Synthetic_Id__c"]


def _get_meta(record, key: str, default=None):
    return record.get("meta", {}).get(key, default)

def _is_denied_boost(boost_record) -> bool:
    return _get_field(boost_record, "ARN_Status__c") == "Denied"


def _safe_float(value, default=0.0) -> float:
    if value in (None, ""):
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _check_number(index: int) -> str:
    """
    Check # is Name on Incoming_Check_Payment__c.
    Keep this realistic but stable.
    """
    patterns = [
        lambda: str(100000 + index),
        lambda: f"EFT{index + 1:06d}",
        lambda: f"ACH{index + 1:06d}",
    ]

    return random.choice(patterns)()


def _payment_date_from_boost(boost_record) -> date:
    """
    Prefer a payment date after Sent_Date__c when available.
    Otherwise use a recent date.
    """
    sent_date_raw = _get_field(boost_record, "Sent_Date__c")

    if sent_date_raw:
        try:
            sent_date = date.fromisoformat(sent_date_raw)
            return sent_date + timedelta(days=random.randint(14, 120))
        except ValueError:
            pass

    return fake.date_between(start_date="-180d", end_date="today")


def generate_incoming_check_payment_records(
    boost_records,
    min_payments_per_boost: int,
    max_payments_per_boost: int,
    payment_probability: float,
):
    records = []

    if not boost_records:
        raise ValueError("Cannot generate Incoming Check Payments without Boost records.")

    payment_index = 0

    for boost in boost_records:
        is_denied = _is_denied_boost(boost)

        effective_payment_probability = (
            max(payment_probability, 0.85)
            if is_denied
            else payment_probability
        )

        if random.random() > effective_payment_probability:
            continue

        if is_denied:
            payment_count = random.randint(
                max(1, min_payments_per_boost),
                max(1, max_payments_per_boost),
            )
        else:
            payment_count = random.randint(
                min_payments_per_boost,
                max_payments_per_boost,
            )

        if payment_count == 0:
            continue

        boost_synthetic_id = _get_synthetic_id(boost)

        boost_patient_claim_synthetic_id = (
            _get_meta(boost, "boost_patient_claim_synthetic_id")
            or _get_field(boost, "_boost_patient_claim_synthetic_id")
        )

        billed_charges = _safe_float(
            _get_field(boost, "Billed_Charges__c"),
            default=1000.0,
        )

        outstanding = _safe_float(
            _get_field(boost, "Outstanding__c"),
            default=billed_charges,
        )

        for payment_number in range(payment_count):
            payment_index += 1

            external_id = f"ICP-{boost_synthetic_id}-{payment_number + 1:03d}"
            check_number = _check_number(payment_index)

            # Keep total check amount within Currency(8,2).
            # Max Currency(8,2) is effectively 999,999.99.
            max_payment_base = max(min(billed_charges, 999999.99), 100.0)

            payer_total = round(
                random.uniform(50.0, max_payment_base),
                2,
            )

            amount_towards_claim = round(
                min(payer_total, max(outstanding, 0.0)),
                2,
            )

            reductions = round(
                random.uniform(0, amount_towards_claim * 0.25),
                2,
            )

            arn_fee = round(
                amount_towards_claim * random.uniform(0.05, 0.18),
                2,
            )

            deductible_from_payor = round(
                random.uniform(0, amount_towards_claim * 0.15),
                2,
            )

            deductible_applied = round(
                min(deductible_from_payor, amount_towards_claim),
                2,
            )

            amount_allowed_member = round(
                max(amount_towards_claim - reductions - arn_fee - deductible_applied, 0),
                2,
            )

            outstanding_after_payment = round(
                max(outstanding - amount_towards_claim, 0),
                2,
            )

            check_date = _payment_date_from_boost(boost)

            fields = {
                # External ID, Unique.
                "Use_for_Transfer__c": external_id,

                # Check #.
                "Name": check_number,

                "Check_Date__c": check_date.isoformat(),

                "Payer_Total__c": payer_total,
                "Total_Check_Amount__c": payer_total,

                "Amount_Towards_This_Claim__c": amount_towards_claim,
                "Amount_Applied_to_Lines__c": amount_towards_claim,
                "Amount_Allowed_Member__c": amount_allowed_member,

                "ARN_Fee__c": arn_fee,

                "Deductible_Amt_From_Payor__c": deductible_from_payor,
                "Deductible_Applied_This_Claim__c": deductible_applied,

                "Outstanding_Amount__c": outstanding_after_payment,
                "Reductions__c": reductions,

                "# Lines Needing Approval__c": None,

                "Approved_del__c": random.choices(
                    population=[True, False],
                    weights=[80, 20],
                    k=1,
                )[0],

                "Create_Income__c": random.choices(
                    population=[True, False],
                    weights=[70, 30],
                    k=1,
                )[0],

                "Reconcile__c": random.choices(
                    population=[True, False],
                    weights=[65, 35],
                    k=1,
                )[0],

                "Denial_Additional_Notes__c": random.choice([
                    None,
                    "Partial payment received from payer.",
                    "Payment applied after payer review.",
                    "Payment requires reconciliation.",
                    "Deductible applied by payer.",
                    fake.sentence(nb_words=8),
                ]),

                "BS_Update_Field__c": random.choice([
                    None,
                    "Synthetic payment generated",
                    "Payment matched to bill",
                    "Payment pending reconciliation",
                ]),

                "Code_Descriptions__c": random.choice([
                    None,
                    "Synthetic EOR/payment detail generated for sandbox testing.",
                    "Payment generated with reductions, ARN fee, and allowed amount.",
                ]),
            }

            # Do not send None field with the invalid '# Lines...' key.
            # Kept out below intentionally.

            fields.pop("# Lines Needing Approval__c", None)

            records.append({
                "object": "Incoming_Check_Payment__c",
                "synthetic_id": external_id,
                "fields": fields,
                "meta": {
                    "boost_synthetic_id": boost_synthetic_id,
                    "boost_patient_claim_synthetic_id": boost_patient_claim_synthetic_id,
                },
            })

    return records