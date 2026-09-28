import sqlite3
import sys

DB = "data/quality.db"
SQL_FILE = "sql/reconciliation.sql"

with open(SQL_FILE, encoding="utf-8") as f:
    text = f.read()

# Split on ';' and keep only chunks that contain real SQL (not just comments)
statements = [
    s for s in text.split(";")
    if any(line.strip() and not line.strip().startswith("--") for line in s.splitlines())
]

conn = sqlite3.connect(DB)
all_pass = True

print("=== SQL RECONCILIATION AND QUALITY CHECKS ===")
for stmt in statements:
    name, expected, actual, result = conn.execute(stmt).fetchone()
    all_pass = all_pass and result == "PASS"
    print(f"{name:36s} expected={str(expected):>12}  actual={str(actual):>12}  {result}")

conn.close()
print()
print("OVERALL:", "ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED")
sys.exit(0 if all_pass else 1)