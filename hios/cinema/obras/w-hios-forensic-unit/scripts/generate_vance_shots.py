#!/usr/bin/env python3
"""
SHOT-GRAMMAR-001 — Vance IDENTITY Shots Generator
==================================================
Generates 10 IDENTITY shots for Marcus Vance using Runway Gen-4.
Each shot uses the LOCKED anchor as image reference.

Constitutional bindings: I9, I11, I14, I19
Model lock: WINDI-SPINE-MODEL-LOCK-20260604173447
Anchor lock: WINDI-ANCHOR-VANCE-LOCK-20260605103558

Usage:
    python generate_vance_shots.py [--dry-run]
"""

import os
import sys
import json
import time
import requests
import hashlib
from datetime import datetime
from pathlib import Path

# === CONFIGURATION ===
RUNWAY_API_KEY = os.environ.get("RUNWAY_API_KEY")
if not RUNWAY_API_KEY:
    # Load from .env
    env_path = Path("/opt/windi/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("RUNWAY_API_KEY="):
                RUNWAY_API_KEY = line.split("=", 1)[1].strip()
                break

ANCHOR_PATH = Path("/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/marcus.vance.anchor.v1.png")
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/shots/vance")
MODEL_LOCK = "WINDI-SPINE-MODEL-LOCK-20260604173447"
ANCHOR_LOCK = "WINDI-ANCHOR-VANCE-LOCK-20260605103558"

# === VANCE SHOTS (from SHOT-GRAMMAR-001) ===
VANCE_SHOTS = [
    {
        "id": "S06-01",
        "scene": 6,
        "description": "Vance emerges from shadow",
        "emotional": False,
        "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, emerging from shadows into dim blue light. Interpol inspector, authoritative presence. Cinematic lighting, noir atmosphere, 4K.",
        "notes": "First appearance"
    },
    {
        "id": "S06-02",
        "scene": 6,
        "emotional": True,
        "description": "Vance's face loses color",
        "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, face draining of color in recognition. Shock and disbelief. Blue bunker lighting reflecting on face. Close-up, cinematic, 4K.",
        "notes": "Recognition moment ⭐"
    },
    {
        "id": "S07-01",
        "scene": 7,
        "emotional": True,
        "description": "Vance's face — ancient pain",
        "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, face showing deep ancient pain. Vulnerability beneath authority. Server room blue light. Close-up portrait, cinematic, 4K.",
        "notes": "Vulnerability ⭐"
    },
    {
        "id": "S09-01",
        "scene": 9,
        "emotional": False,
        "description": "Vance at screen with team",
        "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, standing at large screen with team. Professional intensity. Blue light from monitors. Medium shot, cinematic, 4K.",
        "notes": "Group shot (Vance focus)"
    },
    {
        "id": "S09-02",
        "scene": 9,
        "emotional": True,
        "description": "Vance's non-response",
        "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, face showing weighted silence. Not speaking but communicating everything. Blue ambient light. Close-up, cinematic, 4K.",
        "notes": "Weighted silence ⭐"
    },
    {
        "id": "S11-01",
        "scene": 11,
        "emotional": False,
        "description": "Vance enters confrontation",
        "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, entering corporate office with authority. Interpol badge visible. Natural daylight through windows. Medium shot, cinematic, 4K.",
        "notes": "Authority"
    },
    {
        "id": "S14-01",
        "scene": 14,
        "emotional": False,
        "description": "Vance at window",
        "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, standing at window looking at Frankfurt cityscape. Reflective moment. Golden hour light. Medium shot, cinematic, 4K.",
        "notes": "Corridor aftermath"
    },
    {
        "id": "S14-02",
        "scene": 14,
        "emotional": True,
        "description": "Vance's weighted answer",
        "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, face showing the weight of truth over survival. Deep conviction. Soft corridor light. Close-up portrait, cinematic, 4K.",
        "notes": "Truth > survival ⭐"
    },
    {
        "id": "S15-01",
        "scene": 15,
        "emotional": True,
        "description": "Vance alone at monitor, red eyes",
        "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, alone at monitor late at night, eyes red from exhaustion and emotion. Blue screen glow on face. Close-up, cinematic, 4K.",
        "notes": "Emotional close ⭐"
    },
    {
        "id": "S07-02",
        "scene": 7,
        "emotional": False,
        "description": "Vance observing analysis",
        "prompt": "Middle-aged man with grey slicked-back hair, clean-shaven, dark suit, watching analysis on screen with focused intensity. Professional observation. Blue bunker lighting. Medium close-up, cinematic, 4K.",
        "notes": "Working shot (fills count to 10)"
    }
]

def upload_image_to_runway(image_path: Path) -> str:
    """Upload anchor image and get URL for reference."""
    # Runway accepts base64 or URL
    # For simplicity, we'll use base64 in the prompt
    import base64
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def generate_shot(shot: dict, anchor_base64: str, dry_run: bool = False) -> dict:
    """Generate a single shot using Runway Gen-4 with image reference."""

    result = {
        "shot_id": shot["id"],
        "scene": shot["scene"],
        "description": shot["description"],
        "emotional": shot["emotional"],
        "status": "PENDING",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    if dry_run:
        result["status"] = "DRY_RUN"
        result["prompt"] = shot["prompt"]
        print(f"  [DRY] {shot['id']}: {shot['description']}")
        return result

    # Runway Gen-4 API
    headers = {
        "Authorization": f"Bearer {RUNWAY_API_KEY}",
        "Content-Type": "application/json",
        "X-Runway-Version": "2024-11-06"
    }

    payload = {
        "model": "gen4_turbo",
        "promptImage": f"data:image/png;base64,{anchor_base64}",
        "promptText": shot["prompt"],
        "duration": 5,
        "ratio": "1280:720"
    }

    try:
        # Start generation
        resp = requests.post(
            "https://api.dev.runwayml.com/v1/image_to_video",
            headers=headers,
            json=payload,
            timeout=30
        )

        if resp.status_code != 200:
            result["status"] = "ERROR"
            result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
            print(f"  [ERR] {shot['id']}: {result['error']}")
            return result

        data = resp.json()
        task_id = data.get("id")
        result["task_id"] = task_id
        result["status"] = "QUEUED"
        print(f"  [QUE] {shot['id']}: task_id={task_id}")

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
        print(f"  [ERR] {shot['id']}: {e}")

    return result

def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("SHOT-GRAMMAR-001 — Vance IDENTITY Shots Generator")
    print("=" * 60)
    print(f"Model Lock: {MODEL_LOCK}")
    print(f"Anchor Lock: {ANCHOR_LOCK}")
    print(f"Anchor: {ANCHOR_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 60)

    # Verify anchor exists
    if not ANCHOR_PATH.exists():
        print(f"[FATAL] Anchor not found: {ANCHOR_PATH}")
        sys.exit(1)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load anchor
    print("\nLoading anchor image...")
    anchor_base64 = upload_image_to_runway(ANCHOR_PATH) if not dry_run else ""

    # Calculate anchor hash for provenance
    with open(ANCHOR_PATH, "rb") as f:
        anchor_hash = hashlib.sha256(f.read()).hexdigest()

    print(f"Anchor hash: sha256:{anchor_hash[:16]}...")

    # Generate shots
    print(f"\nGenerating {len(VANCE_SHOTS)} shots...")
    print("-" * 40)

    results = []
    emotional_count = 0
    identity_count = 0

    for shot in VANCE_SHOTS:
        result = generate_shot(shot, anchor_base64, dry_run)
        results.append(result)

        if shot["emotional"]:
            emotional_count += 1
        identity_count += 1

        if not dry_run:
            time.sleep(2)  # Rate limiting

    # Summary
    print("-" * 40)
    print(f"\nSummary:")
    print(f"  Total IDENTITY: {identity_count}")
    print(f"  Emotional (⭐): {emotional_count}")
    print(f"  Queued: {sum(1 for r in results if r['status'] == 'QUEUED')}")
    print(f"  Errors: {sum(1 for r in results if r['status'] == 'ERROR')}")

    # Save manifest
    manifest = {
        "generator": "SHOT-GRAMMAR-001 Vance Generator",
        "model_lock": MODEL_LOCK,
        "anchor_lock": ANCHOR_LOCK,
        "anchor_hash": f"sha256:{anchor_hash}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dry_run": dry_run,
        "shots": results
    }

    manifest_path = OUTPUT_DIR / f"GENERATION_MANIFEST_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest saved: {manifest_path}")

    if not dry_run:
        print("\n[NEXT] Run poll_vance_shots.py to check completion and download videos")
        print("[NEXT] Run measure_vance_shots.py to validate against anchor")

if __name__ == "__main__":
    main()
