-- Reconciliation and data-quality checks
-- Each query returns: check_name, expected, actual, result

-- CHECK 1: source records = clean records + distinct failed records
WITH t AS (
  SELECT
    (SELECT COUNT(*) FROM orders_raw) AS e,
    (SELECT COUNT(*) FROM orders_clean)
      + (SELECT COUNT(DISTINCT row_num) FROM failed_records) AS a
)
SELECT 'record_count_reconciliation' AS check_name, e AS expected, a AS actual,
       CASE WHEN e = a THEN 'PASS' ELSE 'FAIL' END AS result
FROM t;

-- CHECK 2: source amount total = clean amount total + failed amount total
WITH t AS (
  SELECT
    (SELECT ROUND(SUM(CAST(amount AS REAL)), 2) FROM orders_raw) AS e,
    ROUND(
      (SELECT COALESCE(SUM(CAST(amount AS REAL)), 0) FROM orders_clean)
      + (SELECT COALESCE(SUM(CAST(amount AS REAL)), 0)
         FROM (SELECT row_num, amount FROM failed_records GROUP BY row_num)),
    2) AS a
)
SELECT 'amount_total_reconciliation' AS check_name, e AS expected, a AS actual,
       CASE WHEN ABS(e - a) < 0.01 THEN 'PASS' ELSE 'FAIL' END AS result
FROM t;

-- CHECK 3: failed count per rule in failed_records matches the validation summary
SELECT 'failed_by_rule_matches_summary' AS check_name, 0 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM validation_summary s
LEFT JOIN (SELECT rule_name, COUNT(*) AS c FROM failed_records GROUP BY rule_name) f
       ON f.rule_name = s.rule_name
WHERE s.failed_count <> COALESCE(f.c, 0);

-- CHECK 4: clean table has no duplicate order IDs
SELECT 'no_duplicate_ids_in_clean' AS check_name, 0 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM (SELECT order_id FROM orders_clean GROUP BY order_id HAVING COUNT(*) > 1);

-- CHECK 5: clean table has no missing values
SELECT 'no_nulls_in_clean' AS check_name, 0 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM orders_clean
WHERE order_id IS NULL OR customer_id IS NULL OR order_date IS NULL
   OR amount IS NULL OR status IS NULL;

-- CHECK 6: clean table has no zero or negative amounts
SELECT 'no_non_positive_amounts_in_clean' AS check_name, 0 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM orders_clean
WHERE CAST(amount AS REAL) <= 0;

-- CHECK 7: clean table has no future-dated orders
SELECT 'no_future_dates_in_clean' AS check_name, 0 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM orders_clean
WHERE order_date > '2026-09-01';

-- CHECK 8: clean table has only valid statuses
SELECT 'only_valid_statuses_in_clean' AS check_name, 0 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM orders_clean
WHERE status NOT IN ('Pending', 'Shipped', 'Delivered', 'Cancelled');

-- CHECK 9: every failed record points to a real source row
SELECT 'failed_rows_exist_in_raw' AS check_name, 0 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM failed_records f
LEFT JOIN orders_raw r ON f.row_num = r.row_num
WHERE r.row_num IS NULL;