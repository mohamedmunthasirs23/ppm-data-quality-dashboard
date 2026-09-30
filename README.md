# PPM Data Quality & Exception Tracking Dashboard

> **Simulates the real-world workflow of a PPM (Project & Portfolio Management) systems-support analyst**: scanning project master data for integrity issues, raising trackable exceptions, resolving them through a support-ticket lifecycle, and monitoring data-quality health via a visual dashboard.

---

## Why This Project Exists

In any enterprise running SAP PPM, Planisware, Clarity, or similar tools, **project master data is the backbone** of portfolio reporting, resource planning, and financial roll-ups. A single orphaned owner reference or a duplicated project ID can cascade into incorrect dashboards, broken workflows, and audit findings.

This project models that entire data-governance cycle end-to-end — from data generation through detection, triage, resolution, and trend analysis — so that it can serve as a portfolio piece, training sandbox, or lightweight starter kit for real PPM data-quality programs.

---

## Validation Rules

| # | Rule | Issue Type | Severity | Why It Matters | Pass Criteria | Fail Criteria |
|---|------|-----------|----------|---------------|---------------|---------------|
| 1 | **Unique project ID** | Duplicate Project ID | High | Duplicates break aggregation, cause double-counting of budget/scope, and violate primary-key integrity. | Each `project_id` appears exactly once. | `project_id` appears more than once. |
| 2 | **Owner must exist** | Missing Owner ID | High | Every project needs an accountable owner for governance, approval chains, and status reporting. | `owner_id` is non-null for every row. | `owner_id` is null/blank. |
| 3 | **Budget populated** | Missing Budget | Medium | Null budgets skew financial roll-ups and prevent accurate portfolio-level cost tracking. | `budget` is non-null and numeric. | `budget` is null/blank. |
| 4 | **Valid owner reference** | Invalid Owner Reference | High | Referential integrity — if the referenced employee doesn't exist, downstream processes (notifications, approvals) fail silently. | `owner_id` exists in `employee_master.csv`. | `owner_id` value not found in `employee_master.csv`. |
| 5 | **Logical date range** | Invalid Date Range | Medium | An `end_date` before `start_date` indicates a data-entry error and produces negative durations in schedule reports. | `end_date >= start_date`. | `end_date < start_date`. |

---

## End-to-End Example

Below is a complete lifecycle walkthrough for one exception:

```
1. DETECTION
   validate_data.py scans project_master_data.csv and finds:
   → Project PRJ2047 has owner_id = "EMP9903", which does not exist
     in employee_master.csv

2. EXCEPTION RAISED
   exception_id : EXC1029
   project_id   : PRJ2047
   issue_type   : Invalid Owner Reference
   severity     : High
   status       : Open
   date_raised  : 2026-08-14
   detail       : "owner_id 'EMP9903' in project 'PRJ2047' does not
                   exist in employee_master."

3. INVESTIGATION
   The support analyst checks with the HR team and discovers that
   EMP9903 was a contractor whose record was never loaded into
   the employee master after onboarding.

4. RESOLUTION
   The analyst creates the employee record (or reassigns the project
   to an active employee), then updates the exception ticket:
   status           : Closed
   date_resolved    : 2026-08-19
   resolution_notes : "Corrected owner_id to active employee after
                       verifying org chart."

5. DASHBOARD IMPACT
   - Open count drops by 1; Closed count increases by 1
   - Average resolution time recalculates (5 days for this ticket)
   - The trend chart shows the resolved data point
```

---

## Dashboard Features

| Component | Description |
|-----------|-------------|
| **KPI Cards** | Total exceptions, Open, In Progress, Closed, Average Resolution Time (days) |
| **Bar Chart** | Exceptions by Issue Type — instantly shows which category needs the most attention |
| **Donut Chart** | Exceptions by Severity — High / Medium / Low distribution |
| **Trend Line** | Exceptions raised over time with cumulative overlay — tracks whether data quality is improving |
| **Exception Log** | Filterable table with status/severity dropdowns, color-coded pills |

---

## Project Structure

```
ppm-data-quality-dashboard/
├── employee_master.csv          # 40-row employee reference table
├── project_master_data.csv      # 306 project rows (with injected issues)
├── data_quality_exceptions.csv  # 37 exception/ticket records
├── generate_data.py             # Mock data generator with deliberate issues
├── validate_data.py             # Validation engine + ticket lifecycle simulator
├── dashboard.html               # Interactive web dashboard (entry point)
├── dashboard.css                # Dark-mode glassmorphism styling
├── dashboard.js                 # Chart.js visualizations + table rendering
└── README.md                    # This file
```

---

## Tools & Technologies

| Tool | Purpose |
|------|---------|
| **Python 3.12** | Data generation, validation scripting |
| **Pandas** | DataFrame operations, CSV I/O |
| **NumPy** | Random data generation, statistical distributions |
| **HTML / CSS / JavaScript** | Interactive dashboard UI |
| **Chart.js 4.x** | Bar, doughnut, and time-series line charts |
| **Git / GitHub** | Version control and public hosting |

---

## How to Run

```bash
# 1. Generate mock data
python generate_data.py

# 2. Run validation & create exception log
python validate_data.py

# 3. Open the dashboard
#    Serve locally (required for fetch() to load the CSV):
python -m http.server 8000
#    Then open http://localhost:8000/dashboard.html
```

---

## License

MIT — free to use, modify, and distribute.
