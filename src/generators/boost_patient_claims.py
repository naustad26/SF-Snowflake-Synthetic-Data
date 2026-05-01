import random
from datetime import timedelta
from faker import Faker

fake = Faker()

CLAIM_TYPES = [
    "AA",
    "WC",
    "PIP",
    "Commercial",
    "CI",
    "UN",
    "OA",
]

def generate_claim_name(claim_type: str) -> str:
    patterns = [
        lambda: f"{random.randint(10**10, 10**12 - 1)}{claim_type}{random.randint(1, 99):02d}",
        lambda: f"{claim_type}{random.randint(201700000, 202699999)}",
        lambda: f"T{fake.bothify(text='??########').upper()}",
        lambda: f"{fake.bothify(text='??########').upper()}",
        lambda: f"{random.choice(['TA', 'TC', 'TF', 'WC', 'SZ', 'SPN', 'SR'])}{random.randint(1000, 9999999999)}",
    ]

    return random.choice(patterns)()

def generate_boost_patient_claim_records(boost_accounts):
    records = []

    for boost_account in boost_accounts:
        boost_account_sid = boost_account["fields"]["Synthetic_Id__c"]

        for i in range(random.randint(1, 4)):
            dob = fake.date_of_birth(minimum_age=18, maximum_age=85)
            doi = fake.date_between(start_date="-730d", end_date="-60d")
            first_dos = doi + timedelta(days=random.randint(1, 60))

            first_name = fake.first_name()
            last_name = fake.last_name()

            bill_count = random.randint(1, 8)
            open_bill_count = random.randint(0, bill_count)

            deductible_total = round(random.uniform(0, 5000), 2)
            deductible_applied = round(random.uniform(0, deductible_total), 2)

            synthetic_id = f"BPC-{boost_account_sid}-{i + 1:04d}"

            claim_type = random.choice(CLAIM_TYPES)
            claim_name = generate_claim_name(claim_type)

            records.append({
                "Synthetic_Id__c": synthetic_id,
                "Name": claim_name,
                "Claim_Type__c": claim_type,

                "First_Name__c": first_name,
                "Last_Name__c": last_name,
                "DOB__c": dob.isoformat(),
                "DOI__c": doi.isoformat(),
                "First_DOS__c": first_dos.isoformat(),

                "Claim_Type__c": random.choice(CLAIM_TYPES),

                "Total_Billed_Charges__c": round(random.uniform(500, 50000), 2),
                "Bills__c": bill_count,
                "Bills_Open__c": open_bill_count,
                "Open_Tickets__c": random.randint(0, 2),

                "Deductible_Total__c": deductible_total,
                "Deductible_Applied__c": deductible_applied,

                "Denial_Notes__c": fake.sentence(nb_words=10),
                "Check_Claim_Before_Posting__c": random.choice([True, False]),
                "Check_Claim_Detailed_Notes__c": fake.paragraph(nb_sentences=3),

                "_boost_account_synthetic_id": boost_account_sid,
            })

    return records