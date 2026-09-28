# Cloud Data Quality & Analytics Testing Platform

A data-quality testing project that validates an orders dataset, reconciles source and target data using SQL, and reports quality metrics on a Power BI dashboard.

**Tech stack:** Python, Pandas, SQL (PostgreSQL), AWS S3, Power BI, PyTest, Git

---

## Project Overview

Bad data leads to wrong reports. This project checks a 2,000-record orders dataset for data-quality issues before it reaches a dashboard. It validates records against 10 rules, reconciles source and target data, logs failed records, and shows the results in Power BI.

## Architecture

```
CSV Data → AWS S3 → Python Validation → SQL Database → Quality Checks → Power BI Dashboard
```

1. **Source:** Orders CSV with deliberately seeded errors
2. **Storage:** Raw file stored in AWS S3
3. **Validation:** Python script applies 10 data-quality rules
4. **Database:** Valid records, failed records, and rule results are loaded into SQL tables
5. **Reconciliation:** SQL queries compare source and target counts and totals
6. **Reporting:** Power BI dashboard shows data-quality metrics

## Key Results

| Metric | Result |
|---|---|
| Records tested | 2,000 |
| Validation rules | 10 |
| Data issues detected | [150+] |
| Automated test cases (PyTest) | [15] |
| Source-to-target reconciliation | [Counts and totals match after failed records are separated] |

## Validation Rules

| # | Rule | Data-quality dimension |
|---|---|---|
| 1 | Missing or null values in required fields | Completeness |
| 2 | Duplicate order IDs | Uniqueness |
| 3 | Invalid order ID format | Validity |
| 4 | Invalid or unparseable dates | Validity |
| 5 | Future-dated orders | Validity |
| 6 | Negative or zero amounts | Accuracy |
| 7 | Data type mismatches | Consistency |
| 8 | Invalid status values | Validity |
| 9 | Source vs target record count mismatch | Completeness |
| 10 | Source vs target total amount mismatch | Accuracy |

*(Edit this table to match your real 10 rules.)*

## Folder Structure

```
Cloud-Data-Quality-Analytics-Testing-Platform/
├── data/            # Raw and seeded CSV files
├── src/             # validate.py, load_db.py, s3_utils.py
├── sql/             # Schema and reconciliation queries
├── tests/           # PyTest test cases
├── docs/            # Test cases, defect log, screenshots
└── README.md
```

## How to Run

**1. Clone the repository**
```bash
git clone https://github.com/Udaypolishetty/Cloud-Data-Quality-Analytics-Testing-Platform.git
cd Cloud-Data-Quality-Analytics-Testing-Platform
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure AWS (optional)**

Set your AWS credentials with `aws configure` and update the bucket name in the config. Do not commit credentials to the repository.

**4. Run validation**
```bash
python src/validate.py
```

**5. Load results into the database**
```bash
python src/load_db.py
```

**6. Run the tests**
```bash
pytest tests/ -v
```

## Testing Approach

- **Automated tests:** [15] PyTest cases cover each rule with valid, invalid, and boundary inputs.
- **Seeded defects:** The dataset contains known errors (nulls, duplicates, invalid dates, negative amounts), so the framework's output can be checked against what was planted.
- **Reconciliation:** SQL queries compare record counts and amount totals between source and target.
- **Dashboard verification:** Each Power BI metric was cross-checked against an independent SQL query.
- **Documentation:** Test cases and the defect log are in the `docs/` folder.

## SQL Reconciliation Example

```sql
-- Record count check
SELECT
  (SELECT COUNT(*) FROM orders_raw)    AS source_count,
  (SELECT COUNT(*) FROM orders_clean)  AS valid_count,
  (SELECT COUNT(*) FROM failed_records) AS failed_count;

-- Total amount check
SELECT
  (SELECT SUM(amount) FROM orders_raw)   AS source_total,
  (SELECT SUM(amount) FROM orders_clean) AS valid_total;
```

## Dashboard

The Power BI dashboard shows:

- Total, valid, and failed records
- Data-quality percentage
- Duplicate and missing-value counts
- Failed validation rules
- Data-quality trend over time

![Dashboard](docs/dashboard.png)

## What I Learned

- Writing validation rules based on data-quality dimensions
- Reconciling source and target data with SQL
- Automating checks with PyTest
- Documenting test cases and defects clearly
- Moving data through AWS S3 into a SQL database

## Limitations and Future Improvements

- Uses a small sample dataset, not production-scale data
- AWS Glue and Athena could be added for ETL and querying files in S3
- GitHub Actions could run the PyTest suite on every commit
- Validation could be scheduled to run daily

## Author

**Uday Polishetty**
