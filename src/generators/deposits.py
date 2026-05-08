import random
from datetime import date, timedelta
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
    Deposit_ID__c max length is 10.
    Name and Deposit_ID__c should match.
    """
    if index % 3 == 0:
        base_date = date.today() - timedelta(days=180)
        deposit_date = base_date + timedelta(days=index)
        return deposit_date.strftime("%m%d%y") + " EFT"

    if index % 3 == 1:
        return str(1000 + index)

    return str(100 + index)


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