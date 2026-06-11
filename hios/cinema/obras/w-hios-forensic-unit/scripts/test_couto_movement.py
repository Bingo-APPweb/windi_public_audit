#!/usr/bin/env python3
"""
TEST COUTO MOVEMENT — Head Turn + Speaking
============================================
Validate anchor identity with real movement before generating 7 shots.

Liga IA+H: Human Dragon (I9) + CCode
Date: 09 Jun 2026
"""

import sys
import json
import time
import base64
from pathlib import Path
from datetime import datetime

import requests

ANCHOR_PATH = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.couto.anchor.v1.png")
OUTPUT_DIR = Path("/opt/windi/static/docs/hios-forensic/couto-anchor-review")

API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"

MOVEMENT_PROMPT = """A man in his mid-40s with slicked-back grey hair, completely clean-shaven, sharp angular jaw, dark calculating eyes. Wearing dark cashmere overcoat, white shirt, black tie. He turns his head slightly to the side while speaking with cold authority. Corporate executive delivering orders. Subtle head movement, lips moving as he speaks. Near-frontal to three-quarter angle. Professional corporate lighting. Cinematic 4K."""

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()

def load_api_key():
    for line in Path("/opt/windi/.env").read_text().splitlines():
        if line.startswith("RUNWAY_API_KEY="):
            return line.strip().split("=", 1)[1]
    return None

def load_anchor_base64():
    with open(ANCHOR_PATH, "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

def submit_job(api_key, prompt, image_data):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": API_VERSION,
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gen4_turbo",
        "promptImage": image_data,
        "promptText": prompt,
        "duration": 5,
        "ratio": "1280:720"
    }
    log(f"Prompt: {prompt[:80]}...")
    resp = requests.post(f"{API_BASE}/image_to_video", headers=headers, json=payload, timeout=60)
    if resp.status_code in [200, 201]:
        return resp.json().get("id")
    log(f"ERROR: {resp.status_code} - {resp.text[:200]}")
    return None

def poll_job(api_key, task_id, max_wait=300):
    headers = {"Authorization": f"Bearer {api_key}", "X-Runway-Version": API_VERSION}
    start = time.time()
    while time.time() - start < max_wait:
        resp = requests.get(f"{API_BASE}/tasks/{task_id}", headers=headers, timeout=30)
        result = resp.json()
        status = result.get("status", "unknown")
        if status == "SUCCEEDED":
            return result
        elif status == "FAILED":
            log(f"FAILED: {result.get('failureCode')}")
            return None
        log(f"{status} ({int(time.time()-start)}s)")
        time.sleep(10)
    return None

def download_video(result, filename):
    outputs = result.get("output", [])
    if not outputs:
        return None
    output_path = OUTPUT_DIR / filename
    resp = requests.get(outputs[0], timeout=120)
    if resp.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path
    return None

def main():
    log("=" * 60)
    log("TEST COUTO MOVEMENT — Head Turn + Speaking")
    log("=" * 60)

    api_key = load_api_key()
    if not api_key:
        log("FATAL: No API key")
        return

    image_data = load_anchor_base64()
    log(f"Anchor loaded: {ANCHOR_PATH.name}")

    task_id = submit_job(api_key, MOVEMENT_PROMPT, image_data)
    if not task_id:
        log("FATAL: Submit failed")
        return

    log(f"Task: {task_id}")
    result = poll_job(api_key, task_id)
    if not result:
        log("FATAL: Generation failed")
        return

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"couto-movement-test-{timestamp}.mp4"
    video_path = download_video(result, filename)

    if video_path:
        log(f"SUCCESS: {video_path}")
        log(f"URL: https://windi-domain.com/docs/hios-forensic/couto-anchor-review/{filename}")
    else:
        log("FATAL: Download failed")

if __name__ == "__main__":
    main()
