import pandas as pd
import sys
from rules import RULES, validate

SOURCE = "data/orders_source.csv"
ANSWER_KEY = "data/seeded_defects.csv"

if "--from-s3" in sys.argv:
    from s3_utils import download_latest_raw
    download_latest_raw(SOURCE)

df = pd.read_csv(SOURCE, dtype=str)
valid, failed, summary = validate(df)

failed.to_csv("data/failed_records.csv", index=False)
valid.to_csv("data/orders_valid.csv", index=False)
summary.to_csv("data/validation_summary.csv", index=False)

total = len(df)
n_valid = len(valid)
n_failed = failed["row_number"].nunique()
assert total == n_valid + n_failed, "Reconciliation failed: counts do not add up"

print("=== VALIDATION SUMMARY ===")
print(f"Total records : {total}")
print(f"Valid records : {n_valid}")
print(f"Failed records: {n_failed}")
print(f"Data quality  : {n_valid / total * 100:.1f}%")
print(f"Reconciliation: {total} = {n_valid} + {n_failed}  OK")
print()

key = pd.read_csv(ANSWER_KEY)
expected = key["defect_type"].value_counts()
found = failed["rule_name"].value_counts()

print("=== RULE RESULTS vs ANSWER KEY ===")
all_pass = True
for _, name, _, _ in RULES:
    e, f = int(expected.get(name, 0)), int(found.get(name, 0))
    status = "PASS" if e == f else "FAIL"
    all_pass = all_pass and (e == f)
    print(f"{name:20s} expected={e:3d} found={f:3d}  {status}")

key_pairs = {(r, d) for r, d in zip(key["row_number"], key["defect_type"]) if d != "DUPLICATE_ORDER_ID"}
found_pairs = {(r, d) for r, d in zip(failed["row_number"], failed["rule_name"]) if d != "DUPLICATE_ORDER_ID"}
print()
print(f"Missed defects (in key, not found): {len(key_pairs - found_pairs)}")
print(f"False alarms (found, not in key)  : {len(found_pairs - key_pairs)}")
print("OVERALL:", "ALL RULES MATCH THE ANSWER KEY" if all_pass else "CHECK THE FAILURES ABOVE")