#!/usr/bin/env python3
"""
SORA 2 Diagnostic — Forensic API Health Check
Tests if SORA 2 is accepting and processing jobs.

Usage:
    python3 sora_diagnostic.py

Guardian's diagnostic protocol:
    TEST-A: Simple image-like prompt (red apple)
    Check: Does job enter queue? Does status change?
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

# Load from .env.openai if not in environment
env_path = "/opt/windi/hios/.env.openai"
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"')
                os.environ["OPENAI_API_KEY"] = key

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BASE_URL = "https://api.openai.com/v1/videos"

def diagnostic_submit():
    """Submit minimal test job and capture exact API response."""

    print("=" * 60)
    print("SORA 2 DIAGNOSTIC — WINDI Forensic Health Check")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found")
        return None

    print(f"🔑 API Key: {OPENAI_API_KEY[:20]}...{OPENAI_API_KEY[-8:]}")
    print()

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    # Guardian's minimal test: red apple on white table
    test_prompt = "red apple on white table, studio photography, simple background"

    files = {
        "model": (None, "sora-2"),
        "prompt": (None, test_prompt),
        "size": (None, "1280x720"),
        "seconds": (None, "8")
    }

    print("📤 TEST-A: Submitting minimal job...")
    print(f"   Prompt: {test_prompt}")
    print(f"   Model: sora-2")
    print(f"   Duration: 8s")
    print()

    try:
        response = requests.post(
            BASE_URL,
            headers=headers,
            files=files,
            timeout=60
        )
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None

    print(f"📥 HTTP Status: {response.status_code}")
    print()

    # Capture full response for forensic analysis
    print("=" * 60)
    print("RAW API RESPONSE (for Guardian analysis)")
    print("=" * 60)

    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(f"Raw text: {response.text[:1000]}")
        data = {"raw": response.text}

    print()
    print("=" * 60)

    # Interpret response
    if response.status_code == 401:
        print("🔴 DIAGNOSIS: API Key invalid or expired")
        return data

    if response.status_code == 429:
        print("🟡 DIAGNOSIS: Rate limited / Quota exhausted")
        return data

    if response.status_code == 404:
        print("🔴 DIAGNOSIS: Endpoint not found — possible API deprecation")
        return data

    if response.status_code in [500, 502, 503]:
        print("🔴 DIAGNOSIS: Backend error — infrastructure issue")
        return data

    if response.status_code in [200, 201, 202]:
        job_id = data.get("id")
        status = data.get("status", "unknown")
        print(f"🟢 Job accepted: {job_id}")
        print(f"   Initial status: {status}")

        if job_id:
            print()
            print("Polling status for 60 seconds...")
            poll_job(job_id, headers, max_wait=60)

    return data


def poll_job(job_id: str, headers: dict, max_wait: int = 60):
    """Poll job status and report changes."""

    url = f"{BASE_URL}/{job_id}"
    start = time.time()
    last_status = None

    while time.time() - start < max_wait:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            data = response.json()
            status = data.get("status", "unknown")

            if status != last_status:
                elapsed = int(time.time() - start)
                print(f"   [{elapsed:3d}s] Status: {status}")
                last_status = status

                # Full state dump on change
                if status not in ["pending", "queued"]:
                    print(f"         Full state: {json.dumps(data, indent=2)[:500]}")

            if status in ["succeeded", "completed", "complete"]:
                print()
                print("🟢 DIAGNOSIS: SORA 2 is OPERATIONAL")
                print("   Jobs are being processed successfully.")
                return True

            if status == "failed":
                error = data.get("error", data.get("failure_reason", "unknown"))
                print()
                print(f"🟡 DIAGNOSIS: Job failed with error: {error}")
                print("   API is responsive but generation failed.")
                return False

        except Exception as e:
            print(f"   Poll error: {e}")

        time.sleep(5)

    print()
    print("🟠 DIAGNOSIS: Job stayed in queue/pending for 60s")
    print("   This matches Guardian's hypothesis:")
    print("   - Backend saturation")
    print("   - Dead queue")
    print("   - Endpoint accepting but not processing")
    print()
    print("   Recommendation: Check if this persists for hours.")
    print("   If so, likely infrastructure issue, not your account.")

    return None


if __name__ == "__main__":
    result = diagnostic_submit()

    print()
    print("=" * 60)
    print("Save this output for Guardian analysis")
    print("=" * 60)
