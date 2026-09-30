"""
PPM Data Quality Dashboard — Mock Data Generator
==================================================
Generates employee_master.csv and project_master_data.csv with
deliberately injected data-quality issues for validation testing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string

# ── reproducibility ──────────────────────────────────────────────────────────
np.random.seed(42)
random.seed(42)

# ── 1. Employee Master ──────────────────────────────────────────────────────
FIRST_NAMES = [
    "Aarav", "Priya", "Liam", "Sophia", "Mateo", "Fatima", "Noah", "Mia",
    "Ethan", "Zara", "Oliver", "Ananya", "James", "Chloe", "Lucas",
    "Isla", "Benjamin", "Amara", "Daniel", "Emily", "Alexander", "Sara",
    "William", "Nadia", "Henry", "Riya", "Samuel", "Leah", "David",
    "Maya", "Joseph", "Anika", "Charles", "Hana", "Thomas", "Layla",
    "Andrew", "Diya", "Ryan", "Nora",
]
LAST_NAMES = [
    "Sharma", "Patel", "Kim", "Garcia", "Müller", "Johnson", "Chen",
    "Williams", "Singh", "Brown", "Ali", "Davis", "Tanaka", "Martinez",
    "Anderson", "Nguyen", "Thomas", "Jackson", "Lee", "Harris",
    "Clark", "Lewis", "Robinson", "Walker", "Hall", "Young", "King",
    "Wright", "Scott", "Torres", "Hill", "Green", "Adams", "Baker",
    "Nelson", "Carter", "Mitchell", "Roberts", "Turner", "Phillips",
]

employee_ids = [f"EMP{1000 + i}" for i in range(40)]
employee_names = [
    f"{FIRST_NAMES[i]} {random.choice(LAST_NAMES)}" for i in range(40)
]

employees = pd.DataFrame({
    "employee_id": employee_ids,
    "employee_name": employee_names,
})
employees.to_csv("employee_master.csv", index=False)
print(f"✔ employee_master.csv  →  {len(employees)} rows")

# ── 2. Project Master Data (clean base) ─────────────────────────────────────
N = 300
STATUSES = ["Active", "On Hold", "Completed", "Cancelled"]
STATUS_WEIGHTS = [0.40, 0.15, 0.35, 0.10]

project_ids = [f"PRJ{2000 + i}" for i in range(N)]

# generate random start dates within last 3 years
base_date = datetime(2024, 1, 1)
start_dates = [
    base_date + timedelta(days=int(d))
    for d in np.random.randint(0, 900, size=N)
]
# end dates 30-365 days after start
end_dates = [
    sd + timedelta(days=int(d))
    for sd, d in zip(start_dates, np.random.randint(30, 365, size=N))
]

statuses = np.random.choice(STATUSES, size=N, p=STATUS_WEIGHTS).tolist()
owner_ids = np.random.choice(employee_ids, size=N).tolist()
budgets = np.round(np.random.uniform(10_000, 5_000_000, size=N), 2).tolist()

projects = pd.DataFrame({
    "project_id": project_ids,
    "owner_id": owner_ids,
    "status": statuses,
    "start_date": [d.strftime("%Y-%m-%d") for d in start_dates],
    "end_date": [d.strftime("%Y-%m-%d") for d in end_dates],
    "budget": budgets,
})

# ── 3. Inject Data-Quality Issues ───────────────────────────────────────────

# 3a. Duplicate project_id rows (~6 duplicates)
dup_indices = np.random.choice(range(N), size=6, replace=False)
dup_rows = projects.iloc[dup_indices].copy()
# Slightly alter some fields so they look like real duplicate-entry errors
for idx in dup_rows.index:
    dup_rows.at[idx, "budget"] = round(dup_rows.at[idx, "budget"] * 1.01, 2)
projects = pd.concat([projects, dup_rows], ignore_index=True)
print(f"  ↳ Injected {len(dup_rows)} duplicate project_id rows")

# 3b. Missing owner_id (~4% ≈ 12 rows)
null_owner_count = int(0.04 * len(projects))
null_owner_idx = np.random.choice(
    projects.index, size=null_owner_count, replace=False
)
projects.loc[null_owner_idx, "owner_id"] = np.nan
print(f"  ↳ Injected {null_owner_count} null owner_id values")

# 3c. Missing budget (~3% ≈ 9 rows)
null_budget_count = int(0.03 * len(projects))
null_budget_idx = np.random.choice(
    projects.index, size=null_budget_count, replace=False
)
projects.loc[null_budget_idx, "budget"] = np.nan
print(f"  ↳ Injected {null_budget_count} null budget values")

# 3d. Invalid owner references (owner_id not in employee_master)
invalid_owner_ids = ["EMP9901", "EMP9902", "EMP9903", "EMP9904", "EMP9905"]
inv_owner_idx = np.random.choice(
    projects.dropna(subset=["owner_id"]).index, size=5, replace=False
)
for i, idx in enumerate(inv_owner_idx):
    projects.at[idx, "owner_id"] = invalid_owner_ids[i]
print(f"  ↳ Injected {len(inv_owner_idx)} invalid owner_id references")

# 3e. Invalid date ranges (end_date < start_date)
inv_date_idx = np.random.choice(projects.index, size=5, replace=False)
for idx in inv_date_idx:
    sd = datetime.strptime(projects.at[idx, "start_date"], "%Y-%m-%d")
    # set end_date to 10-60 days BEFORE start_date
    bad_end = sd - timedelta(days=random.randint(10, 60))
    projects.at[idx, "end_date"] = bad_end.strftime("%Y-%m-%d")
print(f"  ↳ Injected {len(inv_date_idx)} invalid date ranges")

# ── Shuffle & save ──────────────────────────────────────────────────────────
projects = projects.sample(frac=1, random_state=42).reset_index(drop=True)
projects.to_csv("project_master_data.csv", index=False)
print(f"\n✔ project_master_data.csv  →  {len(projects)} rows (with issues)")
