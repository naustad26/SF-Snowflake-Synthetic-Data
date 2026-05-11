import random


FEE_PERCENTAGES = [
    20,
    25,
    30,
    35,
    40,
]


def generate_arn_fee_records(
    boost_accounts: list[dict],
    arn_payors: list[dict],
    fee_probability_per_boost_account: float = 0.85,
    min_fees_per_boost_account: int = 1,
    max_fees_per_boost_account: int = 4,
) -> list[dict]:
    records = []

    if not boost_accounts:
        raise ValueError("Cannot generate ARN Fees without Boost Account records.")

    if not arn_payors:
        raise ValueError("Cannot generate ARN Fees without ARN Payor records.")

    arn_payor_synthetic_ids = [
        arn_payor["synthetic_id"]
        for arn_payor in arn_payors
    ]

    for boost_account in boost_accounts:
        if random.random() > fee_probability_per_boost_account:
            continue

        boost_account_synthetic_id = boost_account["synthetic_id"]

        fee_count = random.randint(
            min_fees_per_boost_account,
            min(max_fees_per_boost_account, len(arn_payor_synthetic_ids)),
        )

        selected_arn_payor_synthetic_ids = random.sample(
            arn_payor_synthetic_ids,
            k=fee_count,
        )

        for arn_payor_synthetic_id in selected_arn_payor_synthetic_ids:
            synthetic_id = (
                f"ARNFEE-{boost_account_synthetic_id}-{arn_payor_synthetic_id}"
            )

            records.append({
                "object": "ARN_Fees__c",
                "synthetic_id": synthetic_id,
                "fields": {
                    "Synthetic_Id__c": synthetic_id,
                    "Fees_percentage__c": random.choice(FEE_PERCENTAGES),
                },
                "meta": {
                    "boost_account_synthetic_id": boost_account_synthetic_id,
                    "arn_payor_synthetic_id": arn_payor_synthetic_id,
                },
            })

    return records