import random
from faker import Faker

fake = Faker()


def generate_payer_id(index: int) -> str:
    """
    Payer_ID__c is External ID + Unique.
    Use a stable synthetic-style payer ID so reruns update instead of duplicate.
    """
    return f"PAYOR-{index + 1:06d}"


def generate_edi_payer_id() -> str:
    patterns = [
        lambda: fake.bothify(text="#####").upper(),
        lambda: fake.bothify(text="??###").upper(),
        lambda: fake.bothify(text="P####").upper(),
        lambda: fake.bothify(text="EDI#####").upper(),
    ]

    return random.choice(patterns)()


def generate_arn_payor_name(master_name: str, payer_id: str) -> str:
    variants = [
        "Claims",
        "EDI",
        "Medical",
        "Workers Comp",
        "Auto",
        "Commercial",
    ]

    return f"{master_name} {random.choice(variants)} {payer_id[-3:]}"


def generate_arn_payor_records(
    arn_payor_master_records,
    min_payors_per_master: int,
    max_payors_per_master: int,
):
    records = []
    global_index = 0

    if not arn_payor_master_records:
        raise ValueError("Cannot generate ARN Payors without ARN Payor Master records.")

    for master_record in arn_payor_master_records:
        master_synthetic_id = master_record["synthetic_id"]
        master_name = master_record["fields"]["Name"]

        payor_count = random.randint(
            min_payors_per_master,
            max_payors_per_master,
        )

        for _ in range(payor_count):
            payer_id = generate_payer_id(global_index)
            edi_payer_id = generate_edi_payer_id()

            fields = {
                "Payer_ID__c": payer_id,
                "Name": generate_arn_payor_name(master_name, payer_id),
                "EDI_Payer_ID__c": edi_payer_id,

                # These are editable Number fields based on the metadata you shared.
                # Keep them synthetic but plausible.
                "Boost_Bills__c": random.randint(0, 250),
                "Days_Between_Sent_and_Processing_Total__c": random.randint(0, 5000),
            }

            records.append({
                "object": "ARN_Payors__c",
                "synthetic_id": payer_id,
                "fields": fields,
                "meta": {
                    "arn_payor_master_synthetic_id": master_synthetic_id,
                },
            })

            global_index += 1

    return records