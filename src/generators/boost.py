import random
from datetime import timedelta
from .base import fake

ARN_STATUSES = [
    "Appealing Denial",
    "Being Reconsidered",
    "Bill Resubmitted",
    "Denial not yet received",
    "Denied",
    "Duplicate",
    "Information Requested",
    "In Litigation",
    "No Longer Using Boost for This Claim",
    "Overpayment",
    "Paid Member",
    "Partial Payment",
    "Processing",
    "Processing at Payer",
    "Received Check Only",
    "Received EOB Only",
    "Refund Completed",
    "Refund Request to Member",
    "Review with member",
    "See Note",
    "Under Investigation",
    "UR Appeal Processing at DIFS Confirmed",
    "UR Denial Appeal",
    "UR Overturned by DIFS Being Reconsidered",
    "Utilization Review",
    "Waiting for info from member",
    "Waiting for payor response",
    "Needs Approval",
    "Rejected",
    "Rejected at Clearinghouse",
    "Resubmitted Rejection",
]

def generate_bill_id(claim_type: str, index: int) -> str:
    patterns = [
        lambda: f"{random.randint(10**10, 10**12 - 1)}{claim_type}{index:02d}",
        lambda: f"{claim_type}{random.randint(201700000, 202699999)}",
        lambda: fake.bothify(text='??########').upper(),
        lambda: f"T{random.randint(1000, 9999999999)}",
    ]
    return random.choice(patterns)()


def generate_boost_records(boost_patient_claims):
    records = []

    for claim in boost_patient_claims:
        claim_sid = claim["Synthetic_Id__c"]
        boost_account_sid = claim["_boost_account_synthetic_id"]

        bill_count = claim.get("Bills__c", random.randint(1, 4))

        for i in range(bill_count):
            claim_type = claim["Claim_Type__c"]

            dos_start = claim["First_DOS__c"]
            dos_end = dos_start  # simple for now

            billed = round(random.uniform(100, 15000), 2)
            outstanding = round(random.uniform(0, billed), 2)

            boost_synthetic_id = f"BOOST-{claim_sid}-{i + 1:04d}"
            bill_id = boost_synthetic_id

            records.append({

                "Synthetic_Id__c": boost_synthetic_id,
                "Name": generate_bill_id(claim_type, i + 1),

                "Patient_First_Name__c": claim["First_Name__c"],
                "Patient_Last_Name__c": claim["Last_Name__c"],
                "Claim_Type__c": claim_type,

                "DOS_Start__c": dos_start,
                "DOS_End__c": dos_end,
                "DOB__c": claim["DOB__c"],

                "Account_Number__c": fake.bothify(text="ACCT-########"),

                "Bill_ID__c": bill_id,
                "Bill_ID_Jopari__c": f"JOP-{bill_id}",

                "ARN_Status__c": random.choice(ARN_STATUSES),
                "Status_to_Payer__c": fake.sentence(nb_words=6),

                "Sent_Date__c": fake.date_between(start_date="-365d", end_date="-30d").isoformat(),
                # "Uploaded__c": fake.date_between(start_date="-365d", end_date="-30d").isoformat(),
                "Last_Update__c": fake.date_between(start_date="-30d", end_date="today").isoformat(),

                "Billed_Charges__c": billed,
                "Outstanding__c": outstanding,
                "Location__c": fake.city(),

                "_boost_account_synthetic_id": boost_account_sid,
                "_boost_patient_claim_synthetic_id": claim_sid,
            })

    return records