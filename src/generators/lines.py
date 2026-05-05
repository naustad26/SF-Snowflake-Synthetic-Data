import random
from .base import fake


CPT_CODES = [
    ("97530", "Therapeutic Activities"),
    ("97112", "Neuromuscular Re-education"),
    ("97535", "Self-Care/Home Management Training"),
    ("97140", "Manual Therapy"),
    ("97110", "Therapeutic Exercise"),
    ("97116", "Gait Training"),
    ("97014", "Electrical Stimulation"),
    ("97010", "Hot/Cold Packs"),
    ("97542", "Wheelchair Management"),
    ("97750", "Physical Performance Test"),
]

MODIFIERS = ["GP", "GO", "GN"]


DIAGNOSIS_POINTERS = [
    "1",
    "2",
    "3",
    "1,2",
    "1,3",
]


def generate_lines_records(boost_records):
    records = []

    for boost in boost_records:
        boost_sid = boost["Synthetic_Id__c"]
        boost_name = boost["Name"]
        dos = boost["DOS_Start__c"]

        line_count = random.randint(2, 6)

        selected_codes = random.sample(
            CPT_CODES,
            k=min(line_count, len(CPT_CODES))
        )

        for i, (cpt_code, cpt_definition) in enumerate(selected_codes, start=1):
            units = random.choices([1, 2, 3, 4], weights=[65, 20, 10, 5], k=1)[0]

            amount_charged = round(random.uniform(60, 180) * units, 2)
            expected_payment = round(amount_charged * random.uniform(0.55, 0.85), 2)
            amount_paid = round(expected_payment * random.uniform(0.75, 1.15), 2)

            arn_fee = round(amount_paid * 0.30, 2)
            pay_to_member = round(max(amount_paid - arn_fee, 0), 2)
            reductions = round(max(amount_charged - amount_paid, 0), 2)

            synthetic_id = f"LINE-{boost_sid}-{i:04d}"

            records.append({
                "Synthetic_Id__c": synthetic_id,
                "Name": str(i),

                "Lines_ID__c": synthetic_id,
                "Lines_ID_Jopari__c": f"JOP-{synthetic_id}",

                "Date_of_Service__c": dos,
                "Mod_Pkg__c": random.choice(MODIFIERS),
                "Diagnosis_Pointer__c": "1",

                # Store these only if you have text fields for them.
                # Otherwise skip until CPT_Code__c lookup records exist.
                # "CPT_Code_Text__c": cpt_code,
                # "CPT_Code_Definition_Text__c": cpt_definition,

                "Units__c": units,
                "Amount_Charged__c": amount_charged,
                "ARN_Fee_NEW__c": arn_fee,
                "Reductions_New__c": reductions,
                "Pay_to_Member__c": pay_to_member,

                "_boost_synthetic_id": boost_sid,
                # "_cpt_code": cpt_code,
                # "_cpt_definition": cpt_definition,
            })

    return records