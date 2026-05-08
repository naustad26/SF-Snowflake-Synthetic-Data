import random
from datetime import timedelta
from .base import fake


def _get_synthetic_id(record: dict) -> str:
    if "synthetic_id" in record:
        return record["synthetic_id"]

    if "fields" in record:
        return record["fields"]["Synthetic_Id__c"]

    return record["Synthetic_Id__c"]


def _get_meta(record: dict, key: str, default=None):
    return record.get("meta", {}).get(key, default)


def generate_arn_check_number(index: int) -> str:
    base_number = 1000000 + index

    trailing_letter = random.choices(
        population=["", "E"],
        weights=[80, 20],
        k=1,
    )[0]

    return f"D-0{base_number}{trailing_letter}"


def generate_arn_checks_to_members_records(
    boost_accounts: list[dict],
    deposits: list[dict],
    count: int,
):
    records = []

    if not boost_accounts:
        raise ValueError("Cannot generate ARN Checks to Members without Boost Accounts.")

    if not deposits:
        raise ValueError("Cannot generate ARN Checks to Members without Deposits.")

    for i in range(count):
        boost_account = random.choice(boost_accounts)
        deposit = random.choice(deposits)

        boost_account_synthetic_id = _get_synthetic_id(boost_account)

        # Existing Boost Account generator stores the source parent Account here.
        account_synthetic_id = _get_meta(
            boost_account,
            "source_parent_account",
        )

        deposit_synthetic_id = _get_synthetic_id(deposit)

        synthetic_id = f"ACTM-{i + 1:06d}"

        check_date = fake.date_between(start_date="-120d", end_date="today")

        total_check_amount = round(random.uniform(50, 8000), 2)
        deductible = round(random.uniform(0, total_check_amount * 0.20), 2)
        aso = round(random.uniform(0, total_check_amount * 0.10), 2)

        pay_to_member = round(
            max(total_check_amount - deductible - aso, 0),
            2,
        )

        fields = {
            "Synthetic_Id__c": synthetic_id,

            # ARN Check #
            "Name": generate_arn_check_number(i),

            "ARN_Check_Date__c": check_date.isoformat(),
            "ARN_Total_Check_Amount__c": total_check_amount,
            "ARN_Check_Towards_This_Claim__c": pay_to_member,

            "Deductible__c": deductible,
            "ASO__c": aso,

            "Archive__c": random.choices(
                population=[True, False],
                weights=[5, 95],
                k=1,
            )[0],
            "Archive_payment__c": random.choices(
                population=[True, False],
                weights=[5, 95],
                k=1,
            )[0],
            "Member_Archive_Payment__c": random.choices(
                population=[True, False],
                weights=[5, 95],
                k=1,
            )[0],

            "CheckIsDeliveredToClient__c": random.choices(
                population=[True, False],
                weights=[75, 25],
                k=1,
            )[0],
            "Create_Income__c": random.choices(
                population=[True, False],
                weights=[70, 30],
                k=1,
            )[0],
            "EORs_Completed__c": random.choices(
                population=[True, False],
                weights=[65, 35],
                k=1,
            )[0],
            "Match_to_Payments__c": random.choices(
                population=[True, False],
                weights=[70, 30],
                k=1,
            )[0],

            "Notes_Last_Update__c": random.choice([
                None,
                "Synthetic ARN check generated for sandbox testing.",
                "Check reviewed and matched to related payment records.",
                "Payment details pending review.",
                "EOR completed and check marked for member payment.",
            ]),

            "EDIFileName__c": random.choice([
                None,
                f"ARN_CHECK_{i + 1:06d}.txt",
                f"EOR_PAYMENT_{i + 1:06d}.edi",
            ]),

            "EDIFIleText__c": random.choice([
                None,
                "Synthetic EDI/check payment text for sandbox testing.",
            ]),
        }

        records.append({
            "object": "ARN_Checks_to_Members__c",
            "synthetic_id": synthetic_id,
            "fields": fields,
            "meta": {
                "account_synthetic_id": account_synthetic_id,
                "boost_account_synthetic_id": boost_account_synthetic_id,
                "deposit_synthetic_id": deposit_synthetic_id,
            },
        })

    return records