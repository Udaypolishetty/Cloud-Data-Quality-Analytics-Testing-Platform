import sqlite3
from datetime import datetime

import pandas as pd

DB = "data/quality.db"

# Raw source: keep everything as text so bad values are preserved exactly as received
raw = pd.read_csv("data/orders_source.csv", dtype=str)
raw.insert(0, "row_num", raw.index + 2)  # CSV line number, same as the validator uses

clean = pd.read_csv("data/orders_valid.csv")
failed = pd.read_csv("data/failed_records.csv").rename(columns={"row_number": "row_num"})
summary = pd.read_csv("data/validation_summary.csv")

conn = sqlite3.connect(DB)

raw.to_sql("orders_raw", conn, if_exists="replace", index=False)
clean.to_sql("orders_clean", conn, if_exists="replace", index=False)
failed.to_sql("failed_records", conn, if_exists="replace", index=False)
summary.to_sql("validation_summary", conn, if_exists="replace", index=False)

# One row per load, so results can be compared across runs later
total = len(raw)
n_valid = len(clean)
run = pd.DataFrame([{
    "run_timestamp": datetime.now().isoformat(timespec="seconds"),
    "total_records": total,
    "valid_records": n_valid,
    "failed_records": failed["row_num"].nunique(),
    "data_quality_pct": round(n_valid / total * 100, 1),
}])
run.to_sql("validation_runs", conn, if_exists="append", index=False)

conn.commit()

for table in ["orders_raw", "orders_clean", "failed_records", "validation_summary", "validation_runs"]:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table:20s} {count} rows")

conn.close()