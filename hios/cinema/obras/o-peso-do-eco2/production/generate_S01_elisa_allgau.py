#!/usr/bin/env python3
"""
S01 Generation — O Registo da Vida
WINDI-HIOS Cinema · O Peso do Eco v2

Scene: Elisa (content creator, ~30) records vlog in Allgäu at golden sunset
Key requirements:
  - Elisa v2: vibrante, content creator energy
  - Allgäu Alps: native forest, alpine valley view
  - Golden hour light
  - WINDI Ledger indicator diegético (discrete)
  - Marcus sedan parked on trail (background, easy to miss)

Sealed: §139 31 Mai 2026
Invariants: I9, I11, I14
SCREENPLAY canonical line: "Hallo meine Lieben! Ich zeige euch heute
einen atemberaubenden Blick auf die Alpen — hier in meiner Lieblingsregion, dem Allgäu."
"""
import os
import base64
import time
from datetime import datetime
from runwayml import RunwayML

# API Key
os.environ["RUNWAYML_API_SECRET"] = os.getenv("RUNWAY_API_KEY", "key_3831dff2c3ffdbda5363f300b320422be856d0acd6f99459baa6ed9c869b125f2dc9a6d25a4e282bb453b7890946cfb685153faa4fb027d60fa50b29616d0d85")

# Elisa v2 anchor image
ELISA_ANCHOR = "/home/windi/hios/cinema/obras/o-peso-do-eco/_forense/obra2-v2/elisa_anchor_v2_1280x720.png"

# Output directory
OUTPUT_DIR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/production/renders"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load anchor image
print("=" * 60)
print("S01 — O REGISTO DA VIDA")
print("WINDI-HIOS Cinema · O Peso do Eco v2")
print("=" * 60)

with open(ELISA_ANCHOR, "rb") as f:
    elisa_b64 = base64.b64encode(f.read()).decode()
elisa_uri = f"data:image/png;base64,{elisa_b64}"

print(f"\n🎬 Generating S01 with Runway Gen-3 / Veo 3.1")
print(f"   Anchor: Elisa v2 (content creator)")
print(f"   Image size: {len(elisa_b64):,} bytes (base64)")

# PROMPT — Elisa content creator in Allgäu (max 1000 chars for Runway)
PROMPT = """Young blonde German woman (from reference, Elisa, early 30s) recording selfie vlog on smartphone in Allgäu forest at golden sunset.

Golden hour light through spruce trees, backlit autumn leaves. She holds phone at arm's length, talking warmly, gestures with free hand, smiles at camera. Content creator energy - vibrant, genuine joy.

Alpine valley glimpse through trees. Dark sedan barely visible on forest trail behind her. Cinematic warmth, life and light."""

print(f"\n📝 Prompt preview:\n{PROMPT[:200]}...\n")

# Initialize client
client = RunwayML()

try:
    print("⏳ Submitting generation request...")

    task = client.image_to_video.create(
        model="gen3a_turbo",  # or "veo3.1" if available
        prompt_image=[{
            "uri": elisa_uri,
            "position": "first"
        }],
        prompt_text=PROMPT,
        ratio="1280:768",
        duration=5  # 5 seconds for the vlog clip
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
        "scene": "S01",
        "title": "O Registo da Vida",
        "task_id": task.id,
        "status": "GENERATED",
        "prompt": PROMPT,
        "anchor": ELISA_ANCHOR,
        "timestamp": timestamp,
        "duration_seconds": elapsed,
        "result": str(result),
        "canonical_line_de": "Hallo meine Lieben! Ich zeige euch heute einen atemberaubenden Blick auf die Alpen — hier in meiner Lieblingsregion, dem Allgäu.",
        "validation_required": [
            "Elisa v2: content creator energy, vibrant, warm",
            "Selfie POV: phone at arm's length, talking to camera",
            "Allgäu setting: spruce/fir forest, alpine valley glimpse",
            "Golden hour: warm sunset light through trees",
            "Marcus sedan: dark car on trail, barely visible (PROOF CHAIN)",
            "NO tropical vegetation, NO eucalyptus"
        ],
        "post_production_notes": [
            "Add WINDI Ledger indicator to phone screen (diegetic, per §296)",
            "Audio: German voice-over with canonical line",
            "Verify sedan visible for S16 continuity"
        ]
    }

    import json
    meta_file = f"{OUTPUT_DIR}/S01_generation_{timestamp}.json"
    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n📄 Metadata saved: {meta_file}")
    print(f"\n🔍 VALIDATION CHECKLIST:")
    for item in metadata["validation_required"]:
        print(f"   [ ] {item}")

    print(f"\n📝 POST-PRODUCTION:")
    for item in metadata["post_production_notes"]:
        print(f"   • {item}")

    print(f"\n✅ S01 generation complete. Awaiting Human Dragon validation (I9).")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
