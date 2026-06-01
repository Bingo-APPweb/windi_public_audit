#!/usr/bin/env python3
"""
S07 Generation — Chegada da Polícia
WINDI-HIOS Cinema · O Peso do Eco v2

Scene: Helena arrives at crime scene with Bavarian police
Key requirement: BMW/VW POLIZEI vehicles (green/silver/blue)

Sealed: §139 31 Mai 2026
Invariants: I9, I11, I14
"""
import os
import base64
import time
from datetime import datetime
from runwayml import RunwayML

# API Key from environment or hardcoded for this workflow
os.environ["RUNWAYML_API_SECRET"] = os.getenv("RUNWAY_API_KEY", "key_3831dff2c3ffdbda5363f300b320422be856d0acd6f99459baa6ed9c869b125f2dc9a6d25a4e282bb453b7890946cfb685153faa4fb027d60fa50b29616d0d85")

# Helena anchor image (from S13 - same character)
HELENA_ANCHOR = "/opt/windi/hios/visual/producer/obras/o-peso-do-eco/_forense/frames/S13_helena_sozinha_01.jpg"

# Output directory
OUTPUT_DIR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/production/renders"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load anchor image
print("=" * 60)
print("S07 — CHEGADA DA POLÍCIA")
print("WINDI-HIOS Cinema · O Peso do Eco v2")
print("=" * 60)

with open(HELENA_ANCHOR, "rb") as f:
    helena_b64 = base64.b64encode(f.read()).decode()
helena_uri = f"data:image/jpeg;base64,{helena_b64}"

print(f"\n🎬 Generating S07 with Runway Gen-3 / Veo 3.1")
print(f"   Anchor: Helena (S13)")
print(f"   Image size: {len(helena_b64):,} bytes (base64)")

# PROMPT — carefully crafted for Bavarian jurisdiction (max 1000 chars for Runway)
PROMPT = """German police crime scene, misty Bavarian forest, cold autumn morning.

BMW police car with "POLIZEI" text, green/silver/blue livery, blue lights flashing on wet tree trunks.

Woman from reference image (Helena, 45, detective) arrives. Dark navy coat, blonde hair pulled back. Walks under police tape on wet leaves. Serious expression.

Background: forensic team in white suits. Spruce/fir forest, fog between trunks. Wet autumn leaves. Blue police lights reflecting off fog.

Cinematic crime drama atmosphere. German setting only."""

print(f"\n📝 Prompt preview:\n{PROMPT[:200]}...\n")

# Initialize client
client = RunwayML()

try:
    print("⏳ Submitting generation request...")

    task = client.image_to_video.create(
        model="gen3a_turbo",  # or "veo3.1" if available
        prompt_image=[{
            "uri": helena_uri,
            "position": "first"
        }],
        prompt_text=PROMPT,
        ratio="1280:768",
        duration=5  # 5 seconds, can extend in post
    )

    print(f"\n✅ Task created: {task.id}")
    print(f"   Status: {task.status}")

    # Wait for completion
    print("\n⏳ Waiting for generation (this may take 2-5 minutes)...")
    start_time = time.time()

    result = task.wait_for_task_output()

    elapsed = time.time() - start_time
    print(f"\n🎬 Task complete in {elapsed:.1f}s!")

    # Save metadata
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metadata = {
        "scene": "S07",
        "title": "Chegada da Polícia",
        "task_id": task.id,
        "status": "GENERATED",
        "prompt": PROMPT,
        "anchor": HELENA_ANCHOR,
        "timestamp": timestamp,
        "duration_seconds": elapsed,
        "result": str(result),
        "validation_required": [
            "BMW/VW POLIZEI vehicles (green/silver/blue)",
            "Helena: navy coat, blonde hair pulled back, 45 years",
            "Bavarian forest: spruce/fir, no tropical",
            "Atmosphere: fog, wet leaves, blue lights"
        ]
    }

    import json
    meta_file = f"{OUTPUT_DIR}/S07_generation_{timestamp}.json"
    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n📄 Metadata saved: {meta_file}")
    print(f"\n🔍 VALIDATION CHECKLIST:")
    for item in metadata["validation_required"]:
        print(f"   [ ] {item}")

    print(f"\n✅ S07 generation complete. Awaiting Human Dragon validation (I9).")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
