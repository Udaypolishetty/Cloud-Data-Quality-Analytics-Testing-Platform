import pandas as pd

AS_OF_DATE = pd.Timestamp("2026-09-01")  # orders after this date count as "future"
VALID_STATUSES = {"Pending", "Shipped", "Delivered", "Cancelled"}
ORDER_ID_PATTERN = r"^ORD\d{5}$"


# ---------- Helpers ----------
def _id_format_ok(df):
    return df["order_id"].str.match(ORDER_ID_PATTERN, na=False)


def _parsed_date(df):
    return pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="coerce")


def _amount_num(df):
    return pd.to_numeric(df["amount"], errors="coerce")


# ---------- One function per rule: returns True for rows that FAIL ----------
def r01_null_order_date(df):
    return df["order_date"].isna()


def r02_null_customer_id(df):
    return df["customer_id"].isna()


def r03_null_amount(df):
    return df["amount"].isna()


def r04_invalid_order_id(df):
    return df["order_id"].notna() & ~_id_format_ok(df)


def r05_duplicate_order_id(df):
    return _id_format_ok(df) & df["order_id"].duplicated(keep="first")


def r06_invalid_date(df):
    return df["order_date"].notna() & _parsed_date(df).isna()


def r07_future_date(df):
    return _parsed_date(df) > AS_OF_DATE


def r08_negative_amount(df):
    return _amount_num(df) <= 0


def r09_amount_not_numeric(df):
    return df["amount"].notna() & _amount_num(df).isna()


def r10_invalid_status(df):
    return ~df["status"].isin(VALID_STATUSES)


RULES = [
    ("R01", "NULL_ORDER_DATE", "Completeness", r01_null_order_date),
    ("R02", "NULL_CUSTOMER_ID", "Completeness", r02_null_customer_id),
    ("R03", "NULL_AMOUNT", "Completeness", r03_null_amount),
    ("R04", "INVALID_ORDER_ID", "Validity", r04_invalid_order_id),
    ("R05", "DUPLICATE_ORDER_ID", "Uniqueness", r05_duplicate_order_id),
    ("R06", "INVALID_DATE", "Validity", r06_invalid_date),
    ("R07", "FUTURE_DATE", "Validity", r07_future_date),
    ("R08", "NEGATIVE_AMOUNT", "Accuracy", r08_negative_amount),
    ("R09", "AMOUNT_NOT_NUMERIC", "Consistency", r09_amount_not_numeric),
    ("R10", "INVALID_STATUS", "Validity", r10_invalid_status),
]


# ---------- Runs all rules and splits the data ----------
def validate(df):
    df = df.copy()
    df["row_number"] = df.index + 2  # matches the line number in the CSV file

    parts, summary_rows = [], []
    for rule_id, name, dimension, check in RULES:
        hit = df[check(df)].copy()
        hit["rule_id"] = rule_id
        hit["rule_name"] = name
        hit["dimension"] = dimension
        parts.append(hit)
        summary_rows.append({"rule_id": rule_id, "rule_name": name,
                             "dimension": dimension, "failed_count": len(hit)})

    cols = ["row_number", "rule_id", "rule_name", "dimension",
            "order_id", "customer_id", "order_date", "amount", "status"]
    failed = pd.concat(parts)[cols].sort_values("row_number")
    summary = pd.DataFrame(summary_rows)

    failed_rows = set(failed["row_number"])
    valid = df[~df["row_number"].isin(failed_rows)].drop(columns="row_number")
    return valid, failed, summary