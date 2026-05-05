import random
from datetime import timedelta
from faker import Faker

fake = Faker()


DEPOSIT_STATUSES = [
    "Processing Incoming Payments",
    "ReadyforReconciliation",
    "Deposited to Chase",
    "Payments Created for Members",
    "Complete",
]

def generate_deposit_id(index: int) -> str:
    """
    Deposit_ID__c is Text(10), External ID, Unique.
    Real examples:
        032626 EFT
        1022
        847

    Keep Name and Deposit_ID__c matching because org automation appears
    to copy Name into Deposit_ID__c.
    """
    patterns = [
        # MMDDYY EFT, exactly 10 chars
        lambda: fake.date_between(start_date="-180d", end_date="today").strftime("%m%d%y") + " EFT",

        # 3-4 digit deposit/check batch style
        lambda: str(100 + index),
        lambda: str(1000 + index),
    ]

    return random.choice(patterns)()


def generate_deposit_records(count: int):
    records = []

    for i in range(count):
        deposit_id = generate_deposit_id(i)

        deposited_date = fake.date_between(start_date="-180d", end_date="today")

        ready_date = deposited_date + timedelta(days=random.randint(0, 10))
        reconciliation_date = ready_date + timedelta(days=random.randint(0, 20))
        eors_completed_date = reconciliation_date + timedelta(days=random.randint(0, 10))
        qb_date = reconciliation_date + timedelta(days=random.randint(0, 14))

        status = random.choices(
            population=DEPOSIT_STATUSES,
            weights=[35, 25, 20, 10, 10],
            k=1,
        )[0]

        fields = {
            "Deposit_ID__c": deposit_id,
            "Name": deposit_id,

            "Deposited_to_Chase__c": deposited_date.isoformat(),
            "Date_Ready_to_Enter_in_QB__c": ready_date.isoformat(),
            "Reconciliation_Complete__c": reconciliation_date.isoformat(),
            "EORs_Completed__c": eors_completed_date.isoformat(),
            "Date_Entered_in_QB__c": qb_date.isoformat(),
            "Status__c": status,
            "Overpayment_Amount__c": round(
                random.choices(
                    population=[
                        0,
                        random.uniform(25, 2500),
                    ],
                    weights=[85, 15],
                    k=1,
                )[0],
                2,
            ),
        }

        records.append({
            "object": "Deposit__c",
            "synthetic_id": deposit_id,
            "fields": fields,
            "meta": {},
        })

    return records