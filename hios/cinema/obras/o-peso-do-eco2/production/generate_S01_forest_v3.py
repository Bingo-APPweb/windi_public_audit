#!/usr/bin/env python3
"""
S01 Generation v3 — O Registo da Vida (FLORESTA DENSA)
WINDI-HIOS Cinema · O Peso do Eco v2

Human Dragon feedback: "Nao vi a Floresta esse lado sombrio é que da o climax"
Focus: Dense forest setting that sets up the crime scene atmosphere

Sealed: §139 31 Mai 2026
Invariants: I9, I11, I14
"""
import os
import base64
import time
from datetime import datetime

os.environ["RUNWAYML_API_SECRET"] = os.getenv("RUNWAY_API_KEY", "key_3831dff2c3ffdbda5363f300b320422be856d0acd6f99459baa6ed9c869b125f2dc9a6d25a4e282bb453b7890946cfb685153faa4fb027d60fa50b29616d0d85")

from runwayml import RunwayML

# First-frame: Elisa v2 anchor
ELISA_ANCHOR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/thumbs/elisa_anchor_v2_1280x720.png"

OUTPUT_DIR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/production/renders"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("S01 v3 — O REGISTO DA VIDA (FLORESTA DENSA)")
print("WINDI-HIOS Cinema · O Peso do Eco v2")
print("=" * 60)

with open(ELISA_ANCHOR, "rb") as f:
    elisa_b64 = base64.b64encode(f.read()).decode()
elisa_uri = f"data:image/png;base64,{elisa_b64}"

print(f"\n🎬 First-frame: Elisa v2 anchor")
print(f"   Image size: {len(elisa_b64):,} bytes (base64)")

# PROMPT — DENSE FOREST, dramatic atmosphere
PROMPT = """Dense Bavarian forest. Tall dark spruce and fir trees surround the scene. Deep forest trail, shadows between tree trunks. Late afternoon golden light filtering through dense canopy.

Young blonde woman (from reference, Elisa, early 30s) records selfie vlog on smartphone. Warm genuine smile, talks to camera. Content creator energy.

Forest setting is key: thick conifer forest, narrow trail, trees close together. Moody atmosphere but warm light on her face. Autumn leaves on ground.

Background: dark sedan barely visible parked on forest trail behind her, obscured by tree trunks.

Cinematic forest atmosphere. German woodland. Dense trees, filtered light."""

print(f"\n📝 Prompt ({len(PROMPT)} chars):")
print(PROMPT)

client = RunwayML()

try:
    print("\n⏳ Submitting generation request...")

    task = client.image_to_video.create(
        model="gen3a_turbo",
        prompt_image=elisa_uri,
        prompt_text=PROMPT,
        ratio="1280:768",
        duration=5
    )

    print(f"\n✅ Task created: {task.id}")
    print("\n⏳ Waiting for generation...")
    start_time = time.time()

    while True:
        task_status = client.tasks.retrieve(task.id)
        status = task_status.status
        print(f"   Status: {status}")

        if status == "SUCCEEDED":
            elapsed = time.time() - start_time
            print(f"\n🎬 Task complete in {elapsed:.1f}s!")

            output_url = None
            if hasattr(task_status, 'output') and task_status.output:
                output_url = task_status.output[0] if isinstance(task_status.output, list) else task_status.output

            if output_url:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"{OUTPUT_DIR}/S01_forest_v3_{timestamp}.mp4"

                import urllib.request
                urllib.request.urlretrieve(output_url, output_file)
                print(f"✅ Downloaded: {output_file}")

                metadata = {
                    "scene": "S01",
                    "title": "O Registo da Vida",
                    "version": "v3-forest",
                    "task_id": task.id,
                    "prompt": PROMPT,
                    "output_file": output_file,
                    "timestamp": timestamp,
                    "validation_required": [
                        "DENSE FOREST (spruce/fir, trees close together)",
                        "Forest trail visible",
                        "Elisa warm smile, content creator energy",
                        "Golden light filtering through canopy",
                        "Moody atmosphere (setup for crime)",
                        "Sedan hint in background (proof chain)"
                    ]
                }

                import json
                meta_file = f"{OUTPUT_DIR}/S01_forest_v3_{timestamp}.json"
                with open(meta_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                print(f"\n📄 Metadata: {meta_file}")
                print(f"\n🔍 VALIDATION:")
                for item in metadata["validation_required"]:
                    print(f"   [ ] {item}")
            break

        elif status == "FAILED":
            print(f"\n❌ Generation failed")
            break
        else:
            time.sleep(10)

    print(f"\n✅ S01 v3 complete. Awaiting Human Dragon validation (I9).")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
