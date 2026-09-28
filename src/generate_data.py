import random
from datetime import datetime, timedelta

import pandas as pd

random.seed(42)  # same data every run
N = 2000
STATUSES = ["Pending", "Shipped", "Delivered", "Cancelled"]
START = datetime(2026, 1, 1)

# ---------- 1. Build clean data ----------
rows = []
for i in range(1, N + 1):
    rows.append({
        "order_id": f"ORD{i:05d}",
        "customer_id": f"CUST{random.randint(1, 300):04d}",
        "order_date": (START + timedelta(days=random.randint(0, 240))).strftime("%Y-%m-%d"),
        "amount": round(random.uniform(100, 5000), 2),
        "status": random.choice(STATUSES),
    })

df = pd.DataFrame(rows)
df["amount"] = df["amount"].astype(object)  # lets us insert bad text values later
df.to_csv("data/orders_clean.csv", index=False)

# ---------- 2. Pick rows to damage (no overlap) ----------
all_bad = random.sample(range(N), 160)
bad_set = set(all_bad)
untouched = [i for i in range(N) if i not in bad_set]


def take(n):
    return [all_bad.pop() for _ in range(n)]


log = []  # ground-truth list of seeded defects


def record(idx, defect):
    log.append({"row_number": idx + 2, "defect_type": defect})  # +2 = CSV line (header + 1-based)


# ---------- 3. Seed the defects ----------
for idx in take(10):
    df.loc[idx, "order_date"] = None
    record(idx, "NULL_ORDER_DATE")

for idx in take(10):
    df.loc[idx, "customer_id"] = None
    record(idx, "NULL_CUSTOMER_ID")

for idx in take(10):
    df.loc[idx, "amount"] = None
    record(idx, "NULL_AMOUNT")

for idx in take(25):
    df.loc[idx, "order_date"] = random.choice(["2026-13-45", "not_a_date", "31/02/2026"])
    record(idx, "INVALID_DATE")

for idx in take(15):
    future = datetime(2026, 12, 1) + timedelta(days=random.randint(0, 90))
    df.loc[idx, "order_date"] = future.strftime("%Y-%m-%d")
    record(idx, "FUTURE_DATE")

for idx in take(25):
    df.loc[idx, "amount"] = -round(random.uniform(10, 500), 2)
    record(idx, "NEGATIVE_AMOUNT")

for idx in take(10):
    df.loc[idx, "amount"] = "abc"
    record(idx, "AMOUNT_NOT_NUMERIC")

for idx in take(20):
    df.loc[idx, "order_id"] = random.choice(["ORD-XYZ", "12345", "ORDER7"])
    record(idx, "INVALID_ORDER_ID")

for idx in take(15):
    df.loc[idx, "status"] = random.choice(["Unknown", "Returnd", "???"])
    record(idx, "INVALID_STATUS")

for idx in take(20):
    src = random.choice(untouched)
    df.loc[idx, "order_id"] = df.loc[src, "order_id"]  # copy another row's ID
    record(idx, "DUPLICATE_ORDER_ID")

# ---------- 4. Save ----------
df.to_csv("data/orders_source.csv", index=False)
pd.DataFrame(log).to_csv("data/seeded_defects.csv", index=False)

print(f"Rows: {len(df)}")
print(f"Seeded defects: {len(log)}")
print(pd.DataFrame(log)["defect_type"].value_counts())