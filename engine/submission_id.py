"""
WINDI Submission ID Generator v1.0
Heritage: traceId -> submission_id. Format: REG-YYYYMMDD-XXXX
AI processes. Human decides. WINDI guarantees.
"""
import json, os
from datetime import datetime, timezone

def generate_submission_id(counter_dir, prefix="REG"):
    os.makedirs(counter_dir, exist_ok=True)
    counter_file = os.path.join(counter_dir, "counter.json")
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    day_key = f"{prefix}-{today}"

    counters = {}
    if os.path.exists(counter_file):
        with open(counter_file) as f:
            counters = json.load(f)

    count = counters.get(day_key, 0) + 1
    counters[day_key] = count
    with open(counter_file, "w") as f:
        json.dump(counters, f, indent=2)

    return f"{prefix}-{today}-{str(count).zfill(4)}"

def build_submission_header(submission_id, level, policy_version, config_hash):
    return (
        f"WINDI-SUBMISSION-ID: {submission_id}\n"
        f"Governance-Level: {level}\n"
        f"Policy-Version: {policy_version}\n"
        f"Configuration-Hash: {config_hash}\n"
        f"Generated-At: {datetime.now(timezone.utc).isoformat()}"
    )
