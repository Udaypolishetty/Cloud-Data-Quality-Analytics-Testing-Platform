import pandas as pd

from rules import validate

CLEAN_ROW = {
    "order_id": "ORD00001",
    "customer_id": "CUST0001",
    "order_date": "2026-03-01",
    "amount": "100.50",
    "status": "Shipped",
}


def make_df(*overrides):
    """Build a small test dataset. Each override changes fields of a clean row."""
    rows = [{**CLEAN_ROW, **o} for o in overrides] or [dict(CLEAN_ROW)]
    return pd.DataFrame(rows, dtype="str")


def failed_rules(df):
    """Return the set of rule names that flagged at least one row."""
    _, failed, _ = validate(df)
    return set(failed["rule_name"])


# TC01 - a fully valid record should produce no failures
def test_tc01_clean_record_passes():
    assert failed_rules(make_df()) == set()


# TC02 - missing order date is flagged only as a completeness issue
def test_tc02_null_order_date():
    assert failed_rules(make_df({"order_date": None})) == {"NULL_ORDER_DATE"}


# TC03 - missing customer ID
def test_tc03_null_customer_id():
    assert failed_rules(make_df({"customer_id": None})) == {"NULL_CUSTOMER_ID"}


# TC04 - missing amount
def test_tc04_null_amount():
    assert failed_rules(make_df({"amount": None})) == {"NULL_AMOUNT"}


# TC05 - order ID in the wrong format
def test_tc05_invalid_order_id_format():
    assert failed_rules(make_df({"order_id": "ORD-XYZ"})) == {"INVALID_ORDER_ID"}


# TC06 - the second occurrence of an order ID is flagged, the first is not
def test_tc06_duplicate_order_id():
    df = make_df({}, {})  # two identical rows
    _, failed, _ = validate(df)
    assert list(failed["rule_name"]) == ["DUPLICATE_ORDER_ID"]
    assert list(failed["row_number"]) == [3]


# TC07 - date that is not a date at all
def test_tc07_invalid_date_text():
    assert failed_rules(make_df({"order_date": "not_a_date"})) == {"INVALID_DATE"}


# TC08 - date with an impossible month and day
def test_tc08_invalid_date_impossible_values():
    assert failed_rules(make_df({"order_date": "2026-13-45"})) == {"INVALID_DATE"}


# TC09 - order dated after the as-of date
def test_tc09_future_date():
    assert failed_rules(make_df({"order_date": "2026-12-25"})) == {"FUTURE_DATE"}


# TC10 - boundary: an order on the as-of date itself is valid
def test_tc10_boundary_date_on_cutoff_is_valid():
    assert failed_rules(make_df({"order_date": "2026-09-01"})) == set()


# TC11 - negative amount
def test_tc11_negative_amount():
    assert failed_rules(make_df({"amount": "-50.00"})) == {"NEGATIVE_AMOUNT"}


# TC12 - boundary: zero amount is invalid
def test_tc12_boundary_zero_amount():
    assert failed_rules(make_df({"amount": "0"})) == {"NEGATIVE_AMOUNT"}


# TC13 - text in the amount column is flagged once, and not as a negative
def test_tc13_amount_not_numeric():
    assert failed_rules(make_df({"amount": "abc"})) == {"AMOUNT_NOT_NUMERIC"}


# TC14 - status outside the allowed list
def test_tc14_invalid_status():
    assert failed_rules(make_df({"status": "Returnd"})) == {"INVALID_STATUS"}


# TC15 - reconciliation: valid + failed rows always equal total rows,
# even when one row has two defects
def test_tc15_reconciliation_counts_add_up():
    df = make_df(
        {"order_id": "ORD00001"},                                # valid
        {"order_id": "ORD00002"},                                # valid
        {"order_id": "ORD00003", "amount": "-5"},                # 1 defect
        {"order_id": "ORD00004", "customer_id": None,
         "amount": "-9"},                                        # 2 defects, 1 row
        {"order_id": "ORD00005", "status": "???"},               # 1 defect
    )
    valid, failed, _ = validate(df)
    assert len(valid) == 2
    assert failed["row_number"].nunique() == 3
    assert len(df) == len(valid) + failed["row_number"].nunique()