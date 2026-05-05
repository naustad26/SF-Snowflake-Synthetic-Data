from src.generators.lines import generate_lines_records


def generate_lines_step(context):
    boost_records = context.get_records("boost")

    records = generate_lines_records(boost_records)

    context.set_records("lines", records)


def resolve_lines_step(context):
    boost_id_map = context.get_id_map("boost")
    records = context.get_records("lines")

    for line in records:
        boost_sid = line.pop("_boost_synthetic_id")
        line["Claim__c"] = boost_id_map[boost_sid]

    context.set_records("lines", records)


def upsert_lines_step(context):
    records = context.get_records("lines")

    if not records:
        print("No Lines to upsert")
        return

    results = context.sf.bulk.Lines__c.upsert(
        records,
        "Synthetic_Id__c"
    )

    successes = [r for r in results if r.get("success")]
    failures = [r for r in results if not r.get("success")]

    print(
        f"Lines upsert complete. "
        f"Success: {len(successes)}, Failed: {len(failures)}"
    )

    if failures:
        print("Line failures:")
        print(failures[:5])