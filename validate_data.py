"""
PPM Data Quality Dashboard — Validation & Exception Tracking
==============================================================
Scans project_master_data.csv against employee_master.csv,
detects data-quality issues, logs them as exceptions, and
simulates ticket resolution lifecycle.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import uuid

random.seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# Load source data
# ─────────────────────────────────────────────────────────────────────────────
employees = pd.read_csv("employee_master.csv")
projects = pd.read_csv("project_master_data.csv")

valid_employee_ids = set(employees["employee_id"].tolist())

exceptions: list[dict] = []
exc_counter = 1000


def _next_id() -> str:
    global exc_counter
    exc_counter += 1
    return f"EXC{exc_counter}"


def _raise_date() -> str:
    """Random date_raised in the last 90 days."""
    d = datetime(2026, 7, 1) + timedelta(days=random.randint(0, 90))
    return d.strftime("%Y-%m-%d")


# ─────────────────────────────────────────────────────────────────────────────
# Rule 1 — Duplicate project_id
# ─────────────────────────────────────────────────────────────────────────────
dup_mask = projects.duplicated(subset=["project_id"], keep=False)
dup_ids = projects.loc[dup_mask, "project_id"].unique()
for pid in dup_ids:
    exceptions.append({
        "exception_id": _next_id(),
        "project_id": pid,
        "issue_type": "Duplicate Project ID",
        "severity": "High",
        "detail": f"project_id '{pid}' appears multiple times in the master data.",
        "status": "Open",
        "date_raised": _raise_date(),
        "date_resolved": None,
        "resolution_notes": None,
    })

# ─────────────────────────────────────────────────────────────────────────────
# Rule 2 — Missing owner_id
# ─────────────────────────────────────────────────────────────────────────────
missing_owner = projects[projects["owner_id"].isna()]
for _, row in missing_owner.iterrows():
    exceptions.append({
        "exception_id": _next_id(),
        "project_id": row["project_id"],
        "issue_type": "Missing Owner ID",
        "severity": "High",
        "detail": f"owner_id is null for project '{row['project_id']}'.",
        "status": "Open",
        "date_raised": _raise_date(),
        "date_resolved": None,
        "resolution_notes": None,
    })

# ─────────────────────────────────────────────────────────────────────────────
# Rule 3 — Missing budget
# ─────────────────────────────────────────────────────────────────────────────
missing_budget = projects[projects["budget"].isna()]
for _, row in missing_budget.iterrows():
    exceptions.append({
        "exception_id": _next_id(),
        "project_id": row["project_id"],
        "issue_type": "Missing Budget",
        "severity": "Medium",
        "detail": f"budget is null for project '{row['project_id']}'.",
        "status": "Open",
        "date_raised": _raise_date(),
        "date_resolved": None,
        "resolution_notes": None,
    })

# ─────────────────────────────────────────────────────────────────────────────
# Rule 4 — Invalid owner reference
# ─────────────────────────────────────────────────────────────────────────────
has_owner = projects.dropna(subset=["owner_id"])
invalid_ref = has_owner[~has_owner["owner_id"].isin(valid_employee_ids)]
for _, row in invalid_ref.iterrows():
    exceptions.append({
        "exception_id": _next_id(),
        "project_id": row["project_id"],
        "issue_type": "Invalid Owner Reference",
        "severity": "High",
        "detail": (
            f"owner_id '{row['owner_id']}' in project '{row['project_id']}' "
            f"does not exist in employee_master."
        ),
        "status": "Open",
        "date_raised": _raise_date(),
        "date_resolved": None,
        "resolution_notes": None,
    })

# ─────────────────────────────────────────────────────────────────────────────
# Rule 5 — Invalid date range (end_date < start_date)
# ─────────────────────────────────────────────────────────────────────────────
projects["_sd"] = pd.to_datetime(projects["start_date"], errors="coerce")
projects["_ed"] = pd.to_datetime(projects["end_date"], errors="coerce")
bad_dates = projects[projects["_ed"] < projects["_sd"]]
for _, row in bad_dates.iterrows():
    exceptions.append({
        "exception_id": _next_id(),
        "project_id": row["project_id"],
        "issue_type": "Invalid Date Range",
        "severity": "Medium",
        "detail": (
            f"end_date ({row['end_date']}) is before start_date "
            f"({row['start_date']}) for project '{row['project_id']}'."
        ),
        "status": "Open",
        "date_raised": _raise_date(),
        "date_resolved": None,
        "resolution_notes": None,
    })
projects.drop(columns=["_sd", "_ed"], inplace=True)

# ─────────────────────────────────────────────────────────────────────────────
# Build exceptions DataFrame
# ─────────────────────────────────────────────────────────────────────────────
exc_df = pd.DataFrame(exceptions)

# ── Summary ──────────────────────────────────────────────────────────────────
print("\n╔══════════════════════════════════════════════════╗")
print("║   DATA-QUALITY EXCEPTION SUMMARY                ║")
print("╠══════════════════════════════════════════════════╣")
summary = exc_df["issue_type"].value_counts()
for issue, count in summary.items():
    print(f"║  {issue:<36} {count:>4}     ║")
print(f"╠══════════════════════════════════════════════════╣")
print(f"║  {'TOTAL':<36} {len(exc_df):>4}     ║")
print(f"╚══════════════════════════════════════════════════╝\n")


# ─────────────────────────────────────────────────────────────────────────────
# Ticket Resolution Simulation
# ─────────────────────────────────────────────────────────────────────────────
RESOLUTION_TEMPLATES = {
    "Duplicate Project ID": [
        "Merged duplicate records after confirming with PMO lead.",
        "Removed duplicate row; retained original entry with correct budget.",
        "De-duplicated by archiving the later entry per governance policy.",
    ],
    "Missing Owner ID": [
        "Corrected owner_id after confirming with project manager.",
        "Assigned to department head as interim owner pending formal assignment.",
        "Updated owner_id based on HR onboarding records.",
    ],
    "Missing Budget": [
        "Budget value added after finance team confirmed allocation.",
        "Updated budget from approved project charter (v2.1).",
        "Set budget to $0 — internal project with no direct cost allocation.",
    ],
    "Invalid Owner Reference": [
        "Corrected owner_id to active employee after verifying org chart.",
        "Owner had been terminated; reassigned to successor per HR records.",
        "Fixed typo in employee_id; validated against employee_master.",
    ],
    "Invalid Date Range": [
        "Swapped start_date and end_date — confirmed correct dates with PM.",
        "Corrected end_date based on revised project schedule.",
        "Updated start_date from project kick-off meeting minutes.",
    ],
}

STATUS_CHOICES = ["Closed", "In Progress"]
status_weights = [0.60, 0.15]  # remaining 25% stay Open

indices = exc_df.index.tolist()
random.shuffle(indices)

close_count = int(0.60 * len(indices))
in_progress_count = int(0.15 * len(indices))

close_indices = indices[:close_count]
in_progress_indices = indices[close_count : close_count + in_progress_count]

for idx in close_indices:
    raised = datetime.strptime(exc_df.at[idx, "date_raised"], "%Y-%m-%d")
    resolved = raised + timedelta(days=random.randint(1, 14))
    issue = exc_df.at[idx, "issue_type"]
    exc_df.at[idx, "status"] = "Closed"
    exc_df.at[idx, "date_resolved"] = resolved.strftime("%Y-%m-%d")
    exc_df.at[idx, "resolution_notes"] = random.choice(
        RESOLUTION_TEMPLATES.get(issue, ["Resolved per standard procedure."])
    )

for idx in in_progress_indices:
    exc_df.at[idx, "status"] = "In Progress"

# ── Save ─────────────────────────────────────────────────────────────────────
exc_df.to_csv("data_quality_exceptions.csv", index=False)

# ── Post-resolution summary ─────────────────────────────────────────────────
status_summary = exc_df["status"].value_counts()
print("Ticket Status Distribution:")
for st, cnt in status_summary.items():
    print(f"  {st:<15} {cnt}")
print(f"\n✔ data_quality_exceptions.csv  →  {len(exc_df)} exception records saved.")

# ── Refresh embedded dashboard data so dashboard.html works with no local server ──
import json
with open("data_quality_exceptions.csv") as f:
    csv_text = f.read()
with open("data.js", "w") as f:
    f.write("// Auto-generated by validate_data.py — embeds the CSV so dashboard.html works offline (no server needed).\n")
    f.write("const EXCEPTIONS_CSV = " + json.dumps(csv_text) + ";\n")
print("✔ data.js refreshed for dashboard.html")
