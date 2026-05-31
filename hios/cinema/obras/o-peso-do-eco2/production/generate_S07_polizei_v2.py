#!/usr/bin/env python3
"""
S07 Generation v2 — Chegada da Polícia (First-Frame Method)
WINDI-HIOS Cinema · O Peso do Eco v2

First-frame: BMW Polizei Bayern (imagem de referência real)
Animation: Helena arrives, blue lights flash, fog in forest

Guardian recommendation: Use first-frame to guarantee livery,
prompt transforms background from residential to forest.

Sealed: §139 31 Mai 2026
Invariants: I9, I11, I14
"""
import os
import base64
import time
from datetime import datetime

# API Key
os.environ["RUNWAYML_API_SECRET"] = os.getenv("RUNWAY_API_KEY", "key_3831dff2c3ffdbda5363f300b320422be856d0acd6f99459baa6ed9c869b125f2dc9a6d25a4e282bb453b7890946cfb685153faa4fb027d60fa50b29616d0d85")

from runwayml import RunwayML

# First-frame: BMW Polizei Bayern
POLIZEI_IMAGE = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/production/references/S07_polizei/Screenshot 2026-05-31 160513.png"

# Output directory
OUTPUT_DIR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/production/renders"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("S07 v2 — CHEGADA DA POLÍCIA (First-Frame Method)")
print("WINDI-HIOS Cinema · O Peso do Eco v2")
print("=" * 60)

# Load first-frame image
with open(POLIZEI_IMAGE, "rb") as f:
    polizei_b64 = base64.b64encode(f.read()).decode()
polizei_uri = f"data:image/png;base64,{polizei_b64}"

print(f"\n🚔 First-frame: BMW Polizei Bayern")
print(f"   Image size: {len(polizei_b64):,} bytes (base64)")

# PROMPT — Transform background, animate scene (max 1000 chars)
# Priority: (1) Transform to forest, (2) Add Helena, (3) Animate lights
PROMPT = """Transform background to misty Bavarian forest crime scene. Cold autumn morning, fog between spruce trees, wet fallen leaves on ground.

Blue police lights start flashing, reflecting off fog and wet tree trunks.

Woman detective (Helena, 45, blonde hair pulled back, dark navy wool coat) walks into frame from right, approaches the police tape. Serious, determined expression.

Background: forensic team in white suits working. Forest clearing, overcast sky, cold atmosphere.

Camera: static wide shot, police car in foreground left, Helena entering right."""

print(f"\n📝 Prompt ({len(PROMPT)} chars):")
print(PROMPT[:200] + "..." if len(PROMPT) > 200 else PROMPT)

# Initialize client
client = RunwayML()

try:
    print("\n⏳ Submitting generation request (image-to-video)...")

    task = client.image_to_video.create(
        model="gen3a_turbo",
        prompt_image=polizei_uri,
        prompt_text=PROMPT,
        ratio="1280:768",
        duration=5
    )

    print(f"\n✅ Task created: {task.id}")

    # Poll for completion
    print("\n⏳ Waiting for generation...")
    start_time = time.time()

    while True:
        task_status = client.tasks.retrieve(task.id)
        status = task_status.status
        print(f"   Status: {status}")

        if status == "SUCCEEDED":
            elapsed = time.time() - start_time
            print(f"\n🎬 Task complete in {elapsed:.1f}s!")

            # Get output URL
            output_url = None
            if hasattr(task_status, 'output') and task_status.output:
                output_url = task_status.output[0] if isinstance(task_status.output, list) else task_status.output

            if output_url:
                print(f"\n📥 Output URL: {output_url}")

                # Download video
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"{OUTPUT_DIR}/S07_polizei_v2_{timestamp}.mp4"

                import urllib.request
                urllib.request.urlretrieve(output_url, output_file)
                print(f"✅ Downloaded: {output_file}")

                # Save metadata
                metadata = {
                    "scene": "S07",
                    "title": "Chegada da Polícia",
                    "version": "v2",
                    "method": "image-to-video (first-frame)",
                    "task_id": task.id,
                    "status": "GENERATED",
                    "prompt": PROMPT,
                    "first_frame": POLIZEI_IMAGE,
                    "output_file": output_file,
                    "output_url": output_url,
                    "timestamp": timestamp,
                    "duration_seconds": elapsed,
                    "validation_required": [
                        "BMW Polizei Bayern livery preserved (blue/silver/yellow)",
                        "POLIZEI text legible",
                        "Background transformed to forest (no residential)",
                        "Helena enters frame (navy coat, blonde, 45)",
                        "Blue lights flashing",
                        "Fog/mist atmosphere"
                    ],
                    "post_production_notes": [
                        "If POLIZEI text degraded, overlay in post (§296)",
                        "Add Helena voice-over DE if needed",
                        "Verify continuity with S08"
                    ]
                }

                import json
                meta_file = f"{OUTPUT_DIR}/S07_polizei_v2_{timestamp}.json"
                with open(meta_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                print(f"\n📄 Metadata saved: {meta_file}")
                print(f"\n🔍 VALIDATION CHECKLIST:")
                for item in metadata["validation_required"]:
                    print(f"   [ ] {item}")
            else:
                print("⚠️ No output URL in response")
                print(f"   Task status: {task_status}")

            break

        elif status == "FAILED":
            print(f"\n❌ Generation failed")
            if hasattr(task_status, 'failure'):
                print(f"   Failure: {task_status.failure}")
            break

        else:
            time.sleep(10)  # Poll every 10 seconds

    print(f"\n✅ S07 v2 generation complete. Awaiting Human Dragon validation (I9).")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
